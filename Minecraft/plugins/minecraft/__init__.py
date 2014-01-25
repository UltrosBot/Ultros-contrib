# coding=utf-8
__author__ = 'Gareth Coles'

from minecraft_query import MinecraftQuery

from system.command_manager import CommandManager
from system.plugin import PluginObject
from system.protocols.generic.user import User
from utils.config import YamlConfig


class Plugin(PluginObject):

    config = None
    commands = None

    def setup(self):
        self.logger.debug("Entered setup method.")
        try:
            self.config = YamlConfig("plugins/minecraft.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            self._disable_self()
            return
        if not self.config.exists:
            self.logger.error("Unable to find config/plugins/minecraft.yml")
            self.logger.error("Disabling..")
            self._disable_self()
            return

        self.commands = CommandManager.instance()
        self.commands.register_command("mcquery", self.query_command, self, "minecraft.query")

    def query_command(self, protocol, caller, source, command, raw_args,
                      parsed_args):
        if len(parsed_args) < 1:
            caller.respond("Usage: {CHARS}mcquery <address> [port]")
        address = parsed_args[0]
        port = "25565"
        if len(parsed_args) > 1:
            port = parsed_args[1]

        target = source
        if isinstance(source, User):
            target = caller

        try:
            port = int(port)
        except:
            caller.respond("'%s' is not a number.")
            return

        try:
            q = MinecraftQuery(address, int(port))
            status = q.get_rules()
        except Exception as e:
            caller.respond("Error retrieving status: %s" % e)
            return

        done = ""
        done += "[%s] %s | " % (status["version"], status["motd"])
        done += "%s/%s " % (status["numplayers"], status["maxplayers"])
        if "software" in status:
            done += "| %s " % status["software"]
        if "plugins" in status:
            done += "| %s plugins" % len(status["plugins"])

        target.respond(done)
        if protocol.can_spam and "players" in status:
            players = ", ".join(status["players"])
            target.respond("Players: %s" % players)
