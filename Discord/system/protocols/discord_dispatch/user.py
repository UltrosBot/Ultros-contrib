# coding=utf-8

from system.protocols.generic.user import User as BaseUser

__author__ = 'Gareth Coles'


class User(BaseUser):  # Really a guild member
    def __init__(self, nick, protocol, user, roles, joined_at, deaf, mute,
                 status=None, game=None, is_tracked=False):
        self.nick = nick
        self.protocol = protocol
        self.user = user
        self.roles = roles
        self.joined_at = joined_at
        self.deaf = deaf
        self.mute = mute
        self.status = status
        self.game = game
        self.is_tracked = is_tracked

    @property
    def nickname(self):
        return self.nick or self.user.nickname

    @property
    def id(self):
        return self.user.id

    def can_kick(self, user, channel):
        # TODO
        return False

    def can_ban(self, user, channel):
        # TODO
        return False

    def has_permission(self, permission):
        # TODO
        return False

    def respond(self, message):
        message = message.replace("{CHARS}", self.protocol.control_chars)
        self.protocol.send_msg(self, message)
