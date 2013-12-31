# coding=utf-8
__author__ = "Gareth Coles"

import json
import urllib

from system.command_manager import CommandManager
from system.plugin import PluginObject


class GeoIPPlugin(PluginObject):

    commands = None
    api_url = "http://freegeoip.net/json/%s"

    def setup(self):
        self.commands = CommandManager.instance()
        self.commands.register_command("geoip", self.command, self,
                                       "geoip.command")

    def command(self, caller, source, args, protocol):
        if len(args) < 1:
            caller.respond("Usage: {CHAR}geoip <address>")
        else:
            addr = urllib.quote_plus(args[0])
            resp = urllib.urlopen(self.api_url % addr)
            data = resp.read()

            if data.lower().strip("\n").strip("\r").strip(" ") == "notfound":
                source.respond("%s | Not found" % args[0])
            else:
                parsed = json.loads(data)
                country = parsed["country_name"]
                region = parsed["region_name"]
                city = parsed["city"]

                if not country and not city and not region:
                    source.respond("%s | Not found" % args[0])

                source.respond("%s | %s, %s, %s" % (args[0],
                                                    city or "???",
                                                    region or "???",
                                                    country or "???"))
