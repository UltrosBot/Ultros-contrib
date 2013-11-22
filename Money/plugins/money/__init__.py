import urllib

__author__ = 'Jim'


import json

from system.plugin import PluginObject
from system import command_manager
from utils.config import Config
from datetime import datetime, timedelta
#from japan import loli_maids


class MoneyPlugin(PluginObject):
    def decode_rates_table(self, data):
        rates_json = json.loads(data)
        rates_table = rates_json['rates']
        return rates_table

    def get_rates_table(self):
        now = datetime.now()
        if (now - self.rates_table_updated) > timedelta(hours=1):
            # We need to get new data
            if "API-key" in self.config:
                self.logger.debug("Rates table has expired, fetching new data."
                                  "..")
                r = urllib.urlopen("http://openexchangerates.org/api/latest.js"
                                   "on?app_id=" + self.config["API-key"])
                d = r.read()

                self.rates_table_updated = datetime.now()
                return d
            else:
                self.logger.error("API-key not found in config file!")
                return self.rates_table
        else:
            # The old data is still usable
            self.logger.debug("Rates table is still valid, not fetching.")
            return self.rates_table

    def setup(self):
        self.rates_table = self.decode_rates_table(self.get_rates_table())
        self.rates_table_updated = datetime.now()

        self.config = Config("plugins/money.yml")

        self.command = command_manager.CommandManager.instance()
        self.command.register_command("money", self.money_command_called,
                                      self, "money.main")

    def money_command_called(self, caller, source, args, protocol):
        # This is called when a user types .money in chat
        if len(args) < 2:  # at least 2 arguments are needed, if the user has
        # entered one or none:
            caller.respond(
                "Usage: {CHARS}money <value> <start currency> [<end currency 1"
                "> <end currency 2>...] i.e: money 15 GBP USD")
        else:  # 2 args or more:
            self.rates_table = self.decode_rates_table(self.get_rates_table())
              # update the rates table if we need to.

            start_val = args[0]  # the amount of money to convert from
            start_currency = args[1]  # the currency that the above refers to
            start_currency = start_currency.upper()  # uppercase dat

            end_currencies = None  # list of currencies to convert to
            if len(args) == 2:  # create the list of end currencies.
                if "default-currs" in self.config:
                    end_currencies = self.config["default-currs"]
                    # get the default if none specified
                else:
                    self.logger.error("key default-currs not found in config f"
                                      "ile!")
            else:
                end_currencies = args[2:]  # get what the user specified
            output = start_val + " " + start_currency + " = "
            # output starts : "999 XXX = "
            self.logger.debug("end_currencies "
                              "= {0}".format(str(end_currencies)))
            for i in end_currencies:  # convert each currency in turn
                self.logger.debug("i = " + i)
                if start_currency != i:  # exclude the start currency from the
                # end currencies because it's redundant.
                    rate = self.rates_table[i] / \
                        self.rates_table[start_currency]  # calculate the
                        # conversion rate
                    output += "{0:.2f} ".format(float(start_val) * rate) + i
                    # print the value
                    output += self.config["curr-separator"]  # print separator
            source.respond(output)  # Send the response to the user
