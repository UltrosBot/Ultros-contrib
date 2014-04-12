# coding=utf-8
__author__ = 'Gareth Coles'

import json
import urllib

from minecraft_query import MinecraftQuery
from twisted.internet import reactor

from system.command_manager import CommandManager
from system.decorators import run_async_daemon
from system.plugin import PluginObject
from system.protocols.generic.user import User
from system.storage.formats import YAML
from system.storage.manager import StorageManager


class Plugin(PluginObject):

    config = None
    commands = None
    storage = None

    do_relay = False
    relay_targets = []

    status_url = "http://status.mojang.com/check"
    status_refresh_rate = 600

    statuses = {
        "minecraft.net": "???",
        "login.minecraft.net": "???",
        "session.minecraft.net": "???",
        "account.mojang.com": "???",
        "auth.mojang.com": "???",
        "skins.minecraft.net": "???",
        "authserver.mojang.com": "???",
        "sessionserver.mojang.com": "???"
    }
    status_friendly_names = {
        "minecraft.net": "Website",
        "login.minecraft.net": "Login",
        "session.minecraft.net": "Session",
        "account.mojang.com": "Account",
        "auth.mojang.com": "Auth",
        "skins.minecraft.net": "Skins",
        "authserver.mojang.com": "Auth server",
        "sessionserver.mojang.com": "Session server"
    }

    def setup(self):
        self.logger.debug("Entered setup method.")
        self.storage = StorageManager()
        try:
            self.config = self.storage.get_file(self, "config", YAML,
                                                "plugins/minecraft.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            self._disable_self()
            return
        if not self.config.exists:
            self.logger.error("Unable to find config/plugins/minecraft.yml")
            self.logger.error("Disabling..")
            self._disable_self()
            return

        self.do_relay = self.config["relay_status"]
        self.relay_targets = self.config["targets"]

        if not self.relay_targets:
            self.logger.warn("No valid target protocols found. "
                             "Disabling status relaying.")
            self.do_relay = False

        self.commands = CommandManager()
        self.commands.register_command("mcquery", self.query_command, self,
                                       "minecraft.query")

        if self.do_relay:
            reactor.callLater(60, self.check_status)

    @run_async_daemon
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
            target.respond("Error retrieving status: %s" % e)
            return

        done = ""
        done += "[%s] %s | " % (status["version"], status["motd"])
        done += "%s/%s " % (status["numplayers"], status["maxplayers"])
        if "software" in status:
            done += "| %s " % status["software"]
        if "plugins" in status:
            done += "| %s plugins" % len(status["plugins"])

        target.respond(done)
        if protocol.can_flood and "players" in status \
           and len(status["players"]):
            players = ", ".join(status["players"])
            target.respond("Players: %s" % players)

    @run_async_daemon
    def check_status(self, firstparse=False):
        try:
            r = urllib.urlopen(self.status_url)
            d = r.read()

            parsed_statuses = {}

            online = []
            offline = []
            problems = []

            data = json.loads(d)
            for server in data:
                for key, value in server.items():
                    parsed_statuses[key] = value
                    if self.statuses[key] != value:
                        self.logger.debug(u"%s » %s" % (key, value))
                        if value == "green":
                            online.append(self.status_friendly_names[key])
                        elif value == "yellow":
                            problems.append(self.status_friendly_names[key])
                        else:
                            offline.append(self.status_friendly_names[key])

            self.logger.info("%s status changes found." % (len(online)
                                                           + len(offline)
                                                           + len(problems)))

            message = "Mojang status report "
            times = 0
            for element in online:
                if times:
                    message += "| %s » Online " % element
                else:
                    message += "[ %s » Online " % element
                times += 1
            for element in problems:
                if times:
                    message += "| %s » Problems " % element
                else:
                    message += "[ %s » Problems " % element
                times += 1
            for element in offline:
                if times:
                    message += "| %s » Offline " % element
                else:
                    message += "[ %s » Offline " % element
                times += 1

            if times:
                message += "]"
                self.relay_message(message, firstparse)

            self.statuses = parsed_statuses
        except:
            self.logger.exception("Error checking Mojang status")
        finally:
            reactor.callLater(self.status_refresh_rate, self.check_status)

    def relay_message(self, message, first=False):
        for target in self.relay_targets:
            proto = self.factory_manager.get_protocol(target["protocol"])
            if not proto:
                self.logger.warn("Protocol not found: %s" % target["protocol"])
            if first and not target["initial-relay"]:
                continue
            proto.send_msg(target["target"], message, target["target-type"])
