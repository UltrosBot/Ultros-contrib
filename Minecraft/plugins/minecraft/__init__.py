# coding=utf-8

import json
import urllib

from mcstatus import MinecraftServer

from twisted.internet import reactor
from twisted.internet.task import LoopingCall

from system.decorators.threads import run_async_threadpool
from system.plugins.plugin import PluginObject
from system.protocols.generic.user import User
from system.storage.formats import YAML

__author__ = 'Gareth Coles'
__all__ = ["MinecraftPlugin"]


class MinecraftPlugin(PluginObject):
    # TODO: Move to txrequests from urllib

    config = None

    status_url = "http://status.mojang.com/check"
    status_refresh_rate = 600

    task = None

    statuses = {
        "minecraft.net": "???",
        "login.minecraft.net": "???",
        "session.minecraft.net": "???",
        "account.mojang.com": "???",
        "auth.mojang.com": "???",
        "skins.minecraft.net": "???",
        "authserver.mojang.com": "???",
        "sessionserver.mojang.com": "???",
        "api.mojang.com": "???",
        "textures.minecraft.net": "???"
    }
    status_friendly_names = {
        "minecraft.net": "Website",
        "login.minecraft.net": "Login",
        "session.minecraft.net": "Session",
        "account.mojang.com": "Account",
        "auth.mojang.com": "Auth",
        "skins.minecraft.net": "Skins",
        "authserver.mojang.com": "Auth server",
        "sessionserver.mojang.com": "Session server",
        "api.mojang.com": "API",
        "textures.minecraft.net": "Textures"
    }

    @property
    def do_relay(self):
        if not self.relay_targets:
            return False

        return self.config["relay_status"]

    @property
    def relay_targets(self):
        return self.config["targets"]

    def setup(self):
        self.logger.trace("Entered setup method.")

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

        if not self.relay_targets:
            self.logger.warn("No valid target protocols found. "
                             "Disabling status relaying.")

        self.commands.register_command(
                "mcquery", self.query_command, self, b"minecraft.query",
                default=True
        )

        if self.do_relay:
            reactor.callLater(30, self.start_relay)

    def start_relay(self):
        self.check_status(True)

        self.task = LoopingCall(self.check_status)
        self.task.start(self.status_refresh_rate)

    def deactivate(self):
        if self.task:
            self.task.stop()

    @run_async_threadpool
    def query_command(self, protocol, caller, source, command, raw_args,
                      parsed_args):
        if len(parsed_args) < 1:
            caller.respond("Usage: {CHARS}mcquery <address[:port]>")
        address = parsed_args[0]
        target = source

        if isinstance(source, User):
            target = caller

        try:
            q = MinecraftServer.lookup(address)
            status = q.status()
        except Exception as e:
            target.respond("Error retrieving status: %s" % e)
            self.logger.exception("Error retrieving status")
            return

        servername = status.description

        if isinstance(servername, dict):
            servername = servername.get("text", "<Unknown server name>")

        done = ""
        done += "[%s] %s | " % (status.version.name, servername)
        done += "%s/%s " % (status.players.online, status.players.max)
        if "plugins" in status.raw:
            done += "| %s plugins" % len(status.raw["plugins"])

        target.respond(done)

        if protocol.can_flood and status.players.sample:
            players = ", ".join([x.name for x in status.players.sample])
            target.respond("Players: %s" % players)

    @run_async_threadpool
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
                        self.logger.trace(u"%s » %s" % (key, value))
                        if value == "green":
                            online.append(self.status_friendly_names[key])
                        elif value == "yellow":
                            problems.append(self.status_friendly_names[key])
                        else:
                            offline.append(self.status_friendly_names[key])

            self.logger.trace("%s status changes found." % (len(online) +
                                                            len(offline) +
                                                            len(problems)))

            parts = []

            for element in online:
                parts.append("%s » Online" % element)
            for element in problems:
                parts.append("%s » Problems" % element)
            for element in offline:
                parts.append("%s » Offline" % element)

            if parts:
                message = "Mojang status report [%s]" % " | ".join(parts)
                self.relay_message(message, firstparse)

            self.statuses = parsed_statuses
        except Exception:
            self.logger.exception("Error checking Mojang status")

    def relay_message(self, message, first=False):
        for target in self.relay_targets:
            proto = self.factory_manager.get_protocol(target["protocol"])

            if not proto:
                self.logger.warn("Protocol not found: %s" % target["protocol"])
                continue

            if first and not target.get("initial-relay", False):
                continue

            proto.send_msg(target["target"], message, target["target-type"])
