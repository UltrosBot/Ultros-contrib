# coding=utf-8
import base64
import re

from collections import deque
from numbers import Number

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.task import LoopingCall
from txrequests import Session

from system.commands.manager import CommandManager
from system.enums import CommandState
from system.events import discord as discord_events
from system.events import general as general_events
from system.events.manager import EventManager
from system.factory_manager import FactoryManager

from system.protocols.discord.base_protocol import DiscordProtocol
from system.protocols.discord.channel import PrivateChannel
from system.protocols.discord import opcodes
from system.protocols.discord.discriminators import DiscriminatorManager
from system.protocols.discord.guild import Guild
from system.protocols.discord.misc import Attachment, Embed, Role, \
    PermissionOverwrite
from system.protocols.discord.permissions import BAN_MEMBERS, KICK_MEMBERS, \
    get_permissions
from system.protocols.discord.user import User

from system.storage.manager import StorageManager
from system.storage.formats import MEMORY

# TODO: Dispatch work
# TODO: Document

__author__ = 'Gareth Coles'

ACTION_REGEX = re.compile(ur"^[\*_].*[\*_]$")
INTEGER_REGEX = re.compile(ur"^[\d]+$")

INCOMING_MENTION_REGEX = re.compile(ur"^<@[\d]+>$")
OUTGOING_MENTION_REGEX = re.compile(ur"^@.*#[\d]{4}$")

MESSAGE_SEPARATOR = "\n"
ZWS = u"\u200B"  # Zero-width space


class Protocol(DiscordProtocol):
    command_manager = None
    discriminator_manager = None
    event_manager = None
    factory_manager = None
    storage_manager = None

    ourselves = None
    user_settings = {}

    guilds = {}
    users = {}
    channels = {}
    sub_protocols = {}
    roles = {}

    heartbeat_task = None
    heartbeat_interval = 0
    last_seq = 0

    message_queue = deque()
    queue_emptying = False
    sending_message = False
    queue_task = None

    def __init__(self, name, factory, config):
        DiscordProtocol.__init__(self, name, factory, config)
        self.name = name

        self.setup()

    def setup(self):
        self.command_manager = CommandManager()
        self.discriminator_manager = DiscriminatorManager(self)
        self.event_manager = EventManager()
        self.factory_manager = FactoryManager()
        self.storage_manager = StorageManager()

        self.discriminator_manager.setup()

    # region Discord event handlers

    def discord_event_ready(self, message):
        """
        Fired on a READY message; we get this when we've just connected

        It contains all kinds of information - User info, permissions,
        roles,
        "guilds" (servers), and so on.
        """

        # TODO: Check over

        gateway_version = int(message["v"])

        if gateway_version != 4:
            self.log.error(
                "Incorrect gateway version ({}), "
                "please update your bot.".format(
                    gateway_version
                )
            )

            self.factory.shutting_down = True
            return self.shutdown()

        private_channels = message["private_channels"]

        self.log.info("Connected. Gateway version: {}".format(gateway_version))

        self.ourselves = self.add_user(message["user"])

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
            self.add_user(channel["recipient"])

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

            self.factory.shutting_down = True
            return self.shutdown()

        self.log.info("Received ready event")

        self.send_presence_update(None, "Ultros", "https://ultros.io")

    def discord_event_channel_create(self, message):
        if "guild_id" not in message:
            channel = self.add_channel(message)

            self.log.info(u"Channel created: {}".format(channel.name))

            event = discord_events.ChannelCreateEvent(self, channel)
            self.event_manager.run_callback("Discord/ChannelCreated", event)
        else:
            guild = self.get_guild(int(message["guild_id"]))
            del message["guild_id"]

            permission_overwrites = []
            for overwrite in message["permission_overwrites"]:
                permission_overwrites.append(
                    PermissionOverwrite(
                        overwrite["id"],
                        overwrite["type"],
                        overwrite["allow"],
                        overwrite["deny"]
                    )
                )

            # We're doing this instead of just passing it as later
            # message passing will likely use setattr()
            message["permission_overwrites"] = permission_overwrites
            del permission_overwrites

            sub_protocol = self.get_protocol(guild.id)

            if message["type"] == "voice":  # Voice channel
                sub_protocol.dispatch_voice_channel_created(
                    int(message["id"]), message["name"],
                    message["position"], message["permission_overwrites"],
                    message["bitrate"]
                )
            else:  # Text channel
                sub_protocol.dispatch_text_channel_created(
                    int(message["id"]), message["name"],
                    message["position"], message["permission_overwrites"],
                    message["topic"], message["last_message_id"]
                )

    def discord_event_channel_update(self, message):
        # This only happens with Guild channels; not private
        guild = self.get_guild(int(message["guild_id"]))
        channel_id = int(message["id"])

        del message["guild_id"]
        del message["id"]

        if "permission_overwrites" in message:
            permission_overwrites = []

            for overwrite in message["permission_overwrites"]:
                permission_overwrites.append(
                    PermissionOverwrite(
                        overwrite["id"],
                        overwrite["type"],
                        overwrite["allow"],
                        overwrite["deny"]
                    )
                )

            # We're doing this instead of just passing it as later
            # message passing will likely use setattr()

            message["permission_overwrites"] = permission_overwrites
            del permission_overwrites

        sub_protocol = self.get_protocol(guild.id)

        if message["type"] == "voice":  # Voice channel
            sub_protocol.dispatch_voice_channel_updated(
                channel_id, message
            )
        else:  # Text channel
            sub_protocol.dispatch_text_channel_updated(
                channel_id, message
            )

    def discord_event_channel_delete(self, message):
        channel_id = int(message["id"])

        if "guild_id" not in message:
            channel = self.del_channel(channel_id)

            self.log.info(u"Channel deleted: {}".format(channel.name))

            event = discord_events.ChannelRemoveEvent(self, channel)
            self.event_manager.run_callback("Discord/ChannelRemoved", event)
        else:
            guild = self.get_guild(int(message["guild_id"]))
            sub_protocol = self.get_protocol(guild.id)

            if message["type"] == "voice":  # Voice channel
                sub_protocol.dispatch_voice_channel_removed(channel_id)
            else:  # Text channel
                sub_protocol.dispatch_text_channel_removed(channel_id)

    def discord_event_guild_ban_add(self, message):
        guild = self.get_guild(int(message["guild_id"]))
        sub_protocol = self.get_protocol(guild.id)
        sub_protocol.dispatch_ban_added(int(message["user"]["id"]))

    def discord_event_guild_ban_remove(self, message):
        guild = self.get_guild(int(message["guild_id"]))
        sub_protocol = self.get_protocol(guild.id)
        sub_protocol.dispatch_ban_removed(int(message["user"]["id"]))

    def discord_event_guild_create(self, message):
        guild = self.add_guild(message)

        self.log.info(u"Got guild: {}".format(guild.name))

        event = discord_events.GuildCreateEvent(self, guild)
        self.event_manager.run_callback("Discord/GuildCreated", event)

        self.send_request_guild_members(guild.id)

    def discord_event_guild_update(self, message):
        guild = self.get_guild(message["id"])

        if "roles" in message:
            roles = []

            for role in message["roles"]:
                existing_role = self.get_role(int(role["id"]))

                if existing_role is not None:
                    role["permissions"] = get_permissions(role["permissions"])

                    for k, v in role.iteritems():
                        if v is not None:
                            setattr(existing_role, k, v)

                    roles.append(existing_role)

                else:
                    roles.append(self.add_role(role))

            message["roles"] = roles
            del roles

        for k, v in message.iteritems():
            if v is not None:
                setattr(guild, k, v)

        self.get_protocol(guild.id).dispatch_guild_updated(message)

        self.log.info(u"Guild updated: {}".format(guild.name))

        event = discord_events.GuildUpdateEvent(self, guild)
        self.event_manager.run_callback("Discord/GuildUpdated", event)

    def discord_event_guild_emoji_update(self, message):
        guild = self.get_guild(message["guild_id"])

        self.get_protocol(guild.id).dispatch_emoji_updated(message["emojis"])

    def discord_event_guild_delete(self, message):
        guild = self.get_guild(message["id"])
        was_removed = not message.get("unavailable", False)

        if was_removed:
            self.log.info(u"Removed from guild: {}".format(guild.name))
        else:
            self.log.info(u"Lost guild: {}".format(guild.name))

        event = discord_events.GuildDeleteEvent(self, guild, was_removed)
        self.event_manager.run_callback("Discord/GuildDeleted", event)

        self.del_guild(guild.id)

    def discord_event_guild_integrations_update(self, message):
        proto = self.get_protocol(int(message["guild_id"]))
        proto.dispatch_integrations_updated()

    def discord_event_guild_member_add(self, message):
        user = self.add_user(message["user"])
        roles = [self.get_role(r) for r in message["roles"]]

        proto = self.get_protocol(int(message["guild_id"]))
        proto.dispatch_member_added(
            user, message.get("nick", None), roles, message["joined_at"],
            message["deaf"], message["mute"]
        )

    def discord_event_guild_member_remove(self, message):
        proto = self.get_protocol(int(message["guild_id"]))
        proto.dispatch_member_removed(int(message["user"]["id"]))

    def discord_event_guild_member_update(self, message):
        message["user"] = self.add_user(message["user"])
        message["roles"] = [self.get_role(r) for r in message["roles"]]

        proto = self.get_protocol(int(message["guild_id"]))

        proto.dispatch_member_updated(**message)

    def discord_event_guild_role_create(self, message):
        proto = self.get_protocol(int(message["guild_id"]))
        role = self.add_role(message["role"])

        proto.dispatch_role_created(role)

    def discord_event_guild_role_update(self, message):
        proto = self.get_protocol(int(message["guild_id"]))
        role = self.add_role(message["role"])

        proto.dispatch_role_updated(role)

    def discord_event_guild_role_delete(self, message):
        proto = self.get_protocol(int(message["guild_id"]))
        proto.dispatch_role_removed(int(message["role_id"]))

        self.del_role(int(message["role_id"]))

    def discord_event_message_create(self, message):
        # TODO
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
        # TODO (No guild ID)
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

        self.log.info(u"Message in channel \"{}\" updated: {}".format(
            channel.name, message_id
        ))

        event = discord_events.MessageUpdateEvent(
            self, message_id, channel, **message
        )

        self.event_manager.run_callback("Discord/MessageUpdated", event)

    def discord_event_message_delete(self, message):
        # TODO (No guild ID)
        message_id = message["id"]
        channel = self.get_channel(message["channel_id"])

        self.log.info(u"Message in channel \"{}\" deleted: {}".format(
            channel.name, message_id
        ))

        event = discord_events.MessageDeleteEvent(
            self, message_id, channel
        )

        self.event_manager.run_callback("Discord/MessageDeleted", event)

    def discord_event_presence_update(self, message):
        # {
        #  u'status': u'offline',
        #  u'game': {"url?", "type?", "name"},
        #  u'guild_id': u'124255619791323136',
        #  u'user': {
        #   u'id': u'116138050710536192'
        #  },
        #  u'roles': []
        # }

        proto = self.get_protocol(int(message["guild_id"]))
        roles = [self.get_role(r) for r in message["roles"]]

        game_name = None
        game_url = None
        game_type = None

        if message.get("game", None) is not None:
            game = message["game"]

            game_name = game.get("name", None)
            game_url = game.get("url", None)
            game_type = game.get("type", None)

        proto.dispatch_presence_updated(
            int(message["user"]["id"]), message["status"], roles, game_name,
            game_url, game_type
        )

    def discord_event_typing_start(self, message):
        # TODO (No guild ID)
        user = self.get_user(["user_id"])
        channel = self.get_channel(message["channel_id"])
        timestamp = message["timestamp"]

        event = discord_events.TypingStartEvent(
            self, user, channel, timestamp
        )

        self.log.debug(
            u"User \"{}\" started typing".format(user.nickname)
        )

        self.event_manager.run_callback("Discord/TypingStarted", event)

    def discord_event_user_settings_update(self, message):
        # Payload: User settings; not documented
        self.log.info(u"Synchronised user settings were updated")
        event = discord_events.UserSettingsUpdateEvent(self, message)

        self.event_manager.run_callback("Discord/UserSettingsUpdated", event)

    def discord_event_user_update(self, message):
        user = self.add_user(message)

        self.log.info(
            u"User \"{}\" updated their profile".format(user.nickname)
        )

        event = discord_events.UserUpdateEvent(self, user)
        self.event_manager.run_callback("Discord/UserUpdated", event)

    def discord_event_voice_state_update(self, message):
        proto = self.get_protocol(int(message["guild_id"]))

        session_id = message["session_id"]
        self_mute = message["self_mute"]
        self_deaf = message["self_deaf"]
        server_mute = message["mute"]
        server_deaf = message["deaf"]

        proto.dispatch_voice_state_updated(
            int(message["user_id"]), session_id, self_mute, self_deaf,
            server_mute, server_deaf
        )

    def discord_event_guild_member_chunk(self, message):
        proto = self.get_protocol(int(message["guild_id"]))

        for member in message["members"]:
            member["user"] = self.add_user(member["user"])

        proto.dispatch_member_chunk(message["members"])

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

    def discord_heartbeat(self, message):
        self.send_heartbeat(message["d"])

    def discord_dispatch(self, message):
        data = message["d"]
        sequence = message["s"]
        message_type = message["t"]

        self.last_seq = sequence

        self.log.trace(u"Received event: [{}] {}".format(message_type, data))

        function_name = "discord_event_{}".format(message_type.lower())

        if hasattr(self, function_name):
            getattr(self, function_name)(data)

    def discord_voice_server_ping(self, message):
        # Not documented
        pass

    def discord_reconnect(self, message):
        # Not documented
        self.shutdown()  # Force a reconnect
        pass

    def discord_invalid_session(self, message):
        self.log.error("Error: Invalid session. Check your token.")
        self.factory.shutting_down = True
        self.shutdown()

    # endregion

    # region Internal methods

    @inlineCallbacks
    def get_private_channel(self, user):
        c = self.get_channel(user.nickname, "private")

        if c is None:
            try:
                self.log.debug(
                    u"No private channel for '{}' - let's create one".format(
                        user.name
                    )
                )
                result = yield self.web_create_dm(user.id)
                result["recipient"] = self.get_user(
                    int(result["recipient"]["id"])
                )
                self.log.debug(u"Result: {}".format(result))

                c = self.add_channel(result)
                self.log.debug(u"Channel ({}): {}".format(type(c), c))
            except Exception:
                self.log.exception(u"Failed to create channel for {}".format(
                    user.name
                ))
                raise

        returnValue(c)

    def add_user(self, user_obj):
        _id = int(user_obj["id"])

        existing_user = self.get_user(_id)

        if existing_user:
            for key, value in user_obj.iteritems():
                if value is not None:
                    setattr(existing_user, key, value)

            return existing_user

        username = user_obj["username"]
        discriminator = user_obj["discriminator"]
        avatar = user_obj["avatar"]
        verified = user_obj.get("verified", None)
        email = user_obj.get("email", None)

        user = User(
            username, self, _id, discriminator, avatar, verified, email, False
        )

        user.is_tracked = True
        self.users[_id] = user

        return user

    def del_user(self, user):
        u = self.get_user(user)

        if u is not None:
            del self.users[u.id]

        return u

    def add_role(self, role_obj):
        _id = role_obj["id"]

        existing_role = self.get_role(_id)

        if existing_role is not None:
            for k, v in role_obj.iteritems():
                if v is not None:
                    setattr(existing_role, k, v)
            return existing_role

        name = role_obj["name"]
        color = role_obj["color"]
        hoist = role_obj["hoist"]
        position = role_obj["position"]
        permissions = role_obj["permissions"]
        managed = role_obj["managed"]

        role = Role(_id, name, color, hoist, position, permissions, managed)

        self.roles[_id] = role
        return role

    def get_role(self, role):
        role_obj = None

        if isinstance(role, basestring):
            if INTEGER_REGEX.match(role):
                role_obj = self.roles.get(int(role), None)
            else:
                for r in self.roles.itervalues():
                    if r.name.lower() == role.lower():
                        role_obj = r
                        break
        else:
            role_obj = self.roles.get(role, None)
        return role_obj

    def del_role(self, role):
        r = self.get_role(role)

        if r is not None:
            del self.roles[r.id]

        return r

    def add_channel(self, channel_obj):
        _id = int(channel_obj["id"])

        existing_channel = self.get_channel(_id)

        if existing_channel is not None:
            for key, value in channel_obj.iteritems():
                if value is not None:
                    setattr(existing_channel, key, value)

            return existing_channel

        is_private = channel_obj["is_private"]
        recipient = self.get_user(int(channel_obj["recipient"]["id"]))
        last_message_id = channel_obj["last_message_id"]

        channel = PrivateChannel(
            recipient, self, last_message_id, _id, is_private
        )

        self.channels[channel.id] = channel

        return channel

    def del_channel(self, channel):
        c = self.get_channel(channel)

        if c:
            del self.channels[channel.id]

        return c

    def add_protocol(self, guild, channels, members, presences):
        existing_protocol = self.get_protocol(guild.id)

        if existing_protocol is not None:
            return existing_protocol

        protocol_names = self.config.get("protocol_names", {})

        if guild.id in protocol_names:
            name = "{}/{}".format(self.name, protocol_names[guild.id])
        elif guild.name in protocol_names:
            name = "{}/{}".format(self.name, protocol_names[guild.name])
        else:
            name = "{}/{}#{}".format(
                self.name, guild.name,
                self.discriminator_manager.get_guild_discriminator(
                    guild.id)
            )

        config = self.storage_manager.get_file(
            self, "config", MEMORY, ":memory:{}:".format(name),
            {
                "main": {
                    "protocol-type": "discord_dispatch",
                    "can-flood": self.config["main"]["can-flood"]
                },
                "guild": guild.id,
                "channels": channels,
                "members": members,
                "presences": presences,
                "parent-protocol": self.name
            }
        )

        config.editable = False

        self.factory_manager.load_protocol(name, config)
        self.sub_protocols[guild.id] = name

    def get_protocol(self, guild_id):
        """
        :rtype: system.protocols.discord_dispatch.protocol.Protocol
        """

        if guild_id in self.sub_protocols:
            proto_name = self.sub_protocols[guild_id]

            return self.factory_manager.get_protocol(proto_name)
        return None

    def get_protocol_by_channel(self, channel_id):
        for proto in self.sub_protocols.itervalues():
            if proto.has_channel(channel_id):
                return proto

        return None

    def get_protocols_for_user(self, user_id):
        protos = []

        for proto in self.sub_protocols.itervalues():
            if proto.has_user(user_id):
                protos.append(proto)

        return protos

    def del_protocol(self, guild_id):
        proto = self.get_protocol(guild_id)

        if proto is None:
            return

        proto_name = proto.name

        del proto
        del self.sub_protocols[guild_id]

        return self.factory_manager.unload_protocol(proto_name)

    def add_guild(self, guild_obj):
        guild_id = int(guild_obj["id"])
        channels = guild_obj["channels"]
        members = guild_obj["members"]

        roles = guild_obj["roles"]
        done_roles = []

        for role in roles:
            done_roles.append(self.add_role(role))

            guild_obj["roles"] = done_roles

        for member in members:
            member["user"] = self.add_user(member["user"])

        existing_guild = self.get_guild(guild_id)

        if existing_guild is not None:
            for key, value in guild_obj.iteritems():
                if value is not None:
                    setattr(existing_guild, key, value)

            existing_protocol = self.get_protocol(existing_guild.id)
            existing_protocol.add_channels(channels)
            existing_protocol.add_members(members)

            return existing_guild

        name = guild_obj["name"]
        icon = guild_obj["icon"]
        splash = guild_obj["splash"]
        owner_id = guild_obj["owner_id"]
        region = guild_obj["region"]
        afk_channel_id = guild_obj["afk_channel_id"]
        afk_timeout = guild_obj["afk_timeout"]
        verification_level = guild_obj["verification_level"]
        emojis = guild_obj["emojis"]  # Array of emoji objects
        features = guild_obj["features"]  # ???

        embed_enabled = guild_obj.get("embed_enabled", False)
        embed_channel_id = guild_obj.get("embed_channel_id", None)
        presences = guild_obj.get("presences", [])

        guild = Guild(name, None, guild_id, icon, splash, owner_id,
                      region, afk_channel_id, afk_timeout, embed_enabled,
                      embed_channel_id, verification_level, roles, emojis,
                      features)

        self.add_protocol(guild, channels, members, presences)

        self.guilds[guild_id] = guild

        return guild

    def del_guild(self, guild):
        g = self.get_guild(guild)

        if g is not None:
            del self.guilds[guild.id]
            self.del_protocol(guild)

        return g

    def get_guild(self, guild):
        guild_obj = None

        if isinstance(guild, basestring):
            if INTEGER_REGEX.match(guild):
                guild_obj = self.guilds.get(int(guild), None)
            else:
                for g in self.guilds.values():
                    if g.name.lower() == guild.lower():
                        guild_obj = g
                        break
        else:
            guild_obj = self.guilds.get(guild, None)

        return guild_obj

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

    def get_channel(self, channel):
        """
        :rtype channel: system.protocols.discord.channel.Channel
        """
        if isinstance(channel, basestring):
            if INTEGER_REGEX.match(channel):
                return self.channels.get(int(channel), None)

            for c in self.channels.itervalues():
                if c.name.lower() == channel.lower():
                    return c
        elif isinstance(channel, Number):
            return self.channels.get(channel, None)

        return None

    def get_user(self, user):
        if isinstance(user, basestring):
            if user[0] == "@":
                user = user[1:]
            if INTEGER_REGEX.match(user):
                return self.get_user(int(user))
            for u in self.users.itervalues():
                if u.nickname == user:
                    return u
        elif isinstance(user, Number):
            for u in self.users.itervalues():
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
        return len(self.channels)

    def send_action(self, target, message, target_type=None, use_event=True):
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
                    word = u"<@{}>".format(user.id)

                words.append(word)

            message = " ".join(words)

        if self.config.get("mentions", {}).get("prevent_everyone", True):
            message = message.replace(u"@everyone", u"@{}everyone".format(ZWS))
            message = message.replace(u"@here", u"@{}here".format(ZWS))

        if isinstance(target, User):
            target = yield self.get_private_channel(target)

        if use_event:
            event = general_events.ActionSent(self, target, message)
            self.event_manager.run_callback("ActionSent", event)

            if event.cancelled:
                return

            if event.printable:
                self.log.info(u"-> *{}* {}".format(target.name, message))

        else:
            self.log.info(u"-> *{}* {}".format(target.name, message))

        self.add_to_queue(target.id, u"_{}_".format(message))

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
                    word = u"<@{}>".format(user.id)

                words.append(word)

            message = " ".join(words)

        if self.config.get("mentions", {}).get("prevent_everyone", True):
            message = message.replace(u"@everyone", u"@{}everyone".format(ZWS))
            message = message.replace(u"@here", u"@{}here".format(ZWS))

        if isinstance(target, User):
            target = yield self.get_private_channel(target)

        if use_event:
            event = general_events.MessageSent(self, "message", target, message)
            self.event_manager.run_callback("MessageSent", event)

            if event.cancelled:
                return

            if event.printable:
                self.log.info(u"-> *{}* {}".format(target.name, message))

        else:
            self.log.info(u"-> *{}* {}".format(target.name, message))

        self.add_to_queue(target.id, message)

    def add_to_queue(self, target, message):
        self.message_queue.append((target, message))

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

        if len(self.message_queue) < 1:
            self.stop_emptying_queue()
            return

        self.sending_message = True

        constructed = ""
        current_id = None

        while len(self.message_queue) > 0:
            _id, content = self.message_queue[0]

            if current_id is None:
                current_id = _id

            if _id != current_id:
                break

            message = MESSAGE_SEPARATOR + content

            if (len(constructed) + len(message)) < 2000:
                constructed += message
                self.message_queue.popleft()
            else:
                break

        if constructed.startswith(MESSAGE_SEPARATOR):
            constructed = constructed[len(MESSAGE_SEPARATOR):]

        try:
            _ = yield self.web_create_message(current_id, constructed)
        finally:
            self.sending_message = False

    def shutdown(self):
        for guild in list(self.guilds.values()):
            self.del_protocol(guild.id)

        self.stop_emptying_queue()
        self.message_queue.clear()
        self.stop_heartbeat()
        self.sendClose()
        self.transport.loseConnection()

    # endregion

    pass
