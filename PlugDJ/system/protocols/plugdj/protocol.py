# coding=utf-8
__author__ = "Gareth Coles"

import HTMLParser

import system.protocols.plugdj.drivers as webdriver

from system.command_manager import CommandManager
from system.enums import CommandState
from system.event_manager import EventManager
from system.events import general as general_events
from system.events import plugdj as plug_events

from system.logging.logger import getLogger

from system.protocols.generic.protocol import NoChannelsProtocol
from system.protocols.plugdj.channel import Channel
from system.protocols.plugdj.user import User

from system.translations import Translations

from twisted.internet import reactor
from twisted.internet.task import LoopingCall

from utils.html import html_to_text
from utils.switch import Switch

_ = Translations().get()


class Protocol(NoChannelsProtocol):
    """
    Protocol for working with the music-sharing website plug.dj

    This is a channel-less protocol designed to connect to a single plug.dj
    room and provide a bot with various chat and moderation commands.

    We've done this using Selenium's WebDrivers, some tricky Javascript
    injection and some looped polling. We agree that this is somewhat hackish,
    but it's really the only feasible way to do something like this.

    We've customized a couple of the drivers to disable keep_alive as it seems
    to cause concurrency issues as well.
    """

    __version__ = "0.0.1"

    TYPE = "plugdj"
    CHANNELS = False

    factory = None
    config = None
    log = None
    event_manager = None
    command_manager = None

    nickname = ""
    ourselves = None
    can_flood = False

    control_chars = "."

    driver = None
    __task = None

    channel = None
    users = {}

    dj = None
    last_dj = None

    song = None
    waitlist = []

    html_parser = None

    def __init__(self, name, factory, config):
        NoChannelsProtocol.__init__(self, name, factory, config)
        self.log = getLogger(self.name)

        self.command_manager = CommandManager()
        self.event_manager = EventManager()

        self.html_parser = HTMLParser.HTMLParser()

        self.setup()

    # region Setup stages

    def setup(self):
        self.log.info("Setting up..")

        selenium = self.config.get("selenium", {})
        driver = selenium.get("driver", "firefox").lower()
        args = selenium.get("args", [])
        kwargs = selenium.get("kwargs", {})

        if driver == "firefox":
            self.driver = webdriver.Firefox(*args, **kwargs)
        elif driver == "chrome":
            self.driver = webdriver.Chrome(*args, **kwargs)
        elif driver == "ie":
            self.driver = webdriver.Ie(*args, **kwargs)
        elif driver == "opera":
            self.driver = webdriver.Opera(*args, **kwargs)
        elif driver == "safari":
            self.driver = webdriver.Safari(*args, **kwargs)
        elif driver == "phantomjs":
            self.driver = webdriver.PhantomJS(*args, **kwargs)
        elif driver == "android":
            self.driver = webdriver.Android(*args, **kwargs)
        elif driver == "remote":
            self.driver = webdriver.Remote(*args, **kwargs)
        else:
            self.log.error("Unknown web driver: %s" % driver)

            # Clean up so everything can be garbage-collected
            self.factory.manager.remove_protocol(self.name)

        reactor.callWhenRunning(self.setup_stage_0)

    def setup_stage_0(self):
        self.log.info("Waiting 30 seconds for the front page to load..")

        event = general_events.PreConnectEvent(self, self.config)
        self.event_manager.run_callback("PreConnect", event)

        try:
            self.driver.get("http://plug.dj")
        except Exception:
            self.log.exception("Error while logging in")
        else:
            reactor.callLater(30, self.setup_stage_1)

    def setup_stage_1(self):
        self.log.info("Logging in..")

        event = general_events.PostConnectEvent(self, self.config)

        self.event_manager.run_callback("PostConnect", event)

        try:
            self.driver.execute_script("$(\".existing button\").click();")

            self.driver.find_element_by_id("email").send_keys(
                self.config["identity"]["email"]
            )

            self.driver.find_element_by_id("password").send_keys(
                self.config["identity"]["password"]
            )

            self.driver.find_element_by_id("submit").click()
        except Exception:
            self.log.exception("Error while logging in")
        else:
            reactor.callLater(5, self.setup_stage_2)

    def setup_stage_2(self):
        self.log.info("Joining room and waiting 60 seconds for it to load..")

        event = general_events.PreSetupEvent(self, self.config)

        self.event_manager.run_callback("PreSetup", event)

        self.channel = Channel(self.config["channel"], self)

        try:
            self.driver.get("https://plug.dj/%s" % self.config["channel"])
        except Exception:
            self.log.exception("Error while joining room")
        else:
            reactor.callLater(60, self.setup_stage_3)

    def setup_stage_3(self):
        try:
            dj = self.call_api("getDJ")

            if dj:
                self.log.info("Current DJ: %s" % dj["username"])
            else:
                self.log.info("Nobody is playing anything right now.")
        except Exception:
            self.log.exception("Error checking current DJ")

        try:
            self.log.info("Injecting JavaScript..")

            script = open("system/protocols/plugdj/inject.js").read()

            self.driver.execute_script(script)
        except Exception:
            self.log.exception("Error injecting JavaScript")
        else:
            self.channel = Channel(self.config["channel"], self)
            for user in self.call_api("getUsers"):
                self.add_user(user)

            self.ourselves = self.get_user(
                self.call_api("getUser")
            )

            self.waitlist = sorted([
                self.add_user(u) for u in self.call_api("getWaitList")
            ], key=lambda x: x.waitlist_position)

            waiting = len(self.waitlist)

            if waiting > 1:
                self.log.info("%s users are waiting to play."
                              % len(self.waitlist))
            elif waiting == 1:
                self.log.info("1 user is waiting to play.")
            else:
                self.log.info("No users are waiting to play.")

            self.start_loop()

            event = general_events.PostSetupEvent(self, self.config)

            self.event_manager.run_callback("PostSetup", event)

    # endregion

    # region Message event loop

    def next_events(self):
        return self.driver.execute_script(
            "return document.ultros.get_items();"
        )

    def start_loop(self):
        self.__task = LoopingCall(self.event_loop)
        self.__task.start(0.05)

    def stop_loop(self):
        if self.__task:
            self.__task.stop()
        self.__task = None

    def event_loop(self):
        events = self.next_events()

        for event in events:
            self.log.trace(
                "Event (%s): %s" % (event["event"], event)
            )

            try:
                if event["event"] == "advance":
                    self.advance_event(event)
                elif event["event"] == "chat":
                    self.chat_event(event)
                elif event["event"] == "command":
                    self.command_event(event)
                elif event["event"] == "grab":
                    self.grab_event(event)
                elif event["event"] == "mod_skip":
                    self.mod_skip_event(event)
                elif event["event"] == "score":
                    self.score_event(event)
                elif event["event"] == "user_join":
                    self.user_join_event(event)
                elif event["event"] == "user_leave":
                    self.user_leave_event(event)
                elif event["event"] == "user_skip":
                    self.user_skip_event(event)
                elif event["event"] == "vote":
                    self.vote_event(event)
                elif event["event"] == "wait_list":
                    self.wait_list_event(event)
                else:
                    self.log.warn("Unknown event type: %s" % event["type"])
            except Exception:
                self.log.exception("Error actioning event!")
                self.log.error("Event: %s" % event)

    # endregion

    # region Plug event handlers

    def advance_event(self, event):
        if event["dj"]:
            user = self.get_user(event["dj"]["username"])

            self.last_dj = self.dj
            self.dj = user

            _event = plug_events.Advance(
                self, self.last_dj, self.dj,
                event["last_play"], event["media"],
                event["score"], event["raw_object"]
            )

            self.event_manager.run_callback("PlugDJ/Advance", _event)

            self.log.info("%s is now playing: %s - %s" % (
                user.username,
                event["media"]["author"],  # Not artist for some reason
                event["media"]["title"]
            ))
        else:
            self.last_dj = self.dj
            self.dj = None

            _event = plug_events.WaitlistEmpty(
                self, self.last_dj, event["last_play"],
                event["score"], event["raw_object"]
            )

            self.event_manager.run_callback("PlugDJ/WaitlistEmpty", _event)

            self.log.info("Everybody has left the waitlist.")

    def chat_event(self, event):
        message = html_to_text(event.get("message", ""))

        if event["type"] == "mention":
            event["type"] = "message"

            message = event["message"]
            if message.startswith(u"@%s" % self.ourselves.username):
                message = message.lstrip(u"@%s" % self.ourselves.username)
                message = message.lstrip()

            if not len(message):
                return

        if event["type"] == "message":
            if event["username"] == self.ourselves.username:
                return

            user = self.get_user(event["username"])

            _event = general_events.PreMessageReceived(
                self, user, self.channel, message, "message"
            )

            self.event_manager.run_callback("PreMessageReceived", _event)

            if _event.printable:
                self.log.info("<%s> %s" % (
                    user.username, _event.message
                ))

            if not _event.cancelled:
                result = self.command_manager.process_input(
                    _event.message, user, self.channel, self,
                    self.control_chars, self.ourselves.username
                )

                for case, default in Switch(result[0]):
                    if case(CommandState.RateLimited):
                        self.log.debug("Command rate-limited")
                        user.respond("That command has been rate-limited,"
                                     " please try again later.")
                        return  # It was a command
                    if case(CommandState.NotACommand):
                        self.log.debug("Not a command")
                        break
                    if case(CommandState.UnknownOverridden):
                        self.log.debug("Unknown command overridden")
                        return  # It was a command
                    if case(CommandState.Unknown):
                        self.log.debug("Unknown command")
                        break
                    if case(CommandState.Success):
                        self.log.debug("Command ran successfully")
                        return  # It was a command
                    if case(CommandState.NoPermission):
                        self.log.debug("No permission to run command")
                        return  # It was a command
                    if case(CommandState.Error):
                        user.respond("Error running command: %s" % result[1])
                        return  # It was a command
                    if default:
                        self.log.debug("Unknown command state: %s" % result[0])
                        break

                second_event = general_events.MessageReceived(
                    self, user, self.channel, _event.message, "message"
                )
                self.event_manager.run_callback(
                    "MessageReceived", second_event
                )
        elif event["type"] == "emote":
            if event["username"] == self.ourselves.username:
                return

            user = self.get_user(event["username"])

            _event = general_events.ActionReceived(
                self, user, self.channel, message
            )

            self.event_manager.run_callback("ActionReceived", _event)

            if _event.printable:
                self.log.info("* %s %s" % (
                    user.username, _event.message
                ))
        elif event["type"] == "moderation":
            _event = plug_events.ModerationMessage(
                self, event["message"], event["raw_object"]
            )

            self.event_manager.run_callback("PlugDJ/ModerationMessage", _event)

            if _event.printable:
                self.log.info("[Moderation] %s" %
                              event["message"])
        elif event["type"] == "system":
            _event = plug_events.SystemMessage(
                self, event["message"], event["raw_object"]
            )

            self.event_manager.run_callback("PlugDJ/SystemMessage", _event)

            if _event.printable:
                self.log.info("[System] %s" %
                              event["message"])
        elif event["type"] == "skip":
            _event = plug_events.SkipMessage(
                self, event["message"], event["raw_object"]
            )

            self.event_manager.run_callback("PlugDJ/SkipMessage", _event)
        elif event["type"] == "welcome":
            message = self.html_parser.unescape(event["message"])

            _event = plug_events.WelcomeMessage(
                self, message, event["raw_object"]
            )

            self.event_manager.run_callback("PlugDJ/WelcomeMessage", _event)

            if _event.printable:
                self.log.info("[Welcome] %s" % message)
        else:
            _event = plug_events.UnknownMessage(
                self, event["message"], event["raw_object"]
            )

            self.event_manager.run_callback("PlugDJ/UnknownMessage", _event)

            if _event.printable:
                self.log.warn("Unknown chat message type: %s" % event["type"])
                self.log.warn("Event: %s" % event)

    def command_event(self, event):
        _event = plug_events.Command(
            self, event["command"], event["raw_object"]
        )

        self.event_manager.run_callback("PlugDJ/Command", _event)

        if _event.printable:
            self.log.info("Command: %s" % event["command"])

    def grab_event(self, event):
        user = self.add_user(event["user"])

        _event = plug_events.Grabbed(
            self, self.call_api("getMedia"), user, event["raw_object"]
        )

        self.event_manager.run_callback("PlugDJ/Grabbed", _event)

        if _event.printable:
            self.log.info("%s grabbed the current song." %
                          user.username)

    def mod_skip_event(self, event):
        user = self.get_user(event["username"])

        _event = plug_events.ModeratorSkip(self, user, event["raw_object"])

        self.event_manager.run_callback("PlugDJ/ModeratorSkip", _event)

        if _event.printable:
            self.log.info("%s force-skipped the previous song." %
                          user.username)

    def score_event(self, event):
        _event = plug_events.Score(
            self, event["positive"], event["negative"], event["grabs"],
            event["raw_object"]
        )

        self.event_manager.run_callback("PlugDJ/Score", _event)

        if _event.printable:
            self.log.info("Score: +%s/-%s (%s grabs)" % (
                event["positive"], event["negative"], event["grabs"]
            ))

    def user_join_event(self, event):
        user = self.add_user(event["user"])

        _event = general_events.UserConnected(
            self, user
        )

        self.event_manager.run_callback("UserConnected", _event)

        self.log.info("User %s joined the room." % user.username)

        self.add_user(event["user"])

    def user_leave_event(self, event):
        user = self.get_user(event["user"])

        _event = general_events.UserDisconnected(
            self, user
        )

        self.event_manager.run_callback("UserDisconnected", _event)

        self.log.info("User %s left the room." % user.username)

        self.del_user(user.username)

    def user_skip_event(self, event):
        user = self.get_user(event["username"])

        _event = plug_events.UserSkip(self, user, event["raw_object"])

        self.event_manager.run_callback("PlugDJ/UserSkip", _event)

        if _event.printable:
            self.log.info("%s skipped the previous song." %
                          user.username)

    def vote_event(self, event):
        user = self.add_user(event["user"])

        _event = plug_events.Vote(
            self, user, event["vote"], event["raw_object"]
        )

        self.event_manager.run_callback("PlugDJ/Vote", _event)

        user.vote = event["vote"]

        if _event.printable:
            if event["vote"] > 0:
                self.log.info("%s wooted the current song." %
                              user.username)
            elif event["vote"] < 0:
                self.log.info("%s meh'd the current song." %
                              user.username)

    def wait_list_event(self, event):
        # Using add_user so the user object update
        users = [self.add_user(u) for u in event["users"]]

        joined = None
        left = None

        for u in users:
            if u not in self.waitlist:
                joined = u

        for u in self.waitlist:
            if u not in users:
                left = u

        self.waitlist = sorted(  # There's probably a better way :(
            users, key=lambda x: x.waitlist_position
        )

        if bool(left) != bool(joined):
            if joined is not None:
                _event = plug_events.JoinedWaitlist(
                    self, joined, self.waitlist, event["raw_object"]
                )

                self.event_manager.run_callback(
                    "PlugDJ/JoinedWaitlist", _event
                )

                if _event.printable:
                    self.log.info("%s joined the waitlist." % joined.username)
            if left is not None:
                _event = plug_events.LeftWaitlist(
                    self, left, self.waitlist, event["raw_object"]
                )

                self.event_manager.run_callback(
                    "PlugDJ/LeftWaitlist", _event
                )

                if _event.printable:
                    self.log.info("%s left the waitlist." % left.username)

    # endregion

    # region Plug-specific API functions

    def call_api(self, function, *args):
        to_append = []

        for arg in args:
            if isinstance(arg, str) or isinstance(arg, unicode):
                # Mandatory escaping for JS
                arg = arg.replace("\"", "\\\"")
                to_append.append("\"%s\"" % arg)
            else:
                to_append.append(repr(arg))

        return self.driver.execute_script(
            "return API.%s(%s);"
            % (function, ", ".join(to_append))
        )

    def woot(self):
        self.driver.find_element_by_id("woot").click()

    def meh(self):
        self.driver.find_element_by_id("meh").click()

    # endregion

    # region Internal functions

    def add_user(self, user_object):
        un = user_object["username"]
        if un in self.users:
            u = self.users.get(un)
            u.update_info(user_object)
        else:
            u = User(un, self, True)
            u.update_info(user_object)
            self.users[un] = u
        return u

    def del_user(self, username):
        if username in self.users:
            u = self.users.get(username)
            u.is_tracked = False
            del self.users[username]

    # endregion

    # region Public API functions

    def shutdown(self):
        """
        Called when a protocol needs to disconnect. Cleanup should be done
        here.
        """

        try:
            self.__task.stop()
        except Exception as e:
            self.log.warn("Error stopping task: %s" % e)

        try:
            self.driver.quit()
        except Exception as e:
            self.log.warn("Error shutting down driver: %s" % e)

    def get_channel(self, *args, **kwargs):
        return self.channel

    def get_user(self, user):
        """
        Used to retrieve a user.

        Return None if we can't find it. This also supports plug.dj user
        dicts, for ease of use.

        :param user: string or dict representing the user we need.
        :return User if found, else None
        :rtype User, None
        """
        if isinstance(user, str) or isinstance(user, unicode):
            return self.users.get(user, None)
        else:
            return self.users.get(user["username"], None)

    def send_msg(self, target, message, target_type=None, use_event=True):
        """
        Send a message to a user or a channel.

        :param target: A string, User or Channel object.
        :param message: The message to send.
        :param target_type: The type of target
        :param use_event: Whether to fire the MessageSent event or not.
        :return: Boolean describing whether the target was found and messaged.
        """

        if target is None or isinstance(target, Channel):
            event = general_events.MessageSent(
                self, "message", self.channel, message
            )

            self.event_manager.run_callback("MessageSent", event)

            self.call_api("sendChat", event.message)

            if event.printable:
                self.log.info("-> <%s> %s" % (
                    self.ourselves.username, event.message
                ))
        else:
            if isinstance(target, str) or isinstance(target, unicode):
                target = self.get_user(target)

            event = general_events.MessageSent(
                self, "message", target, message
            )

            self.event_manager.run_callback("MessageSent", event)

            self.call_api("sendChat", "@%s %s" % (target.name, event.message))

            if event.printable:
                self.log.info("-> <%s> @%s %s" % (
                    self.ourselves.username, target.name, event.message
                ))

    def send_action(self, target, message, target_type=None, use_event=True):
        """
        Send an action to a user of channel. (i.e. /me used action!)

        If a protocol does not have a separate method for actions, then this
        method should send a regular message in format "*message*", in italics
        if possible.

        :param target: A string, User or Channel object. Ignored here.
        :param message: The message to send.
        :param target_type: The type of target
        :param use_event: Whether to fire the MessageSent event or not.
        :return: Boolean describing whether the target was found and messaged.
        """

        event = general_events.ActionSent(self, self.channel, message)

        self.event_manager.run_callback("ActionSent", event)

        self.driver.find_element_by_id(
            "chat-input-field"
        ).send_keys(
            "/me %s\n" % event.message
        )

        if event.printable:
            self.log.info("-> * %s %s" % (
                self.ourselves.username, event.message
            ))

    def global_kick(self, user, channel=None, reason=None, force=False):
        raise NotImplementedError(_("This function needs to be implemented!"))

    def global_ban(self, user, channel=None, reason=None, force=False):
        raise NotImplementedError("This function needs to be implemented!")

    # endregion

    pass
