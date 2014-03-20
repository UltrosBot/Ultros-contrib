# coding=utf-8
__author__ = "Gareth Coles"

import math
import time

from system.command_manager import CommandManager
from system.event_manager import EventManager
from system.plugin import PluginObject
from utils.data import SqliteData


class LastseenPlugin(PluginObject):

    commands = None
    events = None

    data = None  # SQLite for a change

    def setup(self):
        self.commands = CommandManager()
        self.events = EventManager()
        self.data = SqliteData("plugins/lastseen/users.sqlite")

        with self.data as c:
            # Multiline strings because of an IDE bug
            c.execute("""CREATE TABLE IF NOT EXISTS users
                      (user TEXT, protocol TEXT, at INTEGER)""")

        self.commands.register_command("seen", self.seen_command, self,
                                       "seen.seen")

        # General events

        self.events.add_callback("PreMessageReceived", self,
                                 self.event_handler, 0, cancelled=True,
                                 extra_args=[self.event_source_caller])
        self.events.add_callback("PreCommand", self,
                                 self.event_handler, 0, cancelled=True,
                                 extra_args=[self.event_source_caller])
        self.events.add_callback("NameChanged", self,
                                 self.event_handler, 0, cancelled=True,
                                 extra_args=[self.event_user_caller])
        self.events.add_callback("UserDisconnected", self,
                                 self.event_handler, 0, cancelled=True,
                                 extra_args=[self.event_user_caller])

        # Mumble events

        self.events.add_callback("Mumble/UserRemove", self,
                                 self.event_handler, 0, cancelled=True,
                                 extra_args=[self.event_user_caller])
        self.events.add_callback("Mumble/UserJoined", self,
                                 self.event_handler, 0, cancelled=True,
                                 extra_args=[self.event_user_caller])
        self.events.add_callback("Mumble/UserMoved", self,
                                 self.event_handler, 0, cancelled=True,
                                 extra_args=[self.event_user_caller])
        self.events.add_callback("Mumble/UserSelfMuteToggle", self,
                                 self.event_handler, 0, cancelled=True,
                                 extra_args=[self.event_user_caller])
        self.events.add_callback("Mumble/UserSelfDeafToggle", self,
                                 self.event_handler, 0, cancelled=True,
                                 extra_args=[self.event_user_caller])
        self.events.add_callback("Mumble/UserRecordingToggle", self,
                                 self.event_handler, 0, cancelled=True,
                                 extra_args=[self.event_user_caller])

    def get_user(self, user, protocol):
        user = user.lower()
        with self.data as c:
            c.execute("""SELECT * FROM users WHERE user=? AND protocol=?""",
                      (user, protocol))
            d = c.fetchone()
            return d

    def insert_user(self, user, protocol):
        user = user.lower()
        with self.data as c:
            now = time.time()
            c.execute("""INSERT INTO users VALUES (?, ?, ?)""", (user,
                                                                 protocol,
                                                                 now))

    def update_user(self, user, protocol):
        user = user.lower()
        with self.data as c:
            now = time.time()
            c.execute("""UPDATE users SET at=? WHERE user=? AND protocol=?""",
                      (now, user, protocol))

    def seen_command(self, protocol, caller, source, command, raw_args,
                     parsed_args):
        args = raw_args.split()  # Quick fix for new command handler signature
        if not args:
            caller.respond("Usage: {CHARS}seen <username>")
        else:
            user = " ".join(args)

            if user.lower() == protocol.ourselves.nickname.lower():
                source.respond("I'm right here, smartass.")
                return

            if user.lower() == caller.nickname.lower():
                source.respond("Having a bit of an out-of-body experience, "
                               "%s?" % caller.nickname)
                return

            data = self.get_user(user, protocol.name)
            if not data:
                source.respond("User '%s' not found." % user)
            else:
                then = math.floor(data[2])
                now = math.floor(time.time())
                seconds = now - then

                m, s = divmod(seconds, 60)
                h, m = divmod(m, 60)
                d, h = divmod(h, 24)

                s = int(s)
                m = int(m)
                h = int(h)
                d = int(d)

                if (s + m + h + d) == 0:
                    source.respond("'%s' was seen just now!" % user)
                else:
                    constructed = "'%s' was seen" % user
                    to_append = []
                    if d > 0:
                        to_append.append("%s days" % d)
                    if h > 0:
                        to_append.append("%s hours" % h)
                    if m > 0:
                        to_append.append("%s minutes" % m)
                    if s > 0:
                        to_append.append("%s seconds" % s)

                    length = len(to_append)
                    i = 1

                    for x in to_append:
                        if length - i == 0:
                            if i != 1:
                                constructed += " and %s" % x
                                i += 1
                                continue
                        if i != 1:
                            constructed += ", %s" % x
                        else:
                            constructed += " %s" % x
                        i += 1

                    constructed += " ago."

                    source.respond(constructed)

    def event_handler(self, event, handler):
        """
        This is a generic function so that other plugins can catch events
        and cause a user's last seen value to update.

        The handler should return (username, protocol name) as a tuple,
        or a list of tuples if it needs to do more than one update.
        """
        data = handler(event)
        if not isinstance(data, list):
            data = [data]

        for element in data:
            user, proto = element
            self.update(user, proto)

    def update(self, user, proto):
        entry = self.get_user(user, proto)

        if not entry:
            self.insert_user(user, proto)
            self.logger.debug("Inserted %s@%s into the table." % (user, proto))
        else:
            self.update_user(user, proto)
            self.logger.debug("Updated entry for %s@%s." % (user, proto))

    def event_source_caller(self, event):
        user = event.source.nickname
        proto = event.caller.name

        return user, proto

    def event_user_caller(self, event):
        user = event.user.nickname
        proto = event.caller.name

        return user, proto
