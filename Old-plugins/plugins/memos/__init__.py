# coding=utf-8

from system.events.general import PreMessageReceived
from system.plugins.plugin import PluginObject
from system.storage.formats import YAML

__author__ = "NotMeh"
__all__ = ["MemosPlugin"]


class MemosPlugin(PluginObject):
    storage = None
    data = None

    def setup(self):
        self.data = self.storage.get_file(self, "data", YAML,
                                          "plugins/memos/memos.yml")

        self.commands.register_command("memo", self.memo, self, default=True,
                                       permission="memos.memo")

        self.events.add_callback("PreMessageReceived", self,
                                 self.message_received, 0)

    def memo(self, protocol, caller, source, command, raw_args, args):
        if args is None:
            args = raw_args.split()

        if len(args) < 2:
            caller.respond("Usage: {CHARS}memo <user> <message>")
            return

        user = args[0]
        message = "[{0}]: {1}".format(caller.name, " ".join(args[1:]))

        with self.data:
            if protocol.name in self.data:
                if user in self.data[protocol.name]:
                    self.data[protocol.name][user].append(message)
                else:
                    self.data[protocol.name].update({user: [message]})
            else:
                self.data[protocol.name] = {user: [message]}

        source.respond("I'll send it to {0}".format(user))

    def message_received(self, event=PreMessageReceived):
        if event.caller.name in self.data:
            if event.source.name in self.data[event.caller.name]:
                event.source.respond('Message for {0}: {1}'.format(
                    event.source.name,
                    self.data[event.caller.name][event.source.name]
                ))

                with self.data:
                    del self.data[event.caller.name][event.source.name]
