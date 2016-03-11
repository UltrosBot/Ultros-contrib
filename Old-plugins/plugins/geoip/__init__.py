# coding=utf-8
import json
import socket
import urllib

from system.decorators.threads import run_async_threadpool
from system.plugins.plugin import PluginObject

__author__ = "Gareth Coles"
__all__ = ["GeoIPPlugin"]


class GeoIPPlugin(PluginObject):
    # TODO: Move from urllib to txrequests

    api_url = "https://freegeoip.net/json/%s"

    def setup(self):
        self.commands.register_command(
            "geoip", self.command, self, "geoip.command", default=True
        )

    @run_async_threadpool
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

            try:
                addr = urllib.quote_plus(args[0])
                resp = urllib.urlopen(self.api_url % addr)
                data = resp.read()

                self.logger.trace("Data: %s" % repr(data))

                parsed = json.loads(data)
            except Exception as e:
                source.respond("%s | Not found" % args[0])
                self.logger.debug("Exception raised: {}".format(e))
                self.logger.debug("Data: {}".format(data))
            else:

                country = parsed.get("country_name", None)
                region = parsed.get("region_name", None)
                city = parsed.get("city", None)
                zip = parsed.get("zip_code", None)

                if not country and not city and not region and not zip:
                    source.respond("%s | Not found" % args[0])
                    return

                source.respond("%s | %s, %s, %s (%s)" % (
                    args[0],
                    city or "Unknown City",
                    region or "Unknown Region",
                    country or "Unknown Country",
                    zip or "Unknown Zip"
                ))
