# coding=utf-8

__author__ = 'Gareth Coles'

import random

from system.storage.formats import DBAPI


class Type(object):

    def __init__(self, plugin, storage, logger):
        self.plugin = plugin
        self.storage = storage
        self.logger = logger

        self.data = self.storage.get_file(
            self.plugin,
            "data",
            DBAPI,
            "sqlite3:data/plugins/items/items.sqlite",
            "data/plugins/items/items.sqlite",
            check_same_thread=False
        )

        self.data.runQuery("CREATE TABLE IF NOT EXISTS items"
                           "(item TEXT, owner TEXT)")

    def _give_txn(self, txn, item, owner):
        txn.execute("SELECT item FROM items WHERE item=?", (item,))
        r = txn.fetchone()

        if r is not None:
            return True

        txn.execute("INSERT INTO items VALUES (?, ?)", (item, owner))
        return False

    def _give_callback(self, result, item, source, protocol):
        if result:
            protocol.send_action(source, "ignores the '%s' as the one she "
                                         "has is better." % item)
        else:
            protocol.send_action(source, "takes the %s and puts it in her "
                                         "bag." % item)

    def _give_callback_fail(self, failure, item, source, protocol):
        protocol.send_action(source, "attempts to take the '%s' but is "
                                     "startled by a loud voice: \"%s\""
                                     % (item, failure.getErrorMessage()))

    def give_command(self, protocol, caller, source, command, raw_args,
                     parsed_args):
        args = raw_args.split()  # Quick fix for new command handler signature
        if len(args) == 0:
            caller.respond("Usage: {CHARS}give <item>")
        item = " ".join(args).lower()

        d = self.data.runInteraction(self._give_txn, item, caller.nickname)

        d.addCallbacks(self._give_callback, self._give_callback_fail,
                       callbackArgs=(item, source, protocol),
                       errbackArgs=(item, source, protocol))

    def _get_txn(self, txn):
        txn.execute("SELECT COUNT(*) FROM items")
        r = txn.fetchone()

        if r[0] < 1:
            return False

        txn.execute("SELECT * FROM items ORDER BY RANDOM() LIMIT 1")
        r = txn.fetchone()

        txn.execute("DELETE FROM items WHERE item=?", (r[0],))

        return r

    def _get_callback(self, result, caller, source, protocol):
        if not result:
            protocol.send_action(source, "doesn't have any items right now.")
        else:
            _name = result[0]
            _owner = result[1]

            protocol.send_action(
                source,
                "retrieves %s%s '%s' and hands it to %s"
                % (
                    _owner,
                    "'" if _owner[-1] == "s" else "'s",
                    _name,
                    caller.nickname
                )
            )

    def _get_callback_fail(self, failure, source, protocol):
        protocol.send_action(source, "attempts to retrieve an item from her "
                                     "bag but is startled by a loud voice: "
                                     "\"%s\"" % failure.getErrorMessage())

    def get_command(self, protocol, caller, source, command, raw_args,
                    parsed_args):
        d = self.data.runInteraction(self._get_txn)

        d.addCallbacks(self._get_callback, self._get_callback_fail,
                       callbackArgs=(caller, source, protocol),
                       errbackArgs=(source, protocol))

    def _count_txn(self, txn):
        txn.execute("SELECT COUNT(*) FROM items")
        r = txn.fetchone()

        return r[0]

    def _count_callback(self, result, source, protocol):
        if result < 1:
            protocol.send_action(source, "doesn't have any items right now.")
        else:
            if result < 3:
                fuzzy = result + random.randint(1, result + 3)
            else:
                fuzzy = result + random.randint(-2, 2)

            if fuzzy < 2:
                protocol.send_action(
                    source, "has around %s item in her bag." % fuzzy
                )
            else:
                protocol.send_action(
                    source, "has around %s items in her bag." % fuzzy
                )

    def _count_callback_fail(self, failure, source, protocol):
        protocol.send_action(source, "attempts to count the items in her "
                                     "bag but is startled by a loud voice: "
                                     "\"%s\"" % failure.getErrorMessage())

    def count_command(self, protocol, caller, source, command, raw_args,
                      parsed_args):
        d = self.data.runInteraction(self._count_txn)

        d.addCallbacks(self._count_callback, self._count_callback_fail,
                       callbackArgs=(source, protocol),
                       errbackArgs=(source, protocol))
