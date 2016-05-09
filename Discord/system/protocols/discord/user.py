# coding=utf-8

from system.protocols.generic.user import User as BaseUser

__author__ = 'Gareth Coles'


class User(BaseUser):
    def __init__(self, nickname, protocol, _id, discriminator, avatar,
                 verified, email, is_tracked=False):
        super(User, self).__init__(nickname, protocol, is_tracked)

        self.username = nickname

        self.id = int(_id)
        self.discriminator = int(discriminator)
        self.avatar = avatar
        self.verified = verified
        self.email = email

        self.nickname = u"{}#{}".format(nickname, self.discriminator)

    def can_ban(self, user, channel):
        return False

    def can_kick(self, user, channel):
        return False

    def respond(self, message):
        message = message.replace("{CHARS}", self.protocol.control_chars)
        self.protocol.send_msg(self, message)
