# coding=utf-8
from numbers import Number

from system.commands.manager import CommandManager
from system.events.manager import EventManager
from system.factory_manager import FactoryManager

from system.protocols.discord.discriminators import DiscriminatorManager
from system.protocols.discord.protocol import Protocol as DiscordProtocol, \
    INTEGER_REGEX
from system.protocols.discord_dispatch.channel import TextChannel, VoiceChannel

from system.protocols.discord_dispatch.user import User
from system.protocols.discord_dispatch.misc import Game

from system.protocols.generic.protocol import ChannelsProtocol

from system.storage.manager import StorageManager

__author__ = 'Gareth Coles'


class Protocol(ChannelsProtocol):
    __version__ = "0.0.1"
    TYPE = "discord_dispatch"

    command_manager = None
    discriminator_manager = None
    event_manager = None
    factory_manager = None
    storage_manager = None

    dispatch_protocol = DiscordProtocol
    guild = None

    channels = {}
    members = {}

    def __init__(self, name, factory, config):
        ChannelsProtocol.__init__(self, name, factory, config)
        self.setup()

    def setup(self):
        self.command_manager = CommandManager()
        self.event_manager = EventManager()
        self.factory_manager = FactoryManager()
        self.storage_manager = StorageManager()

        self.dispatch_protocol = self.factory_manager.get_protocol(
            self.config["parent-protocol"]
        )

        self.guild = self.dispatch_protocol.get_guild(self.config["guild"])

        self.discriminator_manager = DiscriminatorManager(self)
        self.discriminator_manager.setup()

        self.add_channels(self.config["channels"])
        self.add_members(self.config["members"])
        self.add_presences(self.config["presences"])

    def shutdown(self):
        self.channels.clear()
        self.members.clear()
        self.guild = None
        self.discriminator_manager = None

        self.factory.shutting_down = True

    def add_channels(self, channels):
        for channel_obj in channels:
            self.add_channel(channel_obj)

    def add_members(self, members):
        for member_obj in members:
            self.add_user(member_obj)

    def add_presences(self, presences):
        for presence_obj in presences:
            self.set_presence(presence_obj)

    # region: Dispatch handlers

    def dispatch_text_channel_created(
        self, _id, name, position, permission_overwrites, topic,
        last_message_id
    ):
        pass

    def dispatch_text_channel_updated(self, channel_id, partial):
        pass

    def dispatch_text_channel_removed(self, channel_id):
        pass

    def dispatch_voice_channel_created(
        self, _id, name, position, permission_overwrites, bitrate
    ):
        pass

    def dispatch_voice_channel_updated(self, channel_id, partial):
        pass

    def dispatch_voice_channel_removed(self, channel_id):
        pass

    def dispatch_ban_added(self, user_id):
        pass

    def dispatch_ban_removed(self, user_id):
        pass

    def dispatch_guild_updated(self, partial):
        pass

    def dispatch_emoji_updated(self, emojis):
        pass

    def dispatch_integrations_updated(self):
        pass

    def dispatch_member_added(self, user, nick, roles, joined_at, deaf, mute):
        pass

    def dispatch_member_updated(self, **partial):
        # Note: May contain a nick key
        pass

    def dispatch_member_removed(self, user_id):
        pass

    def dispatch_role_created(self, role):
        pass

    def dispatch_role_updated(self, role):
        pass

    def dispatch_role_removed(self, role_id):
        pass

    def dispatch_message_created(self):
        pass

    def dispatch_message_updated(self):
        pass

    def dispatch_message_deleted(self):
        pass

    def dispatch_presence_updated(self, user_id, status, roles, game_name,
                                  game_url, game_type):
        pass

    def dispatch_typing_started(self):
        pass

    def dispatch_voice_state_updated(self, user_id, session_id, self_mute,
                                     self_deaf, server_mute, server_deaf):
        pass

    def dispatch_member_chunk(self, members):
        pass

    # endregion

    # region: Channel management

    def add_channel(self, channel_obj):
        existing_channel = self.get_channel(int(channel_obj["id"]))

        if existing_channel:
            for k, v in channel_obj.iteritems():
                if v is not None:
                    setattr(channel_obj, k, v)

            return existing_channel

        _type = channel_obj["type"]

        _id = channel_obj["id"]
        name = channel_obj["name"]
        position = channel_obj["position"]
        permission_overwrites = channel_obj["permission_overwrites"]

        if _type == "text":
            topic = channel_obj["topic"]
            last_message_id = channel_obj["last_message_id"]

            channel = TextChannel(
                name, _id, position, permission_overwrites, topic,
                last_message_id, self
            )
        else:
            bitrate = channel_obj["bitrate"]

            channel = VoiceChannel(
                name, _id, position, permission_overwrites, bitrate, self
            )

        self.channels[_id] = channel
        return channel

    def get_channel(self, channel_id):
        if isinstance(channel_id, basestring):
            if INTEGER_REGEX.match(channel_id):
                return self.channels.get(int(channel_id), None)

            for c in self.channels.itervalues():
                if c.name.lower() == channel_id.lower():
                    return c
        elif isinstance(channel_id, Number):
            return self.channels.get(channel_id, None)

        return None

    def del_channel(self, channel_id):
        c = self.get_channel(channel_id)

        if c is not None:
            del self.channels[c.id]

        return c

    def has_channel(self, channel_id):
        return self.get_channel(channel_id) is not None

    # endregion

    # region: User management

    def add_user(self, member_obj):
        user = member_obj["user"]
        exising_member = self.get_user(user.id)

        if exising_member:
            for k, v in member_obj.iteritems():
                if v is not None:
                    setattr(member_obj, k, v)
            return exising_member

        user = member_obj["user"]
        nick = member_obj.get("nick", None)
        roles = member_obj["roles"]
        joined_at = member_obj["joined_at"]
        deaf = member_obj["deaf"]
        mute = member_obj["mute"]

        member = User(nick, self, user, roles, joined_at, deaf, mute)
        member.is_tracked = True

        self.members[user.id] = member
        return member

    def get_user(self, member_id):
        if isinstance(member_id, basestring):
            if member_id[0] == "@":
                member_id = member_id[1:]
            if INTEGER_REGEX.match(member_id):
                return self.get_user(int(member_id))
            for u in self.users.itervalues():
                if u.nickname == member_id:
                    return u
        elif isinstance(member_id, Number):
            for u in self.users.itervalues():
                if u.id == member_id:
                    return u
        return None

    def del_user(self, member_id):
        u = self.get_user(member_id)

        if u is not None:
            del self.members[u.id]

        return u

    def has_user(self, member_id):
        return self.get_user(member_id) is not None

    def set_presence(self, presence_obj):
        u = self.get_user(int(presence_obj["user"]["id"]))

        if u is not None:
            game = presence_obj.get("game", None)

            if game is not None:
                game_name = game["name"]
                game_type = game["type"]
                game_url = game["url"]

                u.game = Game(game_name, game_type, game_url)

            roles = presence_obj.get("roles", None)

            if roles is not None:
                roles = [
                    self.dispatch_protocol.get_role(int(r)) for r in roles
                ]
                u.roles = roles

            status = presence_obj.get("status", None)

            if status is not None:
                u.status = status

    # endregion

    # region: Ultros protocol methods

    @property
    def num_channels(self):
        return len(self.channels)

    def send_msg(self, target, message, target_type=None, use_event=True):
        pass

    def global_ban(self, user, reason=None, force=False):
        pass

    def global_kick(self, user, reason=None, force=False):
        pass

    def send_action(self, target, message, target_type=None, use_event=True):
        pass

    def channel_ban(self, user, channel=None, reason=None, force=False):
        pass

    def channel_kick(self, user, channel=None, reason=None, force=False):
        pass

    def leave_channel(self, channel, reason=None):
        pass

    def join_channel(self, channel, password=None):
        pass

    # endregion

    pass
