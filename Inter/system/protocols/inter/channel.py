# coding=utf-8

__author__ = 'Sean'

from system.protocols.generic.channel import Channel as BaseChannel
from system.translations import Translations
_ = Translations().get()


class Channel(BaseChannel):

    name = "Global"

    def __init__(self, name="Global", protocol=None):
        self.name = name
        self.protocol = protocol

    def respond(self, message):
        self.protocol.send_msg(self, message)

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, Channel):
            return self.name == other.name
        return False

    def __ne__(self, other):
        if isinstance(other, Channel):
            return self.name != other.name
        return True
