__author__ = 'Jim'


import json
import mpmath
import urllib

import system.plugin as plugin

from system import command_manager
from system.storage.formats import YAML
from system.storage.manager import StorageManager
from datetime import datetime, timedelta
#from japan import loli_maids


class MoneyPlugin(plugin.PluginObject):

    rates_table = None
    rates_table_updated = datetime.now()

    config = None
    commands = None
    storage = None

    @property
    def precision(self):
        return self.config.get("precision", 2)

    def setup(self):
        self.storage = StorageManager()
        self.config = self.storage.get_file(self, "config", YAML,
                                            "plugins/money.yml")

        self.commands = command_manager.CommandManager()
        self.commands.register_command("money", self.money_command_called,
                                       self, "money.main")

        self._load()

        self.config.add_callback(self._load)

    def _load(self):
        mpmath.mp.dps = self.precision

        self.rates_table_updated = datetime.now()
        self.rates_table = self.get_rates_table(ignore_time=True)

    def decode_rates_table(self, data):
        rates_json = json.loads(data)
        rates_table = rates_json['rates']
        rates_table["PHTLR"] = 2.43
        rates_table["HTLR"] = (2.43 * 0.000000000001)
        return rates_table

    def get_rates_table(self, ignore_time=False):
        now = datetime.now()
        if ((now - self.rates_table_updated) > timedelta(hours=1)) \
           or ignore_time:
            # We need to get new data
            if "API-key" in self.config:
                self.logger.debug("Rates table has expired, fetching new data."
                                  "..")
                r = urllib.urlopen("http://openexchangerates.org/api/latest.js"
                                   "on?app_id=" + self.config["API-key"])
                d = r.read()

                self.rates_table_updated = datetime.now()
                return self.decode_rates_table(d)
            else:
                self.logger.error("API-key not found in config file!")
                return self.rates_table
        else:
            # The old data is still usable
            self.logger.trace("Rates table is still valid, not fetching.")
            return self.rates_table

    def money_command_called(self, protocol, caller, source, command, raw_args,
                             parsed_args):
        args = raw_args.split()  # Quick fix for new command handler signature
        # This is called when a user types .money in chat
        if len(args) < 2:
            # at least 2 arguments are needed, if the user has
            # entered one or none:
            caller.respond(
                "Usage: {CHARS}money <value> <start currency> [<end currency 1"
                "> <end currency 2>...] i.e: money 15 GBP USD")
        else:  # 2 args or more:
            self.rates_table = self.get_rates_table()
            # update the rates table if we need to.

            start_val = args[0]  # the amount of money to convert from
            start_currency = args[1]  # the currency that the above refers to
            start_currency = start_currency.upper()  # uppercase dat

            if start_currency not in self.rates_table:
                caller.respond("Unknown currency: %s" % start_currency)
                return

            end_currencies = None  # list of currencies to convert to
            if len(args) == 2:  # create the list of end currencies.
                if "default-currs" in self.config:
                    end_currencies = self.config["default-currs"]
                    # get the default if none specified
                else:
                    self.logger.error("default-currs not found in config "
                                      "file!")
            else:
                end_currencies = args[2:]  # get what the user specified
            done = []
            for i in end_currencies:  # convert each currency in turn
                i = i.upper()
                if start_currency != i:
                    # exclude the start currency from the
                    # end currencies because it's redundant.
                    if i not in self.rates_table:
                        caller.respond("Unknown currency: %s" % i.upper())
                        return
                    rate = self.rates_table[i] / \
                        self.rates_table[start_currency]  # calculate the
                    # conversion rate

                    r = mpmath.mpf(start_val) * rate
                    formatted = format(float(r), "0.%sf" % self.precision)

                    done.append("%s %s" % (formatted, i))
            output = "%s %s = %s" % (start_val, start_currency,
                                     self.config["curr-separator"].join(done))
            source.respond(output)
