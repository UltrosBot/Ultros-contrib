# coding=utf-8

import json
import re
import urllib2
import time

from system.plugins.plugin import PluginObject
from system.storage.formats import YAML


__author__ = 'Sean'
__all__ = ["AoSPlugin"]


class AoSPlugin(PluginObject):

    _STEAM_PLAYERS_REGEX = re.compile(
        r'apphub_NumInApp">(?P<players>.+) In-Game'
    )
    _IP_REGEX = re.compile(
        r'^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9]'
        r'[0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'
    )

    def setup(self):
        # Initial config load
        try:
            self._config = self.storage.get_file(self,
                                                 "config",
                                                 YAML,
                                                 "plugins/aoshelper.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            self.logger.error("Disabling...")
            self._disable_self()
            return
        if not self._config.exists:
            self.logger.error("Unable to find config/plugins/aoshelper.yml")
            self.logger.error("Disabling...")
            self._disable_self()
            return

        # Load options from config
        self._load()

        self._config.add_callback(self._load)

        # Register commands
        self.commands.register_command("aosplayercount",
                                       self.playercount_cmd,
                                       self,
                                       "aoshelper.playercount",
                                       [
                                           "playercount"
                                       ], default=True)
        self.commands.register_command("aostoip",
                                       self.aos_to_ip_command,
                                       self,
                                       "aoshelper.aostoip",
                                       [
                                           "aos2ip"
                                       ])
        self.commands.register_command("iptoaos",
                                       self.ip_to_aos_command,
                                       self,
                                       "aoshelper.iptoaos",
                                       [
                                           "ip2aos"
                                       ])

        # Setup soem variables
        self._last_update_voxlap = 0
        self._last_update_steam = 0
        self._last_voxlap_player_count = -1
        self._last_steam_player_count = -1

    def reload(self):
        try:
            self._config.reload()
        except Exception:
            self.logger.exception("Error reloading configuration!")
            return False
        return True

    def _load(self):
        self.cache_time = self._config["cache-time"]
        self.max_misses = self._config["max-misses"]

    def playercount_cmd(self, protocol, caller, source, command, raw_args,
                        parsed_args):
        voxlap_players = self.get_voxlap_player_count()
        steam_players = self.get_steam_player_count()
        percentage_players = "-1%"
        if voxlap_players is not None and steam_players is not None:
            percentage_players = str(
                round(
                    voxlap_players / float(
                        steam_players.translate(None, " ,")
                    ) * 100, 1
                )
            ) + '%'
        source.respond(
            "There are currently %s people playing 0.x, and %s people playing "
            "1.0. 0.x player count is %s the size of 1.0's. Graph at "
            "http://goo.gl/M5h3q" % (
                voxlap_players,
                steam_players,
                percentage_players
            )
        )

    def aos_to_ip_command(self, protocol, caller, source, command, raw_args,
                          parsed_args):
        if len(parsed_args) == 1:
            result = self.convert_aos_address_to_ip(parsed_args[0])
            if not result:
                source.respond("Could not get IP for %s" % parsed_args[0])
            else:
                source.respond("IP for %s is %s" % (parsed_args[0], result))
        else:
            caller.respond("Usage: {CHARS}%s <AoS address>" % command)

    def ip_to_aos_command(self, protocol, caller, source, command, raw_args,
                          parsed_args):
        if len(parsed_args) == 1:
            result = self.convert_ip_to_aos_address(parsed_args[0])
            if not result:
                source.respond("Could not get AoS address for %s" %
                               parsed_args[0])
            else:
                source.respond("AoS address for %s is %s" % (
                    parsed_args[0], result))
        else:
            caller.respond("Usage: {CHARS}%s <IP address>" % command)

    def get_voxlap_player_count(self):
        now = time.time()
        time_since_last_update = now - self._last_update_voxlap
        if time_since_last_update > self.cache_time:
            try:
                server_list = json.loads(urllib2.urlopen(
                    "http://services.buildandshoot.com/serverlist.json").read()
                )
                players = 0
                for server in server_list:
                    players += server["players_current"]
                self._last_update_voxlap = now
                self._last_voxlap_player_count = players
                return players
            except:
                if time_since_last_update > self.cache_time * self.max_misses:
                    return None
                else:
                    return self._last_voxlap_player_count
        else:
            return self._last_voxlap_player_count

    def get_steam_player_count(self):
        now = time.time()
        time_since_last_update = now - self._last_update_steam
        if time_since_last_update > self.cache_time:
            try:
                page = urllib2.urlopen(
                    "http://steamcommunity.com/app/224540").read()
                match = self._STEAM_PLAYERS_REGEX.search(page)
                if match:
                    self._last_update_steam = now
                    self._last_steam_player_count = match.group("players")
                    return self._last_steam_player_count
                else:
                    raise Exception()
            except:
                if time_since_last_update > self.cache_time * self.max_misses:
                    return None
                else:
                    return self._last_steam_player_count
        else:
            return self._last_steam_player_count

    def convert_aos_address_to_ip(self, address):
        port = -1
        if address.startswith('aos://'):
            address = address[6:]
        if ':' in address:
            colon = address.index(':')
            port = address[colon + 1:]
            address = address[:colon]
        try:
            address = int(address)
        except:
            return False
        ip = "%i.%i.%i.%i" % tuple(
            (address >> (i * 8)) & 255 for i in xrange(4)
        )
        if port > -1:
            ip += ":" + port
        return ip

    def convert_ip_to_aos_address(self, address):
        port = -1
        if ':' in address:
            colon = address.index(':')
            port = address[colon + 1:]
            address = address[:colon]
        parts = address.split('.')
        try:
            parts = [int(part) for part in parts]
        except:
            return False
        ip = (((parts[3] * 256) + parts[2]) * 256 + parts[1]) * 256 + parts[0]
        if port > -1:
            ip = str(ip) + ":" + port
        return "aos://" + str(ip)

    def is_ip(self, string):
        return self._IP_REGEX.match(string)
