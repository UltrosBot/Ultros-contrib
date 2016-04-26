# coding=utf-8
__author__ = 'Gareth Coles'


class Guild(object):
    def __init__(self, name, protocol, _id, icon, splash, owner_id, region,
                 afk_channel_id, afk_timeout, verification_level, roles,
                 emojis, features, channels, members):
        self.real_name = name
        self.protocol = protocol
        self.id = int(_id)
        self.icon = icon
        self.splash = splash
        self.owner_id = owner_id
        self.region = region
        self.afk_channel_id = afk_channel_id
        self.afk_timeout = afk_timeout
        self.verification_level = verification_level
        self.roles = roles
        self.emojis = emojis
        self.features = features
        self.channels = channels
        self.members = members

        d_m = self.protocol.discriminator_manager
        self.discriminator = d_m.get_guild_discriminator(self.id)

        self.name = ""

        for word in name.split():
            self.name += word[0].upper()

            if word[-1] in "!#$%&*./:;?@+|~":
                self.name += word[-1]
                self.name += " "

        self.name = self.name.strip()

    def update(self, other_guild):
        assert isinstance(other_guild, Guild)

        self.real_name = other_guild.real_name
        self.protocol = other_guild.protocol
        self.id = other_guild.id
        self.icon = other_guild.icon
        self.splash = other_guild.splash
        self.owner_id = other_guild.owner_id
        self.region = other_guild.region
        self.afk_channel_id = other_guild.afk_channel_id
        self.afk_timeout = other_guild.afk_timeout
        self.verification_level = other_guild.verification_level
        self.roles = other_guild.roles
        self.emojis = other_guild.emojis
        self.features = other_guild.features
        self.channels = other_guild.channels
        self.members = other_guild.members
        self.discriminator = other_guild.discriminator
        self.name = other_guild.name
