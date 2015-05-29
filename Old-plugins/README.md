Old plugins
===========

This package will contain most of the plugins from the old iteration of Ultros, found [here](https://github.com/UltrosBot/McBlockit---Helpbot/tree/master/plugins).

## Plugins

* Ass
  * A just-for-fun plugin. Stupid-ass bucket => stupid ass-bucket
* Brainfuck
  * A simple interpreter for the somewhat-popular Brainfuck language
* GeoIP
  * A simple (but somewhat accurate) GeoIP tool, using freegeoip.net
* Items
  * A common-enough bot feature. Give the bot some items, and get random items back later.
* Lastseen
  * Check when a user was last seen online.
* Memos - **Not implemented yet**
  * Send memos to each other, which will be delivered when the recipient is active.
* Russian-roulette
  * Click, click, BANG!

## Configuration

* Brainfuck - `config/plugins/brainfuck.yml`
  * `timeout` - How long a brainfuck program is allowed to execute for, in miliseconds. The default is `100
* Items - `config/plugins/items.yml`
  * `storage` - Which storage engine to use for items.
    * `sqlite` - This is a faster, SQL-based storage, but is hard (if not impossible) to edit by hand.
    * `json` - This is easier to edit by hand, but it's much slower and will eat more RAM than `sqlite` will.


## Commands and permissions

* Ass - No commands, and no permissions.
* Brainfuck - 1 command, and 1 permission.
  * Command - `bf` (Perm: `brainfuck.exec`)
    * Runs some Brainfuck code.
    * `bf <code (no spaces)>`
* GeoIP - 1 command, and 1 permission.
  * Command - `geoip` (Perm: `geoip.command`)
    * Looks up an address in the GeoIP database
    * `geoip <address>`
* Items - 2 commands, and 2 permissions.
  * Command - `give` (Perm: `items.give`)
    * Give an item to the bot.
    * `give <item>`
  * Command - `get` (Perm: `items.get`)
    * Receive a random item from the bot.
    * `get`
* Lastseen - 1 command, and 1 permission.
  * Command - `seen` (Perm: `seen.seen`)
    * Check when a user was last seen being active.
    * `seen <username>`
* Memos - 1 command, and 1 permission
  * Command - `memo` (Perm: `memo.send`)
    * Send a memo to a user, for them to see next time they send a message.
    * `memo <username> <message>`
* Russian-roulette - 1 command, and 1 permission.
  * Command - `rroulette` (Perm: `russianroulette.rroulette`)
    * Play some russian roulette!
    * `rroulette`

## Attribution

* Sean Gordon: Ass and Brainfuck plugins
* Gareth Coles: Plugin porting and rewriting
* Kamyla (AKA NotMeh): GeoIP plugin
