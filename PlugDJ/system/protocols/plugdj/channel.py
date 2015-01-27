__author__ = 'Gareth Coles'

from system.protocols.generic.channel import Channel as BaseChannel
from system.translations import Translations
_ = Translations().get()


class Channel(BaseChannel):
    def respond(self, message):
        return self.protocol.send_msg(self, message)

    def __str__(self):
        return self.name
