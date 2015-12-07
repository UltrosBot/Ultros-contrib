# coding=utf-8

__author__ = 'Gareth Coles'

import datetime
import time
import weakref

from utils.password import mkpasswd


class Sessions(object):

    _plugin_object = None
    sessions = {}

    @property
    def plugin(self):
        return self._plugin_object()

    def __init__(self, plugin, sessions):
        self._plugin_object = weakref.ref(plugin)
        self.sessions = sessions

        self.clear_old()

    def check_login(self, username, password):
        x = self.plugin.commands.auth_handler
        if x.check_login(username, password):
            return True

        return False

    def check_session(self, s):
        if not s["remember"]:
            then = datetime.datetime.fromtimestamp(s["time"])
            now = datetime.datetime.now()

            delta = now - then
            if delta > datetime.timedelta(days=30):
                return False

        return True

    def clear_old(self):
        done = 0

        with self.sessions:
            for key in list(self.sessions.keys()):
                s = self.sessions[key]

                if not self.check_session(s):
                    del self.sessions[key]
                    self.plugin.logger.debug("Removed session: %s" % key)
                    done += 1

        self.plugin.logger.info("Cleared %s old sessions" % done)

    def create_session(self, username, remember=False):
        username = username.lower()
        key = mkpasswd(100)

        s = {
            "username": username,
            "remember": remember,
            "time": time.mktime(datetime.datetime.now().timetuple())
        }

        with self.sessions:
            self.sessions[key] = s

        return key

    def delete_session(self, key):
        with self.sessions:
            if key in self.sessions:
                del self.sessions[key]
                return True

        return False

    def delete_sessions_for_user(self, username):
        with self.sessions:
            for key in list(self.sessions.keys()):
                if self.sessions[key]["username"] == username:
                    del self.sessions[key]

    def get_session(self, key):
        s = self.sessions.get(key, None)

        if s is None:
            return s

        if not self.check_session(s):
            with self.sessions:
                del self.sessions[key]

            return None

        return s

    def update_session_time(self, key):
        if key in self.sessions:
            with self.sessions:
                self.sessions[key]["time"] = time.mktime(
                    datetime.datetime.now().timetuple()
                )
