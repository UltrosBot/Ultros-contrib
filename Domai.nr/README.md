Domai.nr
===========

This plugin allows integration with the Domainr API.

## Commands and permissions

* `domainrsearch <query>`
    * Description: Get domain suggestions for the given query.
    * Aliases: `domainr`
    * Permissions:
        * `domainr.search` - Main permission node, output to user
        * `domainr.search.loud` - Output to channel
* `domainrinfo <domain>
    * Description: Get information about the given domain.
    * Permissions:
        * `domainr.info` - Main permission node, output to user
        * `domainr.info.loud` - Output to channel

## Output

Commands will send their results to the user by default, unless they have the
appropriate "loud" node.

This plugin also makes use of the protocol's can_flood attribute to display the
output in a nicer format if possible.

## API keys and Client IDs

Domainr has two ways to authenticate to their API: an API key or a client_id.
You must have one of these otherwise the plugin will fail to work. You can get
an API key from [mashape](https://market.mashape.com/nbio/domainr/pricing).
As this requires providing payment details, we recommend you set a limit on
charges in your mashape dashboard.

If you are unable to or do not want to sign up to mashape, the awesome folk at
Domainr have also kindly offered[\[1\]][1][\[2\]][2] to provide client IDs to
us for personal use (i.e. stay within the mashape free tier quota).
Send an email to partners@domainr.com asking for one, and don't forget to
mention that you'll be using it with Ultros!

## Attribution

* Sean Gordon

[1]: https://github.com/UltrosBot/Ultros-contrib/issues/29#issuecomment-135285713
[2]: https://github.com/UltrosBot/Ultros-contrib/issues/29#issuecomment-135634184
