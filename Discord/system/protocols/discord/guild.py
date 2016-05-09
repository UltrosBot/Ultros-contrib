# coding=utf-8
__author__ = 'Gareth Coles'


class Guild(object):
    def __init__(self, name, protocol, _id, icon, splash, owner_id, region,
                 afk_channel_id, afk_timeout, embed_enabled, embed_channel_id,
                 verification_level, roles, emojis, features):
        self.name = name
        self.protocol = protocol
        self.id = int(_id)
        self.icon = icon
        self.splash = splash
        self.owner_id = owner_id
        self.region = region
        self.afk_channel_id = afk_channel_id
        self.afk_timeout = afk_timeout
        self.embed_enabled = embed_enabled
        self.embed_channel_id = embed_channel_id
        self.verification_level = verification_level
        self.roles = roles
        self.emojis = emojis
        self.features = features

        self.name = self.name.strip()
