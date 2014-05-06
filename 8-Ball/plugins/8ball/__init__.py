import random

from system.command_manager import CommandManager

import system.plugin as plugin

from system.storage.formats import YAML
from system.storage.manager import StorageManager


__author__ = 'Sean'


class AoSPlugin(plugin.PluginObject):

    commands = None
    storage = None

    def setup(self):
        ### Grab important shit
        self.commands = CommandManager()
        self.storage = StorageManager()

        ### Initial config load
        try:
            self._config = self.storage.get_file(self,
                                                 "config",
                                                 YAML,
                                                 "plugins/8ball.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            self.logger.error("Disabling...")
            self._disable_self()
            return
        if not self._config.exists:
            self.logger.error("Unable to find config/plugins/8ball.yml")
            self.logger.error("Disabling...")
            self._disable_self()
            return

        ### Register commands
        self.commands.register_command("8ball",
                                       self.eight_ball_cmd,
                                       self,
                                       "8ball.8ball")

    def reload(self):
        try:
            self._config.reload()
        except Exception:
            self.logger.exception("Error reloading configuration!")
            return False
        return True

    @property
    def yes_chance(self):
        return self._config["chances"]["yes"]

    @property
    def no_chance(self):
        return self._config["chances"]["yes"]

    @property
    def maybe_chance(self):
        return 100 - self.yes_chance - self.no_chance

    def eight_ball_cmd(self, protocol, caller, source, command, raw_args,
                       parsed_args):
        source.respond("[8ball] " + self.get_response())

    def get_response(self):
        choice = random.randint(1, 100)
        reply_type = "maybe"
        if choice <= self.yes_chance:
            reply_type = "yes"
        elif choice <= self.yes_chance + self.no_chance:
            reply_type = "no"
        return random.choice(self._config["responses"][reply_type])
