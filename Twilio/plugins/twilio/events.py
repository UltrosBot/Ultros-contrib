__author__ = 'Gareth Coles'

from system.events.base import PluginEvent


class SMSReceivedEvent(PluginEvent):

    sender = None
    message = ""

    def __init__(self, caller, sender, message):
        self.sender = sender
        self.message = message
        super(SMSReceivedEvent, self).__init__(caller)
