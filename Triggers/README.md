Triggers
===========

Configurable trigger responses

## Configuration

All sections under `triggers` are optional.

* `triggers`
    * `global` - List of triggers that are global across the bot
    * `protocols` - Dict of protocol names
        * `<proto-name>`
            * `global` - List of triggers that are global across the protocol
            * `channels` - Dict of channels
                * `<channel-name> - List of triggers for this channel

### Trigger format

Triggers are a dict with the following keys:

* `trigger` - A regular expression to search incoming messages for
* `response` - A list of possible responses
* `chance` - (Optional - default: 100) A percentage (0-100) that the trigger will fire
* `flags` - (Optional - default: None) Single-character flags to pass to the regex engine
* `trigger_types` - (Optional - default: {"message": True}) The type of message to trigger on (`message`, `action`, or `notice` (IRC-only))
* `response_type` - (Optional - default: "message") The type of event to respond with (`message`, `action`, `notice` (IRC-only), `channel_kick`, `channel_ban`, `global_kick`, or `global_ban`)
* `permission` - (Optional - default: None) The additional sub-permission required to activate this trigger.

#### Flags

* `D` - Debug
* `I` - Ignore case
* `L` - Locale
* `M` - Multiline
* `S` - Dot all
* `U` - Unicode
* `X` - Verbose

See Python re docs for more info.

#### Response

Responses can either be the response string, or a dict containing the `response`
string and a per-response `type`. Any response without a `type` will use the trigger's
`response_type`.

Responses can contain dynamic content using `{key}`. Possible keys are:

* `<number>` - Any number may be used to be replaced with the number group in the search. E.g. `(Foo)(Bar)`, `1` will be `Foo`, `2` will be `Bar`
* `<name>` - A named capture group from the search. E.g. `(?P<baz>qux)`, `baz` will be `qux`
* `channel` - Channel, as specified in the config
* `source` - User who triggered the response
* `target` - Channel where the response will be sent
* `message` - Original message that triggered the response
* `protocol` - Protocol where the trigger happened

## Permissions

* `triggers.trigger`
    * Description: Whether user's messages can set off triggers.
* `triggers.trigger.<trigger_perm>`
    * Description: Whether user's messages can set off a specific trigger. Also requires the `trigger.trigger` permission.

## Attribution

* Sean Gordon
