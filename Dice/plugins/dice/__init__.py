# coding=utf-8

import random
import re

from system.plugins.plugin import PluginObject
from system.storage.formats import YAML

__all__ = [
    "DiceError", "DiceFormatError", "DicePlugin", "NotEnoughDice",
    "NotEnoughSides"
]


class DiceError(Exception):
    pass


class DiceFormatError(DiceError):
    """
    I don't speak that language.
    """


class NotEnoughDice(DiceError):
    """
    I don't have enough dice. T_T
    """


class NotEnoughSides(DiceError):
    """
    What are you trying to roll, a ball?
    """


class DicePlugin(PluginObject):

    _MODS_REGEX = re.compile(
        r"(?P<sort>s)|(?P<total>t)|(?:\^(?P<high>\d+))|(?:v(?P<low>\d+))"
    )
    _ROLL_REGEX = re.compile(
        r"^(?P<dice>\d+)?(?:d(?P<sides>\d+))?(?P<mods>(?:t|s|\^\d+|v\d+)*)?$"
    )

    _config = None

    def setup(self):
        # Initial config load
        try:
            self._config = self.storage.get_file(
                self, "config", YAML, "plugins/dice.yml"
            )
        except Exception:
            self.logger.exception("Error loading configuration!")
            self.logger.error("Disabling...")
            self._disable_self()
            return
        if not self._config.exists:
            self.logger.error("Unable to find config/plugins/dice.yml")
            self.logger.error("Disabling...")
            self._disable_self()
            return

        # Register commands
        self.commands.register_command(
            "roll", self.roll_cmd, self, "dice.roll", aliases=["dice"],
            default=True
        )

    @property
    def max_dice(self):
        return self._config["max_dice"]

    @property
    def max_sides(self):
        return self._config["max_sides"]

    @property
    def default_dice(self):
        return self._config["default_dice"]

    @property
    def default_sides(self):
        return self._config["default_sides"]

    def _respond(self, target, msg):
        target.respond("[Dice] %s" % msg)

    def roll_cmd(self, protocol, caller, source, command, raw_args,
                 parsed_args):
        try:
            result = self.roll(raw_args)
            self._respond(source, str(result))
        except DiceFormatError:
            self._respond(caller, "Usage: {CHARS}%s [roll info]" % command)
        except NotEnoughDice:
            self._respond(
                caller, "Too many dice. My dice cup is only so big..."
            )
        except NotEnoughSides:
            self._respond(
                caller, "Too many sides. What are you trying to roll, "
                        "a ball?"
            )

    def roll(self, description=""):
        match = self._ROLL_REGEX.match(description.strip())
        if match is None:
            raise DiceFormatError("Invalid dice roll expression")

        parts = match.groupdict()
        dice = int(parts["dice"] or self.default_dice)
        sides = int(parts["sides"] or self.default_sides)
        mods = parts["mods"] or ""

        if dice > self.max_dice:
            raise NotEnoughDice()
        if sides > self.max_sides:
            raise NotEnoughSides()

        # Roll
        result = [random.randint(1, sides) for _ in xrange(dice)]
        return self.apply_mods(result, mods)

    def apply_mods(self, numbers, mods):
        pos = 0
        while True:
            match = self._MODS_REGEX.match(mods, pos=pos)
            if match is None:
                break
            if match.lastgroup == "sort":
                numbers.sort()
                pos += 1
            elif match.lastgroup == "total":
                numbers = [sum(numbers)]
                pos += 1
            elif match.lastgroup == "high":
                count = match.group("high")
                numbers.sort()
                numbers = numbers[-int(count):]
                pos += len(count) + 1
            elif match.lastgroup == "low":
                count = match.group("low")
                numbers.sort()
                numbers = numbers[:int(count)]
                pos += len(count) + 1
        return numbers
