# coding=utf-8

import random
import re

from system.plugins.plugin import PluginObject
from system.storage.formats import YAML

__author__ = 'Sean'
__all__ = ["EightBallPlugin"]


class EightBallPlugin(PluginObject):

    def setup(self):
        # Initial config load
        try:
            self._config = self.storage.get_file(
                self, "config", YAML, "plugins/8ball.yml"
            )
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

        # Setup some stuff
        self._random = random.Random()
        self._question_regex = re.compile("[\W_]+")

        # Register commands
        self.commands.register_command("8ball",
                                       self.eight_ball_cmd,
                                       self,
                                       "8ball.8ball",
                                       default=True)

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

    @property
    def same_answers(self):
        # Default False to keep old behaviour
        return self._config.get("same_answers", False)

    def eight_ball_cmd(self, protocol, caller, source, command, raw_args,
                       parsed_args):
        source.respond("[8ball] " + self.get_response(raw_args))

    def get_response(self, question=None):
        if self.same_answers and question is not None:
            try:
                qseed = question.encode("ascii", "ignore").strip().lower()
                qseed = self._question_regex.sub("", qseed)
                self.logger.debug("qseed: %s" % qseed)
                self._random.seed(qseed)
            except Exception:
                self.logger.exception(
                    "Error while reducing question. Please alert the author."
                )
        # Use self._random so that we can seed it (above) to always get the
        # same answer.
        choice = self._random.randint(1, 100)
        reply_type = "maybe"
        if choice <= self.yes_chance:
            reply_type = "yes"
        elif choice <= self.yes_chance + self.no_chance:
            reply_type = "no"
        # We don't want to use the re-seeded random here or we'll always get
        # the exact same response.
        return random.choice(self._config["responses"][reply_type])
