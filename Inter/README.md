Inter
=====

Inter is a basic plugin and protocol (sans commands, for now) for working with
Inter, which can be found here: https://github.com/gdude2002/Inter/

Inter is a cross-communications server designed for use with the popular game
Minecraft. Please see the above link for more information on it.

Protocol
========

The configuration example is in **config/protocols/inter.yml.example** and should be
fairly self-explanitory. Please note that being connected via multiple Inter
protocols is not fully supported, but we've done our best with it.

The only odd configuration item is `nickname` - this should be set to what you
want messages from the bot itself to show up as being sent from. For example, if
you set it to `Ultros`, then messages sent by the bot itself will appear to come
from a fake user named `Ultros`.

Plugin
======

The plugin provides some basic bridging. It's as uncomplicated as the Inter
protocol itself, which wasn't built to deal with this kind of thing, so some 
users may find it a little basic, but it serves most purposes nicely. It also
adds one command..

* `players` - List players on all connected Inter servers.
    * Permission: `inter.players`

The configuration example is in **conf/plugins/inter.yml.example**, and contains
examples both for protocols without colours, and an example with IRC colours. 
Remember to read the file and fill it out accordingly!