Domai.nr
===========

This plugin allows integration with the Domai.nr API.

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

## Attribution

* Sean Gordon
