__author__ = 'Gareth Coles'

from system.events.base import BaseEvent


class InterEvent(BaseEvent):
    """
    An IRC event. This will only be thrown from the IRC protocol.
    If an event subclasses this, chances are it's an IRC event.
    """

    def __init__(self, caller):
        super(InterEvent, self).__init__(caller)


class InterServerConnected(InterEvent):
    """
    Fired when a server connects to Inter.
    """

    name = ""

    def __init__(self, caller, name):
        self.name = name

        super(InterServerConnected, self).__init__(caller)


class InterServerDisonnected(InterEvent):
    """
    Fired when a server disconnects from Inter.
    """

    name = ""

    def __init__(self, caller, name):
        self.name = name

        super(InterServerDisonnected, self).__init__(caller)


class InterServerListReceived(InterEvent):
    """
    Fired when we get our list of servers and their players.
    """

    servers = {}

    def __init__(self, caller, servers):
        self.servers = servers

        super(InterServerListReceived, self).__init__(caller)


class InterPlayerConnected(InterEvent):
    """
    Fired when a user connects.
    """

    user = None

    def __init__(self, caller, user):
        self.user = user

        super(InterPlayerConnected, self).__init__(caller)


class InterPlayerDisonnected(InterEvent):
    """
    Fired when a user connects.
    """

    user = None

    def __init__(self, caller, user):
        self.user = user

        super(InterPlayerDisonnected, self).__init__(caller)


class InterAuthenticated(InterEvent):
    """
    Fired when we've authenticated.
    """

    def __init__(self, caller):
        super(InterAuthenticated, self).__init__(caller)


class InterAuthenticationError(InterEvent):
    """
    Fired if there's an error authenticating.
    """

    error = ""

    def __init__(self, caller, error):
        self.error = error

        super(InterAuthenticationError, self).__init__(caller)


class InterCoreMessage(InterEvent):
    """
    Fired on a "core" message.
    """

    message = ""

    def __init__(self, caller, message):
        self.message = message

        super(InterCoreMessage, self).__init__(caller)


class InterPing(InterEvent):
    """
    Fired when we respond to a "ping" from the server.
    """

    timestamp = ""

    def __init__(self, caller, timestamp):
        self.timestamp = timestamp

        super(InterPing, self).__init__(caller)


class InterUnknownMessage(InterEvent):
    """
    Fired when we receive an unknown message.
    """

    message = ""

    def __init__(self, caller, message):
        self.message = message

        super(InterUnknownMessage, self).__init__(caller)
