"""
Events specifically related to the plug.dj protocol.
"""

__author__ = 'Gareth Coles'

from system.events.base import BaseEvent


class PlugDJEvent(BaseEvent):
    """
    Event specifically related to the plug.dj protocol.

    All events of this nature should subclass `PlugDJEvent`.
    """

    raw_object = None

    def __init__(self, caller, raw_object):
        self.raw_object = raw_object

        super(PlugDJEvent, self).__init__(caller)


class BaseMessageEvent(PlugDJEvent):
    """
    Base event for different Plug message events
    """

    message = ""
    printable = True

    def __init__(self, caller, message, raw_object, printable=True):
        self.message = message
        self.printable = printable

        super(BaseMessageEvent, self).__init__(caller, raw_object)


class ModerationMessage(BaseMessageEvent):
    """
    Thrown on a message of type "Moderation"
    """

    # TODO: Work out what this actually is


class SystemMessage(BaseMessageEvent):
    """
    Thrown on a system message from the PlugDJ staff
    """


class SkipMessage(BaseMessageEvent):
    """
    Thrown on the chat message sent when someone skips a song
    """


class WelcomeMessage(BaseMessageEvent):
    """
    Thrown when we connect to the chat server

    This usually won't be thrown, but expect to have to handle it as it will
    be thrown every time we lose connection to the chat server and
    reconnect.
    """


class UnknownMessage(BaseMessageEvent):
    """
    Thrown on a message of a type we don't know how to handle
    """


class BaseWaitlistEvent(PlugDJEvent):
    """
    Base event for different waitlist change events
    """

    user = None
    waitlist = []
    printable = True

    def __init__(self, caller, user, waitlist, raw_object, printable=True):
        self.user = user
        self.waitlist = waitlist
        self.printable = printable

        super(BaseWaitlistEvent, self).__init__(caller, raw_object)


class JoinedWaitlist(BaseWaitlistEvent):
    """
    Thrown when someone joins the waitlist
    """


class LeftWaitlist(BaseWaitlistEvent):
    """
    Thrown when someone leaves the waitlist
    """


class Advance(PlugDJEvent):
    """
    Thrown when the song advances
    """

    last_dj = None
    current_dj = None

    last_media = {}
    current_media = {}
    score = {}

    def __init__(self, caller, last_dj, dj, last_media, media, score,
                 raw_object):
        self.last_dj = last_dj
        self.current_dj = dj
        self.last_media = last_media
        self.current_media = media
        self.score = score

        super(Advance, self).__init__(caller, raw_object)


class WaitlistEmpty(PlugDJEvent):
    """
    Thrown when the waitlist becomes empty
    """

    last_dj = None

    last_media = {}
    score = {}

    def __init__(self, caller, last_dj, last_media, score, raw_object):
        self.last_dj = last_dj
        self.last_media = last_media
        self.score = score

        super(WaitlistEmpty, self).__init__(caller, raw_object)


class Command(PlugDJEvent):
    """
    Thrown when someone types a /command into the browser that isn't handled
    by plug itself
    """

    command = ""
    printable = True

    def __init__(self, caller, command, raw_object, printable=True):
        self.command = command
        self.printable = printable

        super(Command, self).__init__(caller, raw_object)


class Grabbed(PlugDJEvent):
    """
    Thrown when a user grabs the current song
    """

    media = {}
    user = None

    printable = True

    def __init__(self, caller, media, user, raw_object, printable=True):
        self.media = media
        self.user = user
        self.printable = printable

        super(Grabbed, self).__init__(caller, raw_object)


class ModeratorSkip(PlugDJEvent):
    """
    Thrown when a moderator force-skips the current song
    """

    user = None
    printable = True

    def __init__(self, caller, user, raw_object, printable=True):
        self.user = user
        self.printable = printable

        super(ModeratorSkip, self).__init__(caller, raw_object)


class Score(PlugDJEvent):
    """
    Thrown whenever the hell Plug feels like it

    Seems to be thrown whenever someone votes, grabs, skips or changes
    song.
    """

    woots = 0
    mehs = 0
    grabs = 0

    printable = True

    def __init__(self, caller, woots, mehs, grabs, raw_object, printable=True):
        self.woots = woots
        self.mehs = mehs
        self.grabs = grabs
        self.printable = printable

        super(Score, self).__init__(caller, raw_object)


class UserSkip(ModeratorSkip):
    """
    Thrown when a user skips their own song
    """


class Vote(PlugDJEvent):
    """
    Thrown when a user votes to woot or meh

    If *vote* is positive, the user voted to woot.
    If *vote* is negative, the user voted to meh.
    """

    user = None
    vote = 0

    printable = True

    def __init__(self, caller, user, vote, raw_object, printable=True):
        self.user = user
        self.vote = vote
        self.printable = printable

        super(Vote, self).__init__(caller, raw_object)
