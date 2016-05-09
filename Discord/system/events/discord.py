# coding=utf-8
from system.events.base import BaseEvent

__author__ = 'Gareth Coles'


class DiscordEvent(BaseEvent):
    """
    A Discord event. This will only be thrown from the Discord protocol.
    If an event subclasses this, chances are it's an Discord event.
    """

    def __init__(self, caller):
        super(DiscordEvent, self).__init__(caller)


class ChannelCreateEvent(DiscordEvent):
    def __init__(self, caller, channel):
        super(ChannelCreateEvent, self).__init__(caller)

        self.channel = channel


class ChannelRemoveEvent(DiscordEvent):
    def __init__(self, caller, channel):
        super(ChannelRemoveEvent, self).__init__(caller)

        self.channel = channel


class ChannelUpdateEvent(DiscordEvent):
    def __init__(self, caller, channel):
        super(ChannelUpdateEvent, self).__init__(caller)

        self.channel = channel


class GuildBanAddEvent(DiscordEvent):
    def __init__(self, caller, user, guild):
        super(GuildBanAddEvent, self).__init__(caller)

        self.user = user
        self.guild = guild


class GuildBanRemoveEvent(DiscordEvent):
    def __init__(self, caller, user, guild):
        super(GuildBanRemoveEvent, self).__init__(caller)

        self.user = user
        self.guild = guild


class GuildCreateEvent(DiscordEvent):
    def __init__(self, caller, guild):
        super(GuildCreateEvent, self).__init__(caller)

        self.guild = guild


class GuildDeleteEvent(DiscordEvent):
    def __init__(self, caller, guild, was_removed):
        super(GuildDeleteEvent, self).__init__(caller)

        self.guild = guild
        self.was_removed = was_removed  # Whether bot was removed from guild


class GuildEmojiUpdateEvent(DiscordEvent):
    def __init__(self, caller, guild, emojis):
        super(GuildEmojiUpdateEvent, self).__init__(caller)

        self.guild = guild
        self.emojis = emojis


class GuildIntegrationsUpdateEvent(DiscordEvent):
    def __init__(self, caller, guild):
        super(GuildIntegrationsUpdateEvent, self).__init__(caller)

        self.guild = guild


class GuildMemberAddEvent(DiscordEvent):
    def __init__(self, caller, guild, user, roles, joined_at):
        super(GuildMemberAddEvent, self).__init__(caller)

        self.guild = guild
        self.user = user
        self.roles = roles
        self.joined_at = joined_at


class GuildMemberChunk(DiscordEvent):
    def __init__(self, caller, guild, members):
        super(GuildMemberChunk, self).__init__(caller)

        self.guild = guild
        self.members = members


class GuildMemberRemoveEvent(DiscordEvent):
    def __init__(self, caller, guild, user):
        super(GuildMemberRemoveEvent, self).__init__(caller)

        self.guild = guild
        self.user = user


class GuildMemberUpdateEvent(DiscordEvent):
    def __init__(self, caller, guild, user, roles):
        super(GuildMemberUpdateEvent, self).__init__(caller)

        self.guild = guild
        self.user = user
        self.roles = roles


class GuildRoleCreateEvent(DiscordEvent):
    def __init__(self, caller, guild, role):
        super(GuildRoleCreateEvent, self).__init__(caller)

        self.guild = guild
        self.role = role


class GuildRoleDeleteEvent(DiscordEvent):
    def __init__(self, caller, guild, role):
        super(GuildRoleDeleteEvent, self).__init__(caller)

        self.guild = guild
        self.role = role


class GuildRoleUpdateEvent(DiscordEvent):
    def __init__(self, caller, guild, role):
        super(GuildRoleUpdateEvent, self).__init__(caller)

        self.guild = guild
        self.role = role


class GuildUpdateEvent(DiscordEvent):
    def __init__(self, caller, guild):
        super(GuildUpdateEvent, self).__init__(caller)

        self.guild = guild


class MessageCreateEvent(DiscordEvent):
    def __init__(self, caller, message_id, channel, author, content,
                 timestamp, edited_timestamp, tts, mention_everyone, mentions,
                 attachments, embeds, nonce):
        super(MessageCreateEvent, self).__init__(caller)

        self.message_id = message_id
        self.channel = channel
        self.author = author
        self.content = content
        self.timestamp = timestamp
        self.edited_timestamp = edited_timestamp
        self.tts = tts
        self.mention_everyone = mention_everyone
        self.mentions = mentions
        self.attachments = attachments
        self.embeds = embeds
        self.nonce = nonce


class MessageDeleteEvent(DiscordEvent):
    def __init__(self, caller, message_id, channel):
        super(MessageDeleteEvent, self).__init__(caller)

        self.message_id = message_id
        self.channel = channel


class MessageUpdateEvent(DiscordEvent):
    message_id = None
    channel = None

    changed_keys = []

    author = None
    content = None
    timestamp = None
    edited_timestamp = None
    tts = None
    mention_everyone = None
    mentions = None
    attachments = None
    embeds = None
    nonce = None

    def __init__(self, caller, message_id, channel, **kwargs):
        super(MessageUpdateEvent, self).__init__(caller)

        self.message_id = message_id
        self.channel = channel

        for k, v in kwargs.itervalues():
            self.changed_keys.append(k)
            setattr(self, k, v)


class PresenceUpdateEvent(DiscordEvent):
    def __init__(self, caller, user, guild, roles, game, status):
        super(PresenceUpdateEvent, self).__init__(caller)

        self.user = user
        self.guild = guild
        self.roles = roles
        self.game = game
        self.status = status


class ReadyEvent(DiscordEvent):
    def __init__(self, caller, guilds, heartbeat_interval, presences,
                 private_channels, session_id, user, gateway_version):
        super(ReadyEvent, self).__init__(caller)

        self.guilds = guilds
        self.heartbeat_interval = heartbeat_interval
        self.presences = presences
        self.private_channels = private_channels
        self.session_id = session_id
        self.user = user
        self.gateway_version = gateway_version


class TypingStartEvent(DiscordEvent):
    def __init__(self, caller, user, channel, timestamp):
        super(TypingStartEvent, self).__init__(caller)

        self.user = user
        self.channel = channel
        self.timestamp = timestamp


class UserSettingsUpdateEvent(DiscordEvent):
    def __init__(self, caller, data):
        super(UserSettingsUpdateEvent, self).__init__(caller)
        # Not documented by the Discord team, here for completion only

        self.data = data


class UserUpdateEvent(DiscordEvent):
    def __init__(self, caller, user):
        super(UserUpdateEvent, self).__init__(caller)

        self.user = user


class VoiceStateUpdateEvent(DiscordEvent):
    def __init__(self, caller, user, guild, channel, session_id, self_mute,
                 self_deaf, server_mute, server_deaf):
        super(VoiceStateUpdateEvent, self).__init__(caller)

        self.user = user
        self.guild = guild
        self.channel = channel
        self.session_id = session_id
        self.self_mute = self_mute
        self.self_deaf = self_deaf
        self.server_mute = server_mute
        self.server_deaf = server_deaf
