import random

from system.command_manager import CommandManager

import system.plugin as plugin

from system.storage.formats import YAML
from system.storage.manager import StorageManager


__author__ = 'Sean'


class JargonPlugin(plugin.PluginObject):

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
                                                 "plugins/jargon.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            self.logger.error("Disabling...")
            self._disable_self()
            return
        if not self._config.exists:
            self.logger.error("Unable to find config/plugins/jargon.yml")
            self.logger.error("Disabling...")
            self._disable_self()
            return

        ### Register commands
        self.commands.register_command("jargon",
                                       self.jargon_cmd,
                                       self,
                                       "jargon.jargon", default=True)

    def reload(self):
        try:
            self._config.reload()
        except Exception:
            self.logger.exception("Error reloading configuration!")
            return False
        return True

    def jargon_cmd(self, protocol, caller, source, command, raw_args,
                   parsed_args):
        source.respond(self.generate_sentence())

    def get_word(self, word_type):
        word_type = word_type.lower()
        if word_type == "verb":
            return random.choice(self._config["verbs"])["plain"]
        elif word_type == "verbing":
            verb = random.choice(self._config["verbs"])
            if "ing" in verb:
                return verb["ing"]
            else:
                return verb["plain"] + "ing"
        elif word_type == "noun":
            return random.choice(self._config["nouns"])
        elif word_type == "adjective":
            return random.choice(self._config["adjectives"])
        elif word_type == "abbreviation":
            return random.choice(self._config["abbreviations"])

    def generate_sentence(self):
        sentenceFormat = random.choice(self._config["formats"])
        words = []
        for word in sentenceFormat["types"]:
            words.append(self.get_word(word))
        return sentenceFormat["format"] % tuple(words)
