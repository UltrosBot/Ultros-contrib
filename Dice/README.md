Dice
===========

This plugin provides a dice roll command.

## Configuration

* `max_dice` - Maximum number of dice per roll.
* `max_sides` - Maximum number of sides per dice.
* `default_dice` - Number of default dice.
* `default_sides` - Number of sides on the default dice.

## Commands and permissions

* `roll [description]`
    * Description: Roll the dice. Optional parameter can be used to change roll information. See "Roll syntax" section for details.
    * Aliases: `dice`
    * Permissions: `dice.roll`

## Roll syntax

The basic roll syntax is `[number of dice][d<number of sides>]`. For example, `6d20` will roll 6 20-sided dice.
Each part is optional: `6` will roll 6 dice of default sides, and `d20` will roll a 20-sided dice the default number of times.
Defaults are set in the config.

Modifiers may be appended to the end of a roll:

* `t` - Returns the total sum of the dice, rather than each value.
* `s` - Returns the values sorted from lowest to highest.
* `^n` - Returns the highest `n` dice only.
* `vn` - Returns the lowest `n` dice only.

## Attribution

* Sean Gordon
