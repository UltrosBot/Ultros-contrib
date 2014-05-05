Jargon
===========

If I can just overclock the Unix Django, I can BASIC the DDOS root,. Damn. But wait... If I can disencrypt their kilobytes with a backdoor handshake then... JACKPOT!

## Configuration

* `formats` - A list of dicts in the following format:
    * `format` - A string with `%s` in places to substitute words
    * `types` - A list of word types (same number as `%s`s above), of `[verbing, verb, adjective, noun, abbreviation]`
* `abbreviations` - A list of abbreviations
* `adjectives` - A list of adjective
* `nouns` - A list of nouns
* `verbs` - A list of dicts in the following format:
    * `plain` - The plain verb
    * `ing` - (optional) The "ing" form of the verb, if not `plain + "ing"`

## Commands and permissions

* `jargon`
    * Description: Generate some jargon.
    * Permissions: `jargon.jargon`

## Attribution

* Sean Gordon
