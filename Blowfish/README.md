Blowfish
========

A lot of clients and bots have scripts/plugins for Blowfish-CDC enciphering. While I personally
don't see the merits of such a thing over (for example) OTR, clients such as mIRC and bots
such as Eggdrop have extensions that support messages of this ilk, and so we decided to add
similar support to Ultros to keep it compatible.

When enabled for a target, this plugin will decrypt incoming messages and encrypt outgoing
messages. It will ignore any messages that aren't encrypted, but they will still appear
in your logs.

## Important: Blowfish is not secure!

Blowfish is not a replacement for proper encryption or OTR. It has a large set of weak keys.
For that reason, please remember that we are providing this plugin for compatibility purposes,
not to keep your discussions of tentacle porn safe.

I repeat: **Do not use this for critical communications that need to be secure. Use a real
method of encryption instead.**

## How it works

I've prepared a simple chart below to explain how it works. If you're doing this manually, remember
to prefix your encrypted messages with `+OK `.

[![](https://www.lucidchart.com/publicSegments/view/545358e2-fb64-4bc6-9fea-5f350a00c0e0/image.png)](https://www.lucidchart.com/publicSegments/view/545358e2-fb64-4bc6-9fea-5f350a00c0e0/image.png)

## Configuration

Blowfish has a fairly simple configuration.

* `protocol_name:` - Replace this with the name of the protocol that you want to use the plugin on.
    * `global: "key"` - This is a key to use if we couldn't find a specific key below. You may omit
      this if you don't want protocol-wide ciphering. 
    * `targets:` - A list of specific targets.
        * `"#channel": "key"` - The name of a user or channel, and its ciphering key.

## Usage

Simply use this plugin with your client/bot's script. Messages should be of the form `+OK message`,
where `message` is the enciphered message.
