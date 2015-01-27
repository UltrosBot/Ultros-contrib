PlugDJ
======

A protocol that uses Selenium to interface with the Plug.DJ site and API.

This package isn't finished yet - this documentation will be filled out when
it is.

## TODO list

* Rate-limiting
* Checking for failed logins, etc
* Re-check API methods and returns
    * Ensure that all data is available to plugins
    * Ensure that all output is accurate

## Weirdness

The Plug.DJ API is pretty weird, and somewhat unmaintained. As a result, you'll
see some weirdness in the protocol we've written. Some of the things we've noticed
include:

* Duplicate score messages when someone changes between a woot and a meh
* Duplicate woot message when someone grabs a song after manually wooting it
* Generally missing some information and falling back to sane defaults
    * This happens, for example, when a message in the chat knows who did something
      but that information isn't available in the API.
