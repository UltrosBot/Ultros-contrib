# coding=utf-8

from system.protocols.generic.user import User as BaseUser

__author__ = 'Gareth Coles'


class User(BaseUser):
    voice_channel = None

    def __init__(self, nickname, protocol, _id, discriminator, avatar,
                 verified, email, deaf=False, mute=False, bot=False,
                 is_tracked=False):
        self.real_nickname = nickname
        self.protocol = protocol
        self.is_tracked = is_tracked

        self.id = int(_id)
        self.discriminator = int(discriminator)
        self.avatar = avatar
        self.verified = verified
        self.email = email
        self.deaf = deaf
        self.mute = mute
        self.bot = bot

        self.nickname = u"{}#{}".format(nickname, self.discriminator)

        self.roles = {}
        self.guilds = []

        self.game = None
        self.status = "offline"

    def can_ban(self, user, channel):
        pass

    def can_kick(self, user, channel):
        pass

    def respond(self, message):
        message = message.replace("{CHARS}", self.protocol.control_chars)
        self.protocol.send_msg(self, message)

    def update(self, other_user):
        assert isinstance(other_user, User)

        self.nickname = other_user.nickname
        self.protocol = other_user.protocol
        self.id = other_user.id
        self.discriminator = other_user.discriminator
        self.avatar = other_user.avatar
        self.verified = other_user.verified
        self.email = other_user.email
        self.deaf = other_user.deaf
        self.mute = other_user.mute
        self.bot = other_user.bot

    @staticmethod
    def from_message(message, protocol, is_tracked=False):
        return User(
            message["user"]["username"], protocol, message["user"]["id"],
            message["user"]["discriminator"], message["user"]["avatar"],
            verified=message.get("verified", message["user"].get("verified")),
            email=message.get("email", message["user"].get("email")),
            deaf=message.get("deaf", message["user"].get("deaf")),
            mute=message.get("mute", message["user"].get("mute")),
            bot=message.get("bot", message["user"].get("bot")),
            is_tracked=is_tracked
        )
