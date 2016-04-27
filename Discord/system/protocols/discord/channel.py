# coding=utf-8
from system.protocols.generic.channel import Channel as BaseChannel

__author__ = 'Gareth Coles'


class Channel(BaseChannel):
    guild_id = None

    def __init__(self, name, protocol, _id, guild_id, _type, position,
                 is_private, permission_overwrites, topic="",
                 last_message_id="", bitrate=-1):
        super(Channel, self).__init__(name, protocol)
        self.real_name = self.name

        self.id = int(_id)

        if guild_id:
            self.guild_id = int(guild_id)

        self.type = _type
        self.position = position
        self.private = is_private
        self.permission_overwrites = permission_overwrites
        self.topic = topic
        self.last_message_id = last_message_id
        self.bitrate = bitrate

        d_m = self.protocol.discriminator_manager
        self.discriminator = d_m.get_channel_discriminator(self.id)

        if self.guild_id:
            guild = self.protocol.get_guild(self.guild_id)

            if guild is not None:
                self.name = "{}#{}/{}#{}".format(
                    guild.name, guild.discriminator,
                    self.name, self.discriminator
                )

    def respond(self, message):
        message = message.replace("{CHARS}", self.protocol.control_chars)
        self.protocol.send_msg(self, message)

    def is_voice(self):
        return self.type == "voice" or self.bitrate != -1

    def is_text(self):
        return self.type == "text" or self.bitrate == -1

    def is_private(self):
        return self.private

    def get_type(self):
        if self.is_private():
            return "private"
        elif self.is_voice():
            return "voice"
        elif self.is_text():
            return "text"
        else:
            return None  # Hopefully shouldn't happen

    def update(self, other_channel):
        assert isinstance(other_channel, Channel)

        self.name = other_channel.name
        self.protocol = other_channel.protocol
        self.id = other_channel.id
        self.guild_id = other_channel.guild_id
        self.type = other_channel.type
        self.position = other_channel.position
        self.private = other_channel.private
        self.permission_overwrites = other_channel.permission_overwrites
        self.topic = other_channel.topic
        self.last_message_id = other_channel.last_message_id
        self.bitrate = other_channel.bitrate

    @staticmethod
    def from_message(message, protocol):
        return Channel(
            message["name"], protocol, message["id"], int(message["guild_id"]),
            message["type"], message["position"], False,
            message["permission_overwrites"], message.get("topic", ""),
            message.get("last_message_id", ""), message.get("bitrate", -1)
        )


class PrivateChannel(Channel):
    def __init__(self, recipient, protocol, last_message_id, _id, is_private):
        super(PrivateChannel, self).__init__(
            recipient.nickname, protocol, _id, None, "text", 0,
            is_private, [], "", last_message_id, -1
        )

    def respond(self, message):
        pass

    def update(self, other_channel):
        assert isinstance(other_channel, PrivateChannel)

        self.name = other_channel.name
        self.protocol = other_channel.protocol
        self.last_message_id = other_channel.last_message_id
        self.id = other_channel.last_message_id
        self.private = other_channel.is_private

    @staticmethod
    def from_message(message, protocol):
        return PrivateChannel(
            message["recipient"], protocol,
            message["last_message_id"], message["id"], message["is_private"]
        )
