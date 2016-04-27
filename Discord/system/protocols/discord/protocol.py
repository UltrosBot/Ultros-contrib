# coding=utf-8
import base64
import re
from Queue import Queue

from numbers import Number
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.task import LoopingCall
from txrequests import Session

from system.commands.manager import CommandManager
from system.enums import CommandState
from system.events import discord as discord_events
from system.events import general as general_events
from system.events.manager import EventManager

from system.protocols.discord.base_protocol import DiscordProtocol
from system.protocols.discord.channel import Channel, PrivateChannel
from system.protocols.discord import opcodes
from system.protocols.discord.discriminators import DiscriminatorManager
from system.protocols.discord.guild import Guild
from system.protocols.discord.misc import Attachment, Embed, Role
from system.protocols.discord.permissions import BAN_MEMBERS, KICK_MEMBERS
from system.protocols.discord.user import User

# TODO: Logging
# TODO: Outgoing message/etc events

__author__ = 'Gareth Coles'

ACTION_REGEX = re.compile(r"^[\*_].*[\*_]$")
INTEGER_REGEX = re.compile(r"^[\d]+$")

INCOMING_MENTION_REGEX = re.compile(r"^<@[\d]+>$")
OUTGOING_MENTION_REGEX = re.compile(r"^@.*#[\d]{4}$")

ZWS = u"\u200B"  # Zero-width space


class Protocol(DiscordProtocol):
    ourselves = None
    user_settings = {}
    discriminator_manager = None

    guilds = {}
    users = []

    channels = {}
    voice_channels = {}
    private_channels = {}

    heartbeat_task = None
    heartbeat_interval = 0
    last_seq = 0

    message_queue = Queue()
    queue_emptying = False
    sending_message = False
    queue_task = None

    def __init__(self, name, factory, config):
        DiscordProtocol.__init__(self, name, factory, config)
        self.name = name

        self.setup()

    def setup(self):
        self.discriminator_manager = DiscriminatorManager(self)
        self.discriminator_manager.setup()

        self.event_manager = EventManager()
        self.command_manager = CommandManager()

    @property
    def all_channels(self):
        channels = self.channels.copy()
        channels.update(self.voice_channels)
        channels.update(self.private_channels)

        return channels

    # region Discord event handlers

    def discord_event_ready(self, message):
        """
        Fired on a READY message; we get this when we've just connected

        It contains all kinds of information - User info, permissions,
        roles,
        "guilds" (servers), and so on.
        """
        gateway_version = int(message["v"])

        if gateway_version != 4:
            self.log.error(
                "Incorrect gateway version ({}), "
                "please update your bot.".format(
                    gateway_version
                )
            )

            return self.shutdown()

        private_channels = message["private_channels"]
        ourselves = {"user": message["user"]}

        self.log.info("Connected. Gateway version: {}".format(gateway_version))

        self.ourselves = self.add_user(ourselves)

        servers = message["guilds"]

        for server in servers:
            if "unavailable" in server and server["unavailable"]:
                self.log.info("Found unavailable server: {}".format(
                    server["id"]
                ))
            else:
                self.log.info(
                    "Found server: {} -> {}".format(
                        server["id"], server[
                            "name"
                        ]
                    )
                )

        parsed_private_channels = []

        for channel in private_channels:
            user = {"user": channel["recipient"]}
            channel["recipient"] = self.add_user(user)

            parsed_private_channels.append(self.add_channel(channel))

        self.heartbeat_interval = message["heartbeat_interval"] / 1000.0
        self.start_heartbeat()

        event = discord_events.ReadyEvent(
            self, message["guilds"], self.heartbeat_interval,
            message["presences"], parsed_private_channels,
            message["session_id"], self.ourselves, gateway_version
        )

        self.event_manager.run_callback("Discord/Ready", event)

        if event.cancelled:
            self.log.info("Ready event cancelled, shutting down...")
            return self.shutdown()
        self.log.info("Ready event handled.")

    def discord_event_channel_create(self, message):
        channel = self.add_channel(message)
        guild = self.get_guild(channel.guild_id)

        if channel.id not in guild.channels:
            guild.channels.append(channel.id)

        self.log.info("Channel created: {}".format(channel.name))

        event = discord_events.ChannelCreateEvent(self, channel)
        self.event_manager.run_callback("Discord/ChannelCreated", event)

    def discord_event_channel_update(self, message):
        channel = self.add_channel(message)

        self.log.info("Channel updated: {}".format(channel.name))

        event = discord_events.ChannelUpdateEvent(self, channel)
        self.event_manager.run_callback("Discord/ChannelUpdated", event)

    def discord_event_channel_delete(self, message):
        channel = self.del_channel(message["id"])
        guild = self.get_guild(channel.guild_id)

        if channel.id in guild.channels:
            guild.channels.remove(channel.id)

        self.log.info("Channel deleted: {}".format(channel.name))

        event = discord_events.ChannelDeleteEvent(self, channel)
        self.event_manager.run_callback("Discord/ChannelDeleted", event)

    def discord_event_guild_ban_add(self, message):
        # {
        #  u'guild_id': u'124255619791323136',
        #  u'user':
        #   {
        #    u'username': u'Roadcrosser',
        #    u'discriminator': u'3657',
        #    u'id': u'116138050710536192',
        #    u'avatar': u'7593703d9fd5f0a7c86fe378490e52e2'
        #   }
        # }
        user = self.get_user(int(message["user"]["id"]))
        guild = self.get_guild(int(message["guild_id"]))

        self.log.info("User banned from {}: {}".format(
            guild.name, user.nickname
        ))

        event = discord_events.GuildBanAddEvent(self, user, guild)
        self.event_manager.run_callback("Discord/GuildBanAdded", event)

    def discord_event_guild_ban_remove(self, message):
        user = self.add_user(message)
        guild = self.get_guild(message["guild_id"])

        self.log.info("User unbanned from {}: {}".format(
            guild.name, user.nickname
        ))

        event = discord_events.GuildBanRemoveEvent(self, user, guild)
        self.event_manager.run_callback("Discord/GuildBanRemoved", event)

    def discord_event_guild_create(self, message):
        guild_id = message["id"]
        channels = message["channels"]
        members = message["members"]
        presences = message["presences"]

        guild = self.add_guild(message)

        for channel in channels:
            channel["guild_id"] = guild_id
            self.add_channel(channel)

        for user in members:
            self.add_user(user)

        for presence in presences:
            user = self.get_user(int(presence["user"]["id"]))

            user.status = presence["status"]

            if presence["game"]:
                user.game = presence["game"]["name"]

        event = discord_events.GuildCreateEvent(self, guild)
        self.event_manager.run_callback("Discord/GuildCreated", event)

        self.send_request_guild_members(guild.id)

    def discord_event_guild_update(self, message):
        guild = self.add_guild(message)

        event = discord_events.GuildUpdateEvent(self, guild)
        self.event_manager.run_callback("Discord/GuildUpdated", event)

    def discord_event_guild_emjoi_update(self, message):
        guild = self.get_guild(message["guild_id"])
        emojis = message["emojis"]  # Emoji object

        event = discord_events.GuildEmojiUpdateEvent(self, guild, emojis)
        self.event_manager.run_callback("Discord/GuildEmojisUpdated", event)

    def discord_event_guild_delete(self, message):
        guild = self.get_guild(message["id"])
        was_removed = not message.get("unavailable", False)

        event = discord_events.GuildDeleteEvent(self, guild, was_removed)
        self.event_manager.run_callback("Discord/GuildDeleted", event)

    def discord_event_guild_integrations_update(self, message):
        guild = self.get_guild(message["guild_id"])

        # IDK, it exists but it only gives the guild ID, so.. yeah
        event = discord_events.GuildIntegrationsUpdateEvent(self, guild)

        self.event_manager.run_callback(
            "Discord/GuildIntegrationsUpdated", event
        )

    def discord_event_guild_member_add(self, message):
        guild = self.get_guild(int(message["guild_id"]))
        user = self.add_user(message)

        roles = [Role.from_message(r) for r in message["roles"]]

        user.guilds.append(guild.id)
        user.roles[guild.id] = {r.id: r for r in roles}

        joined_at = message["joined_at"]

        event = discord_events.GuildMemberAddEvent(
            self, guild, user, roles, joined_at
        )

        self.event_manager.run_callback("Discord/GuildMemberAdded", event)

    def discord_event_guild_member_remove(self, message):
        guild = self.get_guild(int(message["guild_id"]))
        user = self.add_user(message)

        event = discord_events.GuildMemberRemoveEvent(self, guild, user)
        self.event_manager.run_callback("Discord/GuildMemberRemoved", event)

        if user.id in guild.members:
            guild.members.remove(user.id)

        if guild.id in user.guilds:
            user.guilds.remove(guild.id)

        if guild.id in user.roles:
            del user.roles[guild.id]

        if len(user.guilds) < 1:
            self.del_user(user.id)

    def discord_event_guild_member_update(self, message):
        guild = self.get_guild(message["guild_id"])
        user = self.add_user(message)

        roles = [Role.from_message(r) for r in message["roles"]]

        for role in roles:
            user.roles[guild.id][role.id] = role

        event = discord_events.GuildMemberUpdateEvent(self, guild, user, roles)
        self.event_manager.run_callback("Discord/GuildMemberUpdated", event)

    def discord_event_guild_role_create(self, message):
        guild = self.get_guild(message["guild_id"])
        role = Role.from_message(message["role"])

        event = discord_events.GuildRoleCreateEvent(self, guild, role)
        self.event_manager.run_callback("Discord/GuildRoleCreated", event)

    def discord_event_guild_role_update(self, message):
        guild = self.get_guild(message["guild_id"])
        role = Role.from_message(message["role"])

        event = discord_events.GuildRoleUpdateEvent(self, guild, role)
        self.event_manager.run_callback("Discord/GuildRoleUpdated", event)

    def discord_event_guild_role_delete(self, message):
        guild = self.get_guild(message["guild_id"])
        role = message["role_id"]

        event = discord_events.GuildRoleDeleteEvent(self, guild, role)
        self.event_manager.run_callback("Discord/GuildRoleDeleted", event)

    def discord_event_message_create(self, message):
        message_id = message["id"]
        channel_id = int(message["channel_id"])
        author = message["author"]  # User object
        content = message["content"]
        timestamp = message["timestamp"]
        edited_timestamp = message["timestamp"]  # Or null
        tts = message["tts"]  # Text-to-speech
        mention_everyone = message["mention_everyone"]
        mentions = message["mentions"]  # Array of users
        attachments = message["attachments"]  # Array of attachment objects
        embeds = message["embeds"]  # Array of embed objects
        nonce = message["nonce"]  # Or null

        user = self.get_user(int(author["id"]))

        if user.id == self.ourselves.id:
            return

        if self.config.get("mentions", {}).get("autoconvert", True):
            words = []

            for word in content.split(" "):
                if INCOMING_MENTION_REGEX.match(word):
                    word = word[2:-1]
                    _user = self.get_user(int(word))
                    word = u"@{}".format(_user.nickname)
                words.append(word)

            content = " ".join(words)

        channel = self.get_channel(channel_id)

        if channel.is_private():
            channel = user

        discord_event = discord_events.MessageCreateEvent(
            self, message_id, channel, user, content, timestamp,
            edited_timestamp, tts, mention_everyone,
            [self.get_user(u["id"]) for u in mentions],
            [Attachment.from_message(m) for m in attachments],
            [Embed.from_message(m) for m in embeds],
            nonce
        )

        self.event_manager.run_callback(
            "Discord/MessageCreated", discord_event
        )

        if discord_event.cancelled:
            return

        if ACTION_REGEX.match(content):
            # It's an action
            event = general_events.ActionReceived(
                self, user, channel, content[1:-1]
            )

            self.event_manager.run_callback("ActionReceived", event)

            if event.printable:
                self.log.info(
                    u"* {}:{} {}".format(
                        user.nickname, channel.name, event.message
                    )
                )

            return

        pre_event = general_events.PreMessageReceived(
            self, user, channel, content, "message"
        )

        self.event_manager.run_callback("PreMessageReceived", pre_event)

        if pre_event.printable:
            self.log.info(u"<{}:{}> {}".format(
                user.nickname, channel.name, pre_event.message
            ))

        if pre_event.cancelled:
            return

        result = self.command_manager.process_input(
            pre_event.message, user, channel, self, self.control_chars,
            self.ourselves.real_nickname
        )

        if result[0] is CommandState.RateLimited:
            self.log.debug("Command rate-limited")
            user.respond("That command has been rate-limited, please "
                         "try again later.")
            return
        elif result[0] is CommandState.NotACommand:
            self.log.debug("Not a command")
        elif result[0] is CommandState.UnknownOverridden:
            self.log.debug("Unknown command overridden")
            return  # It was a command
        elif result[0] is CommandState.Unknown:
            self.log.debug("Unknown command")
        elif result[0] is CommandState.Success:
            self.log.debug("Command ran successfully")
            return  # It was a command
        elif result[0] is CommandState.NoPermission:
            self.log.debug("No permission to run command")
            return  # It was a command
        elif result[0] is CommandState.Error:
            user.respond("Error running command: %s" % result[1])
            return  # It was a command
        else:
            self.log.debug("Unknown command state: %s" % result[0])

        event = general_events.MessageReceived(
            self, user, channel, pre_event.message, "message"
        )

        self.event_manager.run_callback(
            "MessageReceived", event
        )

    def discord_event_message_update(self, message):
        # Payload: Partial message
        message_id = message["id"]
        channel = self.get_channel(message["channel_id"])

        del message["id"]
        del message["channel_id"]

        if "author" in message:
            message["author"] = self.get_user(message["author"]["id"])

        if "mentions" in message:
            message["mentions"] = [
                self.get_user(u["id"]) for u in message["mentions"]
            ]

        if "attachments" in message:
            message["attachments"] = [
                Attachment.from_message(m) for m in message["attachments"]
            ]

        if "embeds" in message:
            message["embeds"] = [
                Embed.from_message(m) for m in message["embeds"]
            ]

        event = discord_events.MessageUpdateEvent(
            self, message_id, channel, **message
        )

        self.event_manager.run_callback("Discord/MessageUpdated", event)

    def discord_event_message_delete(self, message):
        message_id = message["id"]
        channel = self.get_channel(message["channel_id"])

        event = discord_events.MessageDeleteEvent(
            self, message_id, channel
        )

        self.event_manager.run_callback("Discord/MessageDeleted", event)

    def discord_event_presence_update(self, message):
        # https://github.com/hammerandchisel/discord-api-docs/issues/34
        # {
        #  u'status': u'offline',
        #  u'game': None,
        #  u'guild_id': u'124255619791323136',
        #  u'user': {
        #   u'id': u'116138050710536192'
        #  },
        #  u'roles': []
        # }
        user = self.get_user(message["user"]["id"])

        if user is None:
            self.log.debug("No such user: {}".format(message["user"]["id"]))
            return  # Can happen when a user is removed from a guild

        guild = self.get_guild(message["guild_id"])

        roles = [Role.from_message(r) for r in message["roles"]]
        game = message["game"]  # Or null

        if game:
            game = game["name"]

        status = message["status"]  # "idle", "online", "offline"

        user.game = game
        user.status = status

        for role in roles:
            user.roles[guild.id][role.id] = role

        event = discord_events.PresenceUpdateEvent(
            self, user, guild, roles, game, status
        )

        self.event_manager.run_callback("Discord/PresenceUpdate", event)

    def discord_event_typing_start(self, message):
        user = self.get_user(["user_id"])
        channel = self.get_channel(message["channel_id"])
        timestamp = message["timestamp"]

        event = discord_events.TypingStartEvent(
            self, user, channel, timestamp
        )

        self.event_manager.run_callback("Discord/TypingStarted", event)

    def discord_event_user_settings_update(self, message):
        # Payload: User settings; not documented
        event = discord_events.UserSettingsUpdateEvent(self, message)

        self.event_manager.run_callback("Discord/UserSettingsUpdated", event)

    def discord_event_user_update(self, message):
        user = self.add_user(message)

        event = discord_events.UserUpdateEvent(self, user)
        self.event_manager.run_callback("Discord/UserUpdated", event)

    def discord_event_voice_state_update(self, message):
        user = self.get_user(message["user_id"])
        guild = self.get_guild(message["guild_id"])
        channel = self.get_channel(message["channel_id"], "voice")
        session_id = message["session_id"]
        self_mute = message["self_mute"]
        self_deaf = message["self_deaf"]
        server_mute = message["mute"]
        server_deaf = message["deaf"]

        user.mute = self_mute or server_mute
        user.deaf = self_deaf or server_deaf

        event = discord_events.VoiceStateUpdateEvent(
            self, user, guild, channel, session_id, self_mute, self_deaf,
            server_mute, server_deaf
        )

        self.event_manager.run_callback("Discord/VoiceStateUpdated", event)

    def discord_event_guild_member_chunk(self, message):
        guild = self.get_guild(message["guild_id"])
        done_members = []

        for member in message["members"]:
            user = self.add_user(member)

            guild.members.append(user.id)
            user.guilds.append(guild.id)
            user.roles[guild.id] = [
                Role.from_message(r) for r in member["roles"]
            ]

            done_members.append(user)

        event = discord_events.GuildMemberChunk(
            self, guild, done_members
        )

        self.event_manager.run_callback("Discord/GuildMemberChunk", event)

    # endregion

    # region Discord message handlers

    def discord_unknown(self, message):
        """
        Called when we have a message type that isn't handled
        """

        self.log.debug(
            "Unknown message ({}): {}".format(
                opcodes.get_name(message["op"]), message
            )
        )

    def discord_dispatch(self, message):
        data = message["d"]
        sequence = message["s"]
        message_type = message["t"]

        self.last_seq = sequence

        self.log.trace("Received event: [{}] {}".format(message_type, data))

        function_name = "discord_event_{}".format(message_type.lower())

        if hasattr(self, function_name):
            getattr(self, function_name)(data)

    def discord_heartbeat(self, message):
        # Not sure if the client ever gets this
        data = self.last_seq

        self.log.info("Heartbeat received: {}".format(data))

    def discord_identify(self, message):
        # Not sure if the client ever gets this
        token = message["token"]
        # properties = message["properties"]
        # compress = message["compress"]
        # large_threshold = message["large_threshold"]

        self.log.info("Received identify message for token: {}".format(token))

    def discord_status_update(self, message):
        # Not sure if the client ever gets this
        idle_since = message["idle_since"]  # Or null
        game = message["game"]  # Or null

        self.log.info("Received idle state: {} / {}".format(game, idle_since))

    def discord_voice_state_update(self, message):
        # Not sure if the client ever gets this
        guild_id = message["guild_id"]
        channel_id = message["channel_id"]  # Or null
        # self_mute = message["self_mute"]
        # self_deaf = message["self_deaf"]

        self.log.info("Received voice state: {} / {}".format(
            guild_id, channel_id
        ))

    def discord_voice_server_ping(self, message):
        # Not documented
        pass

    def discord_resume(self, message):
        # Not sure if the client ever gets this
        token = message["token"]
        # session_id = message["session_id"]
        # seq = message["seq"]

        self.log.info("Received resume message: {}".format(token))

    def discord_reconnect(self, message):
        # Not documented
        pass

    def discord_request_guild_members(self, message):
        # Not sure if the client ever gets this
        guild_id = message["guild_id"]
        # query = message["query"]
        # limit = message["limit"]

        self.log.info("Received guild members request: {}".format(guild_id))

    def discord_invalid_session(self, message):
        # Not documented
        pass

    # endregion

    # region Internal methods

    @inlineCallbacks
    def get_private_channel(self, user):
        c = self.get_channel(user.nickname, "private")

        if c is None:
            try:
                self.log.debug(
                    "No private channel for '{}' - let's create one".format(
                        user.name
                    )
                )
                result = yield self.web_create_dm(user.id)
                result["recipient"] = self.get_user(
                    int(result["recipient"]["id"])
                )
                self.log.debug("Result: {}".format(result))

                c = self.add_channel(result)
                self.log.debug("Channel ({}): {}".format(type(c), c))
            except Exception:
                self.log.exception("Failed to create channel for {}".format(
                    user.name
                ))
                raise

        returnValue(c)

    def add_user(self, member):
        u = self.get_user(int(member["user"]["id"]))
        user = User.from_message(member, self, False)

        if u:
            u.update(user)
            return u

        user.is_tracked = True
        self.users.append(user)

        return user

    def del_user(self, user):
        u = self.get_user(user)

        if u:
            self.users.remove(u)

    def add_channel(self, data):
        if data.get("is_private", False):
            channel = PrivateChannel.from_message(data, self)
        else:
            channel = Channel.from_message(data, self)

        if channel.is_private():
            if channel.id not in self.private_channels:
                self.private_channels[channel.id] = channel
            else:
                other_channel = self.get_channel(channel.id, "private")
                other_channel.update(channel)

                return other_channel
        elif channel.is_text():
            if channel.id not in self.channels:
                self.channels[channel.id] = channel
            else:
                other_channel = self.get_channel(channel.id, "text")
                other_channel.update(channel)

                return other_channel
        elif channel.is_voice():
            if channel.id not in self.voice_channels:
                self.voice_channels[channel.id] = channel
            else:
                other_channel = self.get_channel(channel.id, "voice")
                other_channel.update(channel)

                return other_channel
        else:
            raise TypeError("Unknown channel type: {}".format(channel.type))

        return channel

    def del_channel(self, channel):
        c = self.get_channel(channel)

        if c:
            if c.is_private:
                del self.private_channels[channel.id]
            elif c.is_voice:
                del self.voice_channels[channel.id]
            else:
                del self.channels[channel.id]

        return c

    def add_guild(self, data):
        guild_id = int(data["id"])

        name = data["name"]
        icon = data["icon"]
        splash = data["splash"]
        owner_id = data["owner_id"]
        region = data["region"]
        afk_channel_id = data["afk_channel_id"]
        afk_timeout = data["afk_timeout"]
        verification_level = data["verification_level"]
        roles = data["roles"]  # Array of role objects
        emojis = data["emojis"]  # Array of emoji objects
        features = data["features"]  # ???

        channels = data["channels"]
        members = data["members"]

        guild = Guild(
            name, self, guild_id, icon, splash, owner_id, region,
            afk_channel_id, afk_timeout, verification_level, roles, emojis,
            features,
            channels=[int(channel["id"]) for channel in channels],
            members=[int(user["user"]["id"]) for user in members]
        )

        if guild_id not in self.guilds:
            self.guilds[guild_id] = guild
        else:
            other_guild = self.get_guild(guild_id)
            other_guild.update(guild)

            return other_guild

        return guild

    def del_guild(self, guild):
        if guild in self.guilds:
            del self.guilds[guild]

    def get_guild(self, guild):
        guild = int(guild)
        if guild in self.guilds:
            return self.guilds[guild]
        return None

    def start_heartbeat(self):
        if self.heartbeat_interval:
            self.stop_heartbeat()

            self.heartbeat_task = LoopingCall(
                self.send_heartbeat, self.last_seq
            )

            self.heartbeat_task.start(self.heartbeat_interval)

    def stop_heartbeat(self):
        if self.heartbeat_task:
            if not self.heartbeat_task.running:
                self.heartbeat_task.stop()

    # endregion

    # region Utils

    def set_avatar_from_file(self, path):
        with open(path, "rb") as fh:
            image_data = fh.read()

        encoded = base64.b64encode(image_data)
        avatar = "data:image/jpeg;base64,{}".format(encoded)

        return self.web_modify_current_user(
            avatar=avatar, username=self.ourselves.nickname
        )

    @inlineCallbacks
    def clone_user_avatar(self, user):
        session = Session()
        avatar_url = "https://cdn.discordapp.com/avatars/{}/{}.jpg"

        image_data = yield session.get(avatar_url.format(user.id, user.avatar))
        image_data = image_data.content

        encoded = base64.b64encode(image_data)
        avatar = "data:image/jpeg;base64,{}".format(encoded)

        result = yield self.web_modify_current_user(
            avatar=avatar, username=self.ourselves.nickname
        )

        returnValue(result)
        return

    # endregion

    # region Ultros methods

    def channel_ban(self, user, channel=None, reason=None, force=False):
        pass

    def channel_kick(self, user, channel=None, reason=None, force=False):
        pass

    def get_extra_groups(self, user, target=None):
        return Protocol.get_extra_groups(self, user, target)

    def get_channel(self, channel, _type=None):
        """
        :rtype channel: system.protocols.discord.channel.Channel
        """
        if _type is None:
            channel_set = self.all_channels
        elif _type == "text":
            channel_set = self.channels
        elif _type == "voice":
            channel_set = self.voice_channels
        elif _type == "private":
            channel_set = self.private_channels
        else:
            channel_set = self.all_channels

        if isinstance(channel, basestring):
            for c in channel_set.values():
                if c.name == channel:
                    return c

                if INTEGER_REGEX.match(channel):
                    return self.get_channel(int(channel), _type)
        elif isinstance(channel, Number):
            for c in channel_set.values():
                if c.id == channel:
                    return c

        return None

    def get_user(self, user):
        if isinstance(user, basestring):
            for u in self.users:
                if u.nickname == user:
                    return u
            if INTEGER_REGEX.match(user):
                return self.get_user(int(user))
        elif isinstance(user, Number):
            for u in self.users:
                if u.id == user:
                    return u
        return None

    def global_ban(self, user, reason=None, force=False, guild=None):
        if guild is None:
            for guild in user.guilds:
                self.global_ban(user, reason, force, guild)
            return

        if isinstance(guild, Guild):
            guild = guild.id

        roles = self.ourselves.roles[guild.id]

        for role in roles.values():
            if force or KICK_MEMBERS in role.permissions:
                return self.web_create_guild_ban(guild, user.id)

    def global_kick(self, user, reason=None, force=False, guild=None):
        if guild is None:
            for guild in user.guilds:
                self.global_kick(user, reason, force, guild)
            return

        if isinstance(guild, Guild):
            guild = guild.id

        roles = self.ourselves.roles[guild.id]

        for role in roles.values():
            if force or BAN_MEMBERS in role.permissions:
                self.web_remove_guild_member(guild, user.id)

    def join_channel(self, channel, password=None):
        pass

    def leave_channel(self, channel, reason=None):
        pass

    def num_channels(self):
        return len(self.all_channels)

    def send_action(self, target, message, target_type=None, use_event=True):
        return self.send_msg(
            target, "_{}_".format(message),
            target_type=target_type, use_event=use_event
        )

    @inlineCallbacks
    def send_msg(self, target, message, target_type=None, use_event=True):
        if isinstance(target, basestring):
            if target_type == "channel":
                target = self.get_channel(target)
            elif target_type == "user":
                target = self.get_user(target)

        if self.config.get("mentions", {}).get("autoconvert", True):
            words = []

            for word in message.split(" "):
                if OUTGOING_MENTION_REGEX.match(word):
                    word = word[1:]
                    user = self.get_user(word)
                    word = "<@{}>".format(user.id)

                words.append(word)

            message = " ".join(words)

        if self.config.get("mentions", {}).get("prevent_everyone", True):
            message = message.replace("@everyone", u"@{}everyone".format(ZWS))
            message = message.replace("@here", u"@{}here".format(ZWS))

        if isinstance(target, Channel):
            self.add_to_queue(target.id, message)
        elif isinstance(target, User):
            c = yield self.get_private_channel(target)
            self.add_to_queue(c.id, message)

    def add_to_queue(self, target, message):
        self.message_queue.put_nowait((target, message))

        if not self.queue_emptying:
            self.start_emptying_queue()

    def start_emptying_queue(self):
        self.queue_emptying = True

        self.queue_task = LoopingCall(
            self.send_from_queue
        )

        self.queue_task.start(0.1)

    def stop_emptying_queue(self):
        if self.queue_task:
            self.queue_task.stop()

        self.queue_emptying = False

    @inlineCallbacks
    def send_from_queue(self):
        if self.sending_message:
            return

        if self.message_queue.empty():
            self.stop_emptying_queue()
            return

        self.sending_message = True
        message = self.message_queue.get_nowait()

        try:
            _ = yield self.web_create_message(*message)
        finally:
            self.sending_message = False

    def shutdown(self):
        self.stop_emptying_queue()
        self.stop_heartbeat()
        self.sendClose()
        self.transport.loseConnection()

    # endregion

    pass
