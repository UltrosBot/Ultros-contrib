Wordnik
========================

Wordnik is a site and API used primarily for dictionary lookups for English words.
This plugin exposes that API for people that may want to use your bot.

Before you start, you'll need to get yourself a Wordnik API key. To do this, please do the following..

* Create an account on the [Wordnik site](http://wordnik.com) and verify your email.
* Copy the following text: ```Ultros - This key will be used with the Wordnik plugin for the Ultros multi-protocol bot, used to provide definitions to users on IRC and other chat networks.```
* Go to [This page](http://developer.wordnik.com) and paste the above text into the `How might you use the API?` box.
  * `esperluette` on [#Wordnik@Freenode](irc://irc.freenode.net/wordnik) has requested we copy and paste the same thing into the box, so please honor that request.
  * This step is important; while the API is currently automatically approved, this box is used to collect usage statistics.
    * However, Wordnik **may** decide to use this box for decisions relating to API acceptance later on.
* Type the username you created in step one into the `Your wordnik.com Username` box.
* Wait for your email containing the API key and copy it into the configuration file.

Remember, the API is provided courtesy of Wordnik. The definitions belong to Wiktionary. Be nice!

## Usage

This package supplies the following commands..
* `dict <word>` - Do a dictionary lookup
  * `<word>` represents the word to be looked up.
  * This command requires the `wordnik.dict` permission.
* `wotd` - Do a dictionary lookup on the current word of the day
  * This command requires the `wordnik.wotd` permission.
* The commands will be output to the current channel - or in a private message, if used in one.