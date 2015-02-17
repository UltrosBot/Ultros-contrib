import random
import re
import string
from twisted.internet import reactor
from system.event_manager import EventManager
from system.command_manager import CommandManager

import system.plugin as plugin

from system.storage.formats import YAML
from system.storage.manager import StorageManager

__author__ = 'Sean'


class DrunkPlugin(plugin.PluginObject):

    commands = None
    config = None
    storage = None

    def setup(self):
        ### Grab important shit
        self.commands = CommandManager()
        self.events = EventManager()
        self.storage = StorageManager()

        ### Initial config load
        try:
            self.config = self.storage.get_file(self, "config", YAML,
                                                "plugins/drunkoctopus.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            self.logger.error("Disabling...")
            self._disable_self()
            return
        if not self.config.exists:
            self.logger.error("Unable to find config/plugins/drunkoctopus.yml")
            self.logger.error("Disabling...")
            self._disable_self()
            return

        ### Create vars and stuff
        self._sobering_call = None
        self._drunktalk = DrunkTalk()

        ### Load options from config
        self._load()

        self.config.add_callback(self._load)

        ### Register events and commands

        self.events.add_callback("MessageSent",
                                 self,
                                 self.outgoing_message_handler,
                                 1)
        self.commands.register_command("drunkenness",
                                       self.drunkenness_command,
                                       self,
                                       "drunkoctopus.drunkenness",
                                       default=True)
        self.commands.register_command("drink",
                                       self.drink_command,
                                       self,
                                       "drunkoctopus.drink")

    def reload(self):
        try:
            self.config.reload()
        except Exception:
            self.logger.exception("Error reloading configuration!")
            return False
        return True

    def _load(self):
        self._drunktalk.drunkenness = self.config["drunkenness"]
        self._cooldown_enabled = self.config["cooldown"]["enabled"]
        self._cooldown_time = self.config["cooldown"]["time"]
        self._cooldown_amount = self.config["cooldown"]["amount"]
        self._drinks = self.config["drinks"]

        # Sort out the sobering deferred as necessary
        if self._cooldown_enabled:
            if self._sobering_call is None:
                self.logger.trace("Starting sobering call due to config "
                                  "change")
                self._sobering_call = reactor.callLater(self._cooldown_time,
                                                        self._sober_up)
        else:
            if self._sobering_call is not None:
                self.logger.trace("Cancelling sobering call due to config "
                                  "change")
                self._sobering_call.cancel()

    def _sober_up(self):
        self.logger.trace("Sobering up")
        drunk = self._drunktalk.drunkenness
        drunk -= self._cooldown_amount
        if drunk < 0:
            drunk = 0
        self._drunktalk.drunkenness = drunk
        if self._cooldown_enabled:
            reactor.callLater(self._cooldown_time, self._sober_up)

    def drunkenness_command(self, protocol, caller, source, command, raw_args,
                            parsed_args):
        args = raw_args.split()  # Quick fix for new command handler signature
        if len(args) == 0:
            caller.respond("Drunkenness level: %s" %
                           self._drunktalk.drunkenness)
            return
        elif len(args) == 1:
            try:
                new_drunk = int(args[0])
                self._drunktalk.drunkenness = new_drunk
                caller.respond("New drunkenness level: %s" %
                               self._drunktalk.drunkenness)
                return
            except:
                caller.respond("Invalid drunkenness level (use without "
                               "arguments for usage)")
        else:
            caller.respond("Usage: {CHARS}drunkenness [percent level]")

    def drink_command(self, protocol, caller, source, command, raw_args,
                      parsed_args):
        args = raw_args.split()  # Quick fix for new command handler signature
        if len(args) == 0:
            caller.respond("Usage: {CHARS}drink <type of drink>")
            return
        drink = " ".join(args)
        drinkl = drink.lower()
        if drinkl in self._drinks:
            protocol.send_action(source, "drinks {}".format(drink))
            self._drunktalk.drunkenness += self._drinks[drinkl]
        else:
            caller.respond("I don't have any of that.")

    def outgoing_message_handler(self, event):
        """
        :type event: MessageSent
        """
        self.logger.trace("RECEIVED %s EVENT: %s" % (event.type,
                                                     event.message))
        event.message = self._drunktalk.drunk_typing(event.message)


class DrunkTalk(object):

    # A dict of lowercase to uppercase keys
    _shifted_chars = {
        ",": "<",
        ".": ">",
        "/": "?",
        "\\": "|",
        "-": "_",
        "=": "+",
        "`": "~",
        "[": "{",
        "]": "}",
        ";": ":",
        "'": '"',
        "#": "~",
        "1": "!",
        "2": "@",
        "3": "#",
        "4": "$",
        "5": "%",
        "6": "^",
        "7": "&",
        "8": "*",
        "9": "(",
        "0": ")"
    }

    for c in string.ascii_lowercase:
        _shifted_chars[c] = c.upper()

    _unshifted_chars = {}
    for k, v in _shifted_chars.iteritems():
        _unshifted_chars[v] = k

    # Dict of nearby punctuation (same keyboard line, neightbouring keys)
    _nearby_punct = {
        ",": ["."],
        ".": [",", "/"],
        "/": ["."],
        ";": ["'"],
        "'": [";"],
        "[": ["]"],
        "]": ["[", "\\"]
    }

    _add = {
        "~": ["!"],
        "!": ["~", "@"],
        "@": ["!", "#"],
        "#": ['"', "$"],
        "$": ["#", "%"],
        "%": ["$", "^"],
        "^": ["%", "&"],
        "&": ["^", "*"],
        "*": ["&", "("],
        "(": ["*", ")"],
        ")": ["(", "_"],
        "_": [")", "+"],
        "+": ["="]
    }
    for k, v in _nearby_punct.iteritems():
        _v = [_shifted_chars[c] for c in v]
        _add[_shifted_chars[k]] = _v

    _nearby_punct.update(_add)
    del _add

    def __init__(self, drunkenness=100):
        self.drunkenness = drunkenness
        # Not making these constants in case I want to make them configurable
        # _c = chance, _s = spacing (min spacing between changes)
        self._c_space_mixup = 8
        self._c_letter_mixup = 10
        self._c_shift_mixup = 10
        self._c_punct_remove = 30
        self._c_punct_double = 5
        self._c_punct_similar = 8
        self._s_letter_mixup = 5

    @property
    def drunkenness(self):
        return self._drunkenness

    @drunkenness.setter
    def drunkenness(self, value):
        self._drunkenness = value
        self._multiplier = value / 100

    def drunk_typing(self, msg):
        drunk = self._drunkenness
        while drunk > 100:
            msg = self._drunk_typing(msg)
            drunk -= 100
        return self._drunk_typing(msg)

    def _drunk_typing(self, msg):
        msg = self._mixup_spaces(msg)
        msg = self._mixup_letters(msg)
        msg = self._mixup_shift(msg)
        msg = self._remove_punctuation(msg)
        msg = self._double_punctuation(msg)
        msg = self._nearby_punctuation(msg)
        return msg

    def _roll(self, chance):
        return random.randint(0, 99) < (chance * self._multiplier)

    def _mixup_spaces(self, msg):
        msgl = list(msg)
        pos = msg.find(" ")
        while pos != -1:
            if self._roll(self._c_space_mixup):
                direction = 1
                if pos == 0:
                    direction = 1
                elif pos == len(msgl) - 1:
                    direction = -1
                else:
                    direction = random.choice([-1, 1])
                pos2 = pos + direction
                msgl[pos], msgl[pos2] = msgl[pos2], msgl[pos]
            pos = msg.find(" ", pos + 1)
        return ''.join(msgl)

    def _mixup_letters(self, msg):
        msgl = list(msg)
        match = re.search(r"\w\w", msg)
        start = 0
        while match is not None:
            pos = match.start() + start
            if self._roll(self._c_letter_mixup):
                pos2 = pos + 1
                msgl[pos], msgl[pos2] = msgl[pos2], msgl[pos]
                start = pos + 1
                # re.search doesn't accept a start position, so feed it a
                # substring
            start = pos + self._s_letter_mixup
            msgsub = msg[start:]
            match = re.search(r"\w\w", msgsub)
        return ''.join(msgl)

    def _mixup_shift(self, msg):
        msgl = list(msg)
        # For this, we need to find a place where a shift key was pressed or
        # released, and press/release it one character earlier or later
        shift = msgl[0] in self._unshifted_chars
        just_altered = False
        for x in xrange(1, len(msgl)):
            new_shift = msgl[x] in self._unshifted_chars
            if just_altered:
                shift = new_shift
                just_altered = False
                continue
            if new_shift != shift:
                if self._roll(self._c_shift_mixup):
                    # Function to check if it's possible to shift-swap a
                    # position
                    suitable = lambda p, s: msgl[p] in (
                        self._unshifted_chars if s else self._shifted_chars)

                    # Change current character (shift late)
                    pos = x
                    shifted = new_shift
                    if random.choice([True, False]) or not suitable(pos,
                                                                    shifted):
                        # Actually, change previous character (shift early)
                        pos = x - 1
                        shifted = shift
                        if not suitable(pos, shifted):
                            shift = new_shift
                            continue

                    if shifted:
                        msgl[pos] = self._unshifted_chars[msgl[pos]]
                    else:
                        msgl[pos] = self._shifted_chars[msgl[pos]]
                    just_altered = True
            shift = new_shift
        return ''.join(msgl)

    def _remove_punctuation(self, msg):
        msgl = list(msg)
        removed = 0
        for n, c in enumerate(msg):
            if c in string.punctuation and self._roll(self._c_punct_remove):
                del msgl[n - removed]
                removed += 1
        return ''.join(msgl)

    def _double_punctuation(self, msg):
        msgl = list(msg)
        added = 0
        for n, c in enumerate(msg):
            if c in string.punctuation and self._roll(self._c_punct_double):
                msgl.insert(n + added, c)
                added += 1
        return ''.join(msgl)

    def _nearby_punctuation(self, msg):
        msgl = list(msg)
        for n, c in enumerate(msgl):
            if c in self._nearby_punct and self._roll(self._c_punct_similar):
                msgl[n] = random.choice(self._nearby_punct[c])
        return ''.join(msgl)
