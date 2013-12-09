Old plugins
===========

This package will contain most of the plugins from the old iteration of Ultros, found [here](https://github.com/UltrosBot/McBlockit---Helpbot/tree/master/plugins).

## Plugins

* Ass
  * A just-for-fun plugin. Stupid-ass bucket => stupid ass-bucket
* Brainfuck
  * A simple interpreter for the somewhat-popular Brainfuck language

## Configuration

* Ass - No configuration is needed.
* Brainfuck - You should configure how long a program can execute for (in ms).
  * This setting is in ```config/plugins/brainfuck.yml``` - The default is ```100``` (ms).

## Commands and permissions

* Ass - No commands, and no permissions.
* Brainfuck - 1 command, and 1 permission.
  * Command - ```bf```
    * Runs some Brainfuck code.
    * ```bf <code (no spaces)>```
  * Permission - ```brainfuck.exec```
    * Allows use of the bf command

## Attribution

* Sean Gordon: Ass and Brainfuck plugins
* Gareth Coles: Plugin porting
