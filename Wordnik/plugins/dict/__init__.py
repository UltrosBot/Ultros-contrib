__author__ = 'Gareth Coles'

import urllib
from wordnik import swagger
from wordnik.WordApi import WordApi
from wordnik.WordsApi import WordsApi

from system.command_manager import CommandManager
from system.plugin import PluginObject
from system.plugin_manager import YamlPluginManagerSingleton
from system.protocols.generic.user import User
from utils.config import Config


class DictPlugin(PluginObject):

    api_key = ""
    api_client = None
    word_api = None
    words_api = None

    commands = None
    config = None
    plugman = None

    urls = None

    def setup(self):
        try:
            self.config = Config("plugins/wordnik.yml")
        except Exception:
            self.logger.exception("Unable to load the configuration!")
            return self._disable_self()
        if not self.config.exists:
            self.logger.error("Unable to find the configuration at "
                              "config/plugins/wordnik.yml - Did you fill "
                              "it out?")
            return self._disable_self()
        if not "apikey" in self.config or not self.config["apikey"]:
            self.logger.error("Unable to find an API key; did you fill out the"
                              " config?")
            return self._disable_self()

        self.api_key = self.config["apikey"]
        self.api_client = swagger.ApiClient(self.api_key,
                                            "http://api.wordnik.com/v4")
        self.word_api = WordApi(self.api_client)
        self.words_api = WordsApi(self.api_client)

        self.plugman = YamlPluginManagerSingleton.instance()
        self.urls = self.plugman.getPluginByName("URLs").plugin_object

        self.commands = CommandManager.instance()

        self.commands.register_command("dict", self.dict_command,
                                       self, "wordnik.dict")
        self.commands.register_command("wotd", self.wotd_command,
                                       self, "wordnik.wotd")

    def dict_command(self, caller, source, args, protocol):
        if len(args) < 1:
            caller.respond("Usage: {CHAR}dict <word to look up>")
        else:
            try:
                definition = self.get_definition(args[0])
                if not definition:
                    if isinstance(source, User):
                        caller.respond("%s | No definition found." % args[0])
                    else:
                        source.respond("%s | No definition found." % args[0])
                    return
                word = definition.word
                text = definition.text

                wiktionary_url = "http://en.wiktionary.org/wiki/%s" \
                                 % urllib.quote_plus(word)

                short_url = self.urls.tinyurl(wiktionary_url)
            except Exception as e:
                self.logger.exception("Error looking up word: %s" % args[0])
                caller.respond("Error getting definition: %s" % e)
            else:

                # Necessary attribution as per the Wordnik TOS
                if isinstance(source, User):
                    caller.respond("%s | %s (%s) - Provided by Wiktionary via "
                                   "the Wordnik API" % (word, text, short_url))
                else:
                    source.respond("%s | %s (%s) - Provided by Wiktionary via "
                                   "the Wordnik API" % (word, text, short_url))

    def wotd_command(self, caller, source, args, protocol):
        try:
            wotd = self.get_wotd()
            definition = self.get_definition(wotd)
            word = definition.word
            text = definition.text

            wiktionary_url = "http://en.wiktionary.org/wiki/%s" \
                             % urllib.quote_plus(word)

            short_url = self.urls.tinyurl(wiktionary_url)
        except Exception as e:
            self.logger.exception("Error looking up word of the day.")
            caller.respond("Error getting definition: %s" % e)
        else:

            # Necessary attribution as per the Wordnik TOS
            if isinstance(source, User):
                caller.respond("%s | %s (%s) - Provided by Wiktionary via "
                               "the Wordnik API" % (word, text, short_url))
            else:
                source.respond("%s | %s (%s) - Provided by Wiktionary via "
                               "the Wordnik API" % (word, text, short_url))

    def get_definition(self, word):
        result = self.word_api.getDefinitions(word, limit=1,
                                              sourceDictionaries="wiktionary")
        self.logger.debug("Data: %s" % result)
        if result:
            return result[0]
        return None

    def get_wotd(self):
        result = self.words_api.getWordOfTheDay()
        self.logger.debug("Data: %s" % result)
        return result.word
