# coding=utf-8

import re

from system.plugins.plugin import PluginObject
from system.events.general import MessageReceived


__author__ = 'Gareth Coles'
__all__ = ["AssPlugin"]


class AssPlugin(PluginObject):

    regex = None

    def setup(self):
        self.regex = re.compile(r"(\w+)-ass (\w+)")

        self.events.add_callback("MessageReceived", self, self.ass_swap, 1)

    def ass_swap(self, event=MessageReceived):
        source = event.source
        target = event.target
        message = event.message

        if re.search(self.regex, message) is None:
            return

        result = re.sub(self.regex, r"\1 ass-\2", message)

        target.respond("%s: %s" % (source.nickname, result))
