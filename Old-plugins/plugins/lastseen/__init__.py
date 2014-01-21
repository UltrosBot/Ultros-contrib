# coding=utf-8
__author__ = "Gareth Coles"

import math
import time

from system.command_manager import CommandManager
from system.event_manager import EventManager
from system.events.general import PreMessageReceived, PreCommand
from system.events.general import NameChanged, UserDisconnected
from system.plugin import PluginObject
from utils.data import SqliteData


class LastseenPlugin(PluginObject):

    commands = None
    events = None

    data = None  # SQLite for a change

    def setup(self):
        self.commands = CommandManager.instance()
        self.events = EventManager.instance()
        self.data = SqliteData("plugins/lastseen/users.sqlite")

        with self.data as c:
            # Multiline strings because of an IDE bug
            c.execute("""CREATE TABLE IF NOT EXISTS users
                      (user TEXT, protocol TEXT, at INTEGER)""")

        self.commands.register_command("seen", self.seen_command, self,
                                       "seen.seen")

        self.events.add_callback("PreMessageReceived", self,
                                 self.message_received, 0, cancelled=True)
        self.events.add_callback("PreCommand", self,
                                 self.pre_command, 0, cancelled=True)
        self.events.add_callback("NameChanged", self,
                                 self.name_changed, 0, cancelled=True)
        self.events.add_callback("UserDisconnected", self,
                                 self.user_disconnected, 0, cancelled=True)

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

    def message_received(self, event=PreMessageReceived):
        user = event.source.nickname
        proto = event.caller.name
        entry = self.get_user(user, proto)

        if not entry:
            self.insert_user(user, proto)
        else:
            self.update_user(user, proto)

    def pre_command(self, event=PreCommand):
        user = event.source.nickname
        proto = event.caller.name
        entry = self.get_user(user, proto)

        if not entry:
            self.insert_user(user, proto)
        else:
            self.update_user(user, proto)

    def name_changed(self, event=NameChanged):
        user = event.user.nickname
        proto = event.caller.name
        entry = self.get_user(user, proto)

        if not entry:
            self.insert_user(user, proto)
        else:
            self.update_user(user, proto)

    def user_disconnected(self, event=UserDisconnected):
        user = event.user.nickname
        proto = event.caller.name
        entry = self.get_user(user, proto)

        if not entry:
            self.insert_user(user, proto)
        else:
            self.update_user(user, proto)
