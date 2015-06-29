Jargon
===========

If I can just overclock the Unix Django, I can BASIC the DDOS root,. Damn. But wait... If I can disencrypt their kilobytes with a backdoor handshake then... JACKPOT!

## Configuration

* `version` - The config format version. This is version 2. Old style configs (implicit version 1) will still work.
* `default` - The default category if not given in the command. Leaving this out will result in a random category.
* `per_category_permissions` - Whether or not to require a permission for each individual category/type.
* `prefix_response` - Whether or not messages should be prefixed with "[Jargon] ". This is important if any of your jargon phrases begin with characters/phrases that could trigger other bots.
* `categories` - A dict of categories/types of jargon
    * `<category name>`
        * `names` - An optional list of names to be used instead of the category name above. The first entry is used as the name for `per_category_permissions`.
        * `options` - An optional dict of extra options
            * `capitalise_start` - Uppercase the first letter of generated jargon.
        * `formats` - A list of format strings. See the Format section for details.
        * `words` - A dict of word types
            * `<word type>` - A list of words of a specific type. See the Format section for details.

## Commands and permissions

* `jargon [type]`
    * Description: Generate some jargon.
    * Permissions:
        * `jargon.jargon`
        * `jargon.jargon.<category_name>` if `per_category_permissions` is enabled, in addition to the above permission
    * Aliases:
        * `generatesentence`
        * `generate`
* `jargonlist`
    * Description: Lists all types of jargon available. If `per_category_permissions` is enabled, only categories the user has permission for will be shown.
    * Permissions: `jargon.jargonlist`
    * Aliases:
        * `generatesentencelist`
        * `generatelist`

## Format

### Format strings

Strings can have random words inserted into them using `{word}` style tags. For example:

`"My {noun} likes to {verb} other {noun.plural}."`

In this string, the curly brace tags `{}` are replaced with a word of the type specified inside them.
Word types can come in different forms, which can be specified with a dot after the type followed by the form, as shown
by the plural form of a noun in the example above.

If you want to have actual curly braces in your output, you can escape them with a backslash. You will have to use two
backslashes as one backslash will be interpreted as a YAML escape sequence.

### Word types

You can use any "word type" you want, but there are a few builtin ones with special functionality. Custom word types
can be either a list of strings or list of dicts. If dicts are used, you must access them as `{word_type.dict_key}`
instead of just `{word_type}`. The builtin ones below can be a mixture of both, where a bare string will be used as the
base type and the plugin will attempt to generate missing entries.

Available builtins:

* `noun` - Available forms:
    * `singular` - Base form
    * `plural`
* `verb` - Available forms:
    * `base` - Base form (e.g. "go")
    * `past` - "-ed" form (e.g. "went")
    * `past_participle` - Only useful for irregular verbs (e.g. "gone")
    * `present` - "-s" form (e.g. "goes")
    * `present_participle` - "-ing" form (e.g. "going")

Additionally, `verb` has some aliases that can be used in format strings:

    * `s` => `present`
    * `ing` => `present_participle`
    * `ed` => `past`

These cannot be used in the word type definitions.

## Attribution

* Sean Gordon
