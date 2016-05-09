# coding=utf-8
from system.protocols.generic.user import User

__author__ = 'Gareth Coles'


class GuildMember(User):
    user = None
    roles = []
    joined_at = 0
    deaf = False
    mute = False

    def __init__(self, nick, user, roles, joined_at, deaf, mute,
                 protocol=None, is_tracked=False):
        super(GuildMember, self).__init__(nick, protocol, is_tracked)

        self.user = user
        self.roles = roles
        self.joined_at = joined_at
        self.deaf = deaf
        self.mute = mute

    # region: Properties from the underlying User object

    @property
    def id(self):
        return self.user.id

    @property
    def username(self):
        return self.user.username

    @property
    def discriminator(self):
        return self.user.discriminator

    @property
    def avatar(self):
        return self.user.avatar

    @property
    def verified(self):
        return self.user.verified

    @property
    def email(self):
        return self.user.email

    # endregion

    def can_ban(self, user, channel):
        return False

    def can_kick(self, user, channel):
        return False

    def respond(self, message):
        pass

    def __json__(self):
        pass
