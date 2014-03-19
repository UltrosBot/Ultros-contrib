# coding=utf-8
__author__ = "Gareth Coles"

import random

from system.command_manager import CommandManager
from system.plugin import PluginObject
from utils.config import YamlConfig
from utils.data import JSONData, SqliteData


class ItemsPlugin(PluginObject):

    commands = None

    config = None
    data = None  # SQLite for a change

    storage_type = "sqlite"

    def setup(self):
        self.commands = CommandManager()

        self.logger.debug("Entered setup method.")
        try:
            self.config = YamlConfig("plugins/items.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            self.logger.warn("Defaulting to SQLite for storage.")
        else:
            if not self.config.exists:
                self.logger.warn("Unable to find config/plugins/items.yml")
                self.logger.warn("Defaulting to SQLite for storage.")
            else:
                if self.config["storage"].lower() == "json":
                    self.storage_type = "json"

        if self.storage_type == "sqlite":
            self.data = SqliteData("plugins/items/items.sqlite")

            with self.data as c:
                # Multiline strings because of an IDE bug
                c.execute("""CREATE TABLE IF NOT EXISTS items
                          (item TEXT, owner TEXT)""")
        else:
            self.data = JSONData("plugins/items/items.json")

            if not "items" in self.data:
                self.data["items"] = []

        self.commands.register_command("give", self.give_command, self,
                                       "items.give")
        self.commands.register_command("get", self.get_command, self,
                                       "items.get")

    def number_of_items(self):
        if self.storage_type == "sqlite":
            with self.data as c:
                c.execute("""SELECT COUNT(*) FROM items""")
                d = c.fetchone()
                return d[0]
        else:
            return len(self.data["items"])

    def add_item(self, item, owner):
        item = item.lower()
        if self.storage_type == "sqlite":
            if not self.has_item(item):
                with self.data as c:
                    c.execute("""INSERT INTO items VALUES (?, ?)""", (item,
                                                                      owner))
        else:
            with self.data:
                self.data["items"].append([item, owner])

    def remove_item(self, item):
        item = item.lower()
        if self.storage_type == "sqlite":
            if self.has_item(item):
                with self.data as c:
                    c.execute("""DELETE FROM items WHERE item=?""", (item,))
        else:
            with self.data:
                items = self.data["items"]
                for item_ in items:
                    if item == item_[0]:
                        self.data["items"].remove(item_)

    def retrieve_random_item(self):
        if self.storage_type == "sqlite":
            with self.data as c:
                c.execute("""SELECT * FROM items ORDER BY RANDOM() LIMIT 1""")
                d = c.fetchone()
                return d
        else:
            return random.choice(self.data["items"])

    def has_item(self, item):
        item = item.lower()
        if self.storage_type == "sqlite":
            with self.data as c:
                c.execute("""SELECT item FROM items WHERE item=?""", (item,))
                d = c.fetchone()
                return bool(d)
        else:
            for item_ in self.data["items"]:
                if item == item_[0]:
                    return True
            return False

    def give_command(self, protocol, caller, source, command, raw_args,
                     parsed_args):
        args = raw_args.split()  # Quick fix for new command handler signature
        if len(args) == 0:
            caller.respond("Usage: {CHARS}give <item>")
        item = " ".join(args)
        if not self.has_item(item):
            self.add_item(item, caller.nickname)
            protocol.send_action(source, "takes the '%s' and puts it in her "
                                         "bag" % item)
        else:
            protocol.send_action(source, "ignores the '%s' as the one she has "
                                         "is better." % item)

    def get_command(self, protocol, caller, source, command, raw_args,
                    parsed_args):
        args = raw_args.split()  # Quick fix for new command handler signature
        if self.number_of_items() > 0:
            item = self.retrieve_random_item()
            item_name = item[0]
            item_owner = item[1]
            self.remove_item(item_name)
            protocol.send_action(source, "retrieves %s%s '%s' and hands it to "
                                         "%s" % (item_owner,
                                                 "'" if item_owner[-1] == "s"
                                                 else "'s",
                                                 item_name, caller.nickname))
        else:
            protocol.send_action(source, "doesn't have any items right now.")
