# coding=utf-8
from system.protocols.generic.channel import Channel

__author__ = 'Gareth Coles'


class GuildTextChannel(Channel):
    def __init__(self, name, _id, position, permission_overwrites, topic,
                 last_message_id, protocol=None):
        super(GuildTextChannel, self).__init__(name, protocol)

        self.id = int(_id)
        self.position = position
        self.permission_overwrites = permission_overwrites
        self.topic = topic
        self.last_message_id = last_message_id

    def respond(self, message):
        message = message.replace("{CHARS}", self.protocol.control_chars)
        self.protocol.send_msg(self, message)

    def __json__(self):
        pass


class GuildVoiceChannel(Channel):
    def __init__(self, name, _id, position, permission_overwrites, bitrate,
                 protocol=None):
        super(GuildVoiceChannel, self).__init__(name, protocol)

        self.id = int(_id)
        self.position = position
        self.permission_overwrites = permission_overwrites
        self.bitrate = bitrate

    def respond(self, message):
        pass

    def __json__(self):
        pass


class PrivateChannel(Channel):
    def __init__(self, recipient, protocol, last_message_id, _id, is_private):
        super(PrivateChannel, self).__init__(recipient.nickname, protocol)

        self.id = int(_id)
        self.is_private = is_private
        self.recipient = recipient
        self.last_message_id = last_message_id

    def respond(self, message):
        message = message.replace("{CHARS}", self.protocol.control_chars)
        self.protocol.send_msg(self, message)
