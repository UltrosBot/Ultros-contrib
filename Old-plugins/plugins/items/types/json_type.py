# coding=utf-8

__author__ = 'Gareth Coles'

import random

from system.storage.formats import JSON


class Type(object):

    def __init__(self, plugin, storage, logger):
        self.plugin = plugin
        self.storage = storage
        self.logger = logger

        self.data = self.storage.get_file(self, "data", JSON,
                                          "plugins/items/items.json")

        if "items" not in self.data:
            self.data["items"] = []

    def number_of_items(self):
        return len(self.data["items"])

    def fuzzy_number_of_items(self):
        num = len(self.data["items"])
        if num < 3:
            return num + random.randint(1, num + 3)
        else:
            return num + random.randint(-2, 2)

    def add_item(self, item, owner):
        item = item.lower()
        with self.data:
            self.data["items"].append([item, owner])

    def remove_item(self, item):
        item = item.lower()
        with self.data:
            items = self.data["items"]
            for item_ in items:
                if item == item_[0]:
                    self.data["items"].remove(item_)

    def retrieve_random_item(self):
        return random.choice(self.data["items"])

    def has_item(self, item):
        item = item.lower()
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

    def count_command(self, protocol, caller, source, command, raw_args,
                      parsed_args):
        fuzzy = self.fuzzy_number_of_items()

        if fuzzy < 2:
            protocol.send_action(
                source, "has around %s item in her bag." % fuzzy
            )
        else:
            protocol.send_action(
                source, "has around %s items in her bag." % fuzzy
            )
