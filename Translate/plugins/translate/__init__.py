__author__ = 'Gareth Coles'

from goslate import Goslate, Error

from system.decorators.threads import run_async_threadpool
from system.command_manager import CommandManager
from system.plugins.plugin import PluginObject


class TranslatePlugin(PluginObject):
    commands = None
    goslate = None

    def setup(self):
        self.commands = CommandManager()
        self.goslate = Goslate()

        self.commands.register_command(
            "translate", self.translate_command, self, "translate.translate",
            ["tr", "t"], True
        )

    @run_async_threadpool
    def translate_command(self, protocol, caller, source, command, raw_args,
                          parsed_args):
        if len(parsed_args) < 2:
            caller.respond(
                "Usage: {CHARS}" + command + " <languages> <text>"
            )
            return

        langs = parsed_args[0]
        text = " ".join(parsed_args[1:])

        if ":" in langs:
            split = langs.split(":")
            from_lang, to_lang = split[0], split[1]
        else:
            from_lang, to_lang = "", langs

        try:
            translation = self.goslate.translate(text, to_lang, from_lang)

            source.respond("[{}] {}".format(to_lang, translation))
        except Error as e:
            source.respond("Translation error: {}".format(e))
