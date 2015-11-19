__author__ = 'Gareth Coles'

import time
import weakref

from utils.password import mkpasswd


class APIKeys(object):

    _plugin_object = None
    data = {}

    @property
    def plugin(self):
        return self._plugin_object()

    def __init__(self, plugin, data):
        self._plugin_object = weakref.ref(plugin)
        self.data = data

    def create_key(self, username, tries=0):
        username = username.lower()

        if tries > 4:
            raise KeyError("Unable to generate a unique API key!")

        key = mkpasswd(32)

        if key in self.data:
            time.sleep(0.01)
            return self.create_key(username, tries=tries + 1)

        with self.data:
            self.data[key] = username

        return key

    def delete_key(self, key):
        with self.data:
            if key in self.data:
                del self.data[key]
                return True
            return False

    def delete_username(self, username):
        keys = self.get_keys(username)

        results = []

        for key in keys:
            results.append(self.delete_key(key))

        return results

    def get_keys(self, username):
        username = username.lower()

        keys = []

        for key, value in self.data.iteritems():
            if value == username:
                keys.append(key)

        return keys

    def get_username(self, key):
        if key in self.data:
            return self.data[key]
        return None

    def is_owner(self, username, key):
        username = username.lower()

        return self.get_username(key) == username
