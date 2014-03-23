__author__ = 'Gareth Coles'

from system.events.base import PluginEvent


class ServerStartedEvent(PluginEvent):

    def __init__(self, caller, app):
        self.app = app
        super(ServerStartedEvent, self).__init__(caller)


class ServerStoppingEvent(PluginEvent):

    def __init__(self, caller, app):
        self.app = app
        super(ServerStoppingEvent, self).__init__(caller)


class ServerStoppedEvent(PluginEvent):

    def __init__(self, caller):
        super(ServerStoppedEvent, self).__init__(caller)
