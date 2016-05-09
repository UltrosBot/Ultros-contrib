# coding=utf-8

from system.protocols.discord.channel import GuildTextChannel, \
    GuildVoiceChannel

__author__ = 'Gareth Coles'


class TextChannel(GuildTextChannel):
    pass


class VoiceChannel(GuildVoiceChannel):
    pass
