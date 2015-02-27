DrunkOctopus
===========

This plugin gives your squidopus shots of vodka and rum.

## Configuration

* `drunkenness` - How drunk the bot should be.
* `cooldown` - Sobering up options.
    * `enabled` - Whether or not the bot should sober up over time.
    * `amount` - Amount to sober up by.
    * `time` - Time in seconds between each sobering step.
* `drinks` - A dict of drinks the bot can have, and how much more drunk each drink will make it.

## Commands and permissions

* `drink <type of drink>`
    * Description: Give the bot a drink.
    * Permissions: `drunkoctopus.drink`
* `drunkenness [new level]`
    * Description: Get/set the bot's drunkenness level.
    * Permissions: `drunkoctopus.drunkenness`

## Attribution

* Sean Gordon
