Lua
===

*Note:* This guide is a work in progress.

Interpreter
-----------

We use [lupa](https://github.com/scoder/lupa) to provide Lua functionality. Depending on how you installed it, and
what you have installed, you may be using LuaJIT, Lua 5.2, or Lua 5.1 (in that order of search preference). We highly
recommend using LuaJIT, but for maximum comparability, it's a good idea to target 5.1 as a minimum version for any
plugins you release publicly.

Since this is a Python bot, there are a few change/extensions to the Lua runtime:

    * `import()` - Utility function to load Python modules and get access to them.
    * `print()` - Works pretty much as normal, but is passed through to your plugin's logger (info level).
    * `python` - A lupa-provided table containing some useful Python functions and attributes. You may need this to
                 interact with some Python data types. Some notable ones are below, but check the
                 [lupa](https://github.com/scoder/lupa) page for full details.
        * `builtins` - Python's builtin module.
        * `none` - Python's `None` value. In most cases, nil will be converted automatically, but sometimes you may
                   need to use `None` itself (e.g. key to a dict).
        * `enumerate()` - Iterate over a Python value similar to `ipairs()` in Lua.
        * `eval()` - Run a Python expression and get the result.
        * `iter()` - Iterate over a Python value similar to `for _, v in pairs()` in _Lua.
        * `iterex()` - Iterate over a Python value similar to `for k, v in pairs()` in _Lua.


Plugin Structure
----------------

The plugin loader will attempt to load your plugin from `init.lua` or `__init__.lua`. The first argument will be
a base plugin table with a few pre-defined functions and attributes to make your life easier. You don't have to
use this, but we strongly suggest you do. Your module should return a table which will be used as the plugin object.
If nothing is returned, the base plugin table will be used, but we recommend you always return it anyway.

Lua plugins work similarly to Python plugins, but here's a quick rundown on the standard functions/attributes:

    * `setup()` - Called after your plugin has been loaded. This is where you should open your config file,
                  register commands and event handlers, etc.
    * `reload()` - Called when your plugin is reloaded. This is where you should reinitialise any internal state your
                   plugin has. You may want to call this from your `setup` method to avoid duplicating code.
    * `deactivate()` - Called when your plugin is disabled. This is where you should tidy up any temporary resources
                       your plugin uses, close any external connections it has made, etc.
    * `events` - The event manager. Use this to register event handlers.
    * `commands` - The command manager. Use this to register commands.
    * `storage` - The storage manager. Use this to load config/data files.
    * `logger` - The logger. Use this to log messages to console, etc.


Classes
-------

Please note that plugins use closure-based classes rather than colon-style ones as they mesh nicer with Python.
This means that all methods are defined and called like:

```
function obj.func()
    obj.dostuff()
end

obj.func()
```

rather than:

```
function obj.func(self)
    self:dostuff()
end

obj:func()
```

This allows Lua and Python functions to be used the same with, without requiring different syntax for each type.
You are free to use colon syntax for classes other than the main plugin, but we suggest using closure-style classes
for everything to keep it consistent, unless you have good reason not to.
