# coding=utf-8
__author__ = "Gareth Coles"

from system.command_manager import CommandManager
from system.event_manager import EventManager
from system.events.general import PreMessageReceived
from system.plugin import PluginObject
from system.protocols.generic.channel import Channel
from utils.data import SqliteData


class MemosPlugin(PluginObject):

    commands = None
    events = None

    data = None  # SQLite for a change

    def setup(self):
        self.commands = CommandManager.instance()
        self.events = EventManager.instance()
        self.data = SqliteData("plugins/memos/memos.sqlite")

        with self.data as c:
            # Multiline strings because of an IDE bug
            c.execute("""CREATE TABLE IF NOT EXISTS memos
                      (to TEXT, from TEXT, memo TEXT)""")

        self.events.add_callback("PreMessageReceived", self,
                                 self.message_received, 0)
        self.commands.register_command("memo", self.memo_command, self,
                                       "memo.send")

    def save_memo(self, sender, recipient, memo):
        recipient = recipient.lower()
        with self.data as c:
            c.execute("""INSERT INTO memos VALUES (?, ?, ?)""",
                      (recipient, sender, memo))

    def get_memos(self, recipient):
        recipient = recipient.lower()
        with self.data as c:
            c.execute("""SELECT * FROM memos WHERE from=?""", (recipient,))
            d = c.fetchall()
            return d

    def message_received(self, event=PreMessageReceived):
        user = event.source
        target = event.target if isinstance(event.target, Channel) else user
        memos = self.get_memos(user.name)
        if memos:
            for memo in memos:
                sender = memo[1]
                text = memo[2]
                target.respond("Memo for %s (from %s): %s" % (user.name,
                                                              sender, text))

    def memo_command(self, protocol, caller, source, command, raw_args,
                     parsed_args):
        args = raw_args.split()  # Quick fix for new command handler signature
        raise NotImplementedError("This isn't done yet.")
        # target = None  # TODO: parsing
        # memo = None  # TODO: parsing
        #
        # if len(args) < 2:
        #     caller.respond("Usage: {CHARS}memo TODO")
        # else:
        #     self.save_memo(caller.nickname, target, memo)
        #     source.respond("Alright, I'll keep that for %s." % target)
