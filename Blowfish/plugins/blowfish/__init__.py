# coding=utf-8

"""
Blowfish-CDC support, as seen in Eggdrop and mIRC scripts.

Adds support for messages of the form "+OK <encrypted message>" for configured
targets, and will also send encrypted responses there.
"""

__author__ = "Gareth Coles"

import base64
import random
import string

from Crypto.Cipher import Blowfish

import system.plugin as plugin

from system.event_manager import EventManager
from system.events.general import PreMessageReceived, MessageSent
from system.storage.formats import YAML
from system.storage.manager import StorageManager


class BlowfishPlugin(plugin.PluginObject):
    """
    Blowfish-CDC support, as seen in Eggdrop and mIRC scripts
    """

    config = None
    events = None
    storage = None

    def get_target(self, protocol, target):
        return self.config.get(  # PEP! \o/
            protocol, {}
        ).get(
            "targets", {}
        ).get(
            target, None
        )

    def get_global(self, protocol):
        return self.config.get(protocol, {}).get("global", None)

    def setup(self):
        self.events = EventManager()
        self.storage = StorageManager()

        try:
            self.config = self.storage.get_file(self, "config", YAML,
                                                "plugins/blowfish.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            self._disable_self()
            return
        if not self.config.exists:
            self.logger.error("Unable to find config/plugins/blowfish.yml")
            self._disable_self()
            return

        self.events.add_callback(
            "PreMessageReceived", self, self.pre_message, 10001
        )

        self.events.add_callback(
            "MessageSent", self, self.message_sent, 10001
        )

    def pre_message(self, event=PreMessageReceived):
        if not event.caller:
            return

        target = event.target
        if not target:
            target = event.source

        key = self.get_target(event.caller.name, target)
        if not key:
            key = self.get_global(event.caller.name)
        if key:
            if event.message.startswith("+OK "):
                message = event.message[4:]

                try:
                    result = self.decode(key, message)
                except Exception:
                    self.logger.exception("Unable to decode message")
                    event.cancelled = True
                else:
                    event.message = result
            else:
                event.cancelled = True

    def message_sent(self, event=MessageSent):
        if not event.caller:
            return

        key = self.get_target(event.caller.name, event.target.name)
        if not key:
            key = self.get_global(event.caller.name)
        if key:
            message = event.message

            try:
                result = self.encode(key, message)
            except Exception:
                self.logger.exception("Unable to encode message")
                event.cancelled = True
            else:
                event.message = "+OK %s" % result

    def decode(self, key, text):
        binary = base64.b64decode(text)
        iv = binary[:8]
        encrypted = binary[8:]
        cipher = Blowfish.new(key, Blowfish.MODE_CBC, iv)

        decrypted = cipher.decrypt(encrypted)
        return decrypted.rstrip("\0")

    def encode(self, key, text):
        iv = "%s" % "".join(
            [random.choice(
                string.printable
            ) for x in range(8)]
        )
        cipher = Blowfish.new(key, Blowfish.MODE_CBC, iv)
        length = len(text)
        text += "\0" * abs((length % 8) - 8)
        binary = cipher.encrypt(text)
        return base64.b64encode("%s%s" % (iv, binary))
