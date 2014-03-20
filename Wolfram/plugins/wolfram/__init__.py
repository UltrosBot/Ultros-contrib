__author__ = 'Gareth Coles'

import wolframalpha

from system.command_manager import CommandManager
from system.decorators import run_async
from system.plugin import PluginObject
from system.protocols.generic.channel import Channel
from utils.config import YamlConfig


class AuthPlugin(PluginObject):

    app = None

    config = None
    commands = None

    def setup(self):
        self.logger.debug("Entered setup method.")
        try:
            self.config = YamlConfig("plugins/wolfram.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            self.logger.error("Disabling..")
            self._disable_self()
            return
        if not self.config.exists:
            self.logger.error("Unable to find config/plugins/wolfram.yml")
            self.logger.error("Disabling..")
            self._disable_self()
            return

        self.commands = CommandManager()

        self.app = wolframalpha.Client(self.config["app_id"])

        self.commands.register_command("wolfram", self.wolfram_command, self,
                                       "wolfram.wolfram")

    @run_async
    def wolfram_command(self, protocol, caller, source, command, raw_args,
                        parsed_args):
        target = caller
        if isinstance(source, Channel):
            target = source

        if len(raw_args):
            try:
                res = self.app.query(raw_args)
                first = next(res.results)
                text = first.text.replace("\n", " ")

                target.respond(text)
            except Exception as e:
                if len(str(e)):
                    raise e
                else:
                    target.respond("No answer was found for your query.")

        else:
            caller.respond("Usage: .wolfram <query>")

    def deactivate(self):
        pass
