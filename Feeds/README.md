Feeds
===========

This plugin allows you to configure RSS, ATOM and other feeds to be relayed to channels, or users.

## Configuration

* `feeds` - A list of feeds to parse
  * `name` - Friendly name for your feed
  * `url` - URL to your feed. This can also be a file path.
  * `frequency` - How often (in seconds) to check for updates to the feed
  * `instantly-relay` - Whether to relay immediately when the feed is first parsed. Turn this off to ignore the first parse and just use it to grab a published date.
  * `targets` - A list of targets to relay your feed to
    * `name` - Friendly name of your target, as defined in the `targets` section below.
    * `format` - Format of messages to send on update. You can use the following tokens in your string: `{NAME}`, `{TITLE}`, `{URL}`
* `targets` - Configuration of different targets to relay to
  * `target-name` - Friendly name of your target. This should be the name of the section.
    * `protocol` - Name of the protocol to relay to
    * `target` - Name of the target to relay to
    * `target-type` - Type of target to relay to. This is usually either `user` or `channel`.

## Commands and permissions

* There are no commands or permissions.