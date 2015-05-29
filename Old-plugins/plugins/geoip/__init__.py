# coding=utf-8
__author__ = "Gareth Coles"

import json
import socket
import urllib

import system.plugin as plugin


class GeoIPPlugin(plugin.PluginObject):

    commands = None
    api_url = "https://www.telize.com/geoip/%s"

    def setup(self):
        self.commands.register_command(
            "geoip", self.command, self, "geoip.command", default=True
        )

    def command(self, protocol, caller, source, command, raw_args,
                args):
        if args is None:
            args = raw_args.split()

        if len(args) < 1:
            caller.respond("Usage: {CHARS}geoip <address>")
        else:
            try:
                args[0] = socket.gethostbyname(args[0])
            except socket.gaierror:
                source.respond("%s | Unknown host" % args[0])
                return

            addr = urllib.quote_plus(args[0])
            resp = urllib.urlopen(self.api_url % addr)
            data = resp.read()

            self.logger.trace("Data: %s" % repr(data))

            if data == "Not Found\n":
                source.respond("%s | Not found" % args[0])
            else:
                parsed = json.loads(data)
                country = parsed.get("country", None)
                region = parsed.get("region", None)
                city = parsed.get("city", None)
                isp = parsed.get("isp", None)

                if not country and not city and not region and not isp:
                    source.respond("%s | Not found" % args[0])
                    return

                source.respond("%s | %s, %s, %s (%s)" % (
                    args[0], city or "???", region or "???", country or "???",
                    isp or "Unknown ISP"
                ))
