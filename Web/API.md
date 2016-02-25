REST API (Draft)
================

This is a draft document outlining our plans for the REST API. It will be
updated over time, as and when things are changed and finalized.

HTTP verbs
----------

Each of your available HTTP verbs has a different meaning - While these may
not *entirely* conform to their usual uses, understanding what they mean will
be helpful while designing your API client.

* `GET` - Retrieve information
* `POST` - Insert, update, or otherwise change something or perform an action

More verbs will be added here as they become necessary.

URL structure
-------------

API URLs are structured in the following way:

* `/api/v1` - Versioned API, to deal with deprecation
* `/<api key>` - The API key, used for authentication
* `/[manage, plugins, protocols]` - The section you're dealing with
    * `/manage` - For management of Ultros' various systems
        * `/protocols/<name/s>/<action>` - Used for protocol management
        * `/pluginss/<name/s>/<action>` - Used for plugin management
    * `/plugins/<name/s>/<action>` - For working directly with plugins, some of
      which may define custom actions
    * `/protocols/<name/s>/<action>` - For working directly with protocols, some
      of which may define custom actions

For example, we may decide to utilize the web plugin's `get_username` call,
which returns the username associated with the given API key. The request we
construct may be something like this:

`GET /api/v1/<api key>/plugins/web/get_username`

This would return data similar to the following:

```json
{
    "username": "<your username>"
}
```

Batch operations
----------------

This REST API supports batch operations over multiple targets, using special
name strings. These may be used anywhere you see `<name/s>` in the URL spec.

* `irc-esper` - A single name here, which matches a single target
* `irc-esper,mumble` - Multiple names here, which matches each corresponding target
* `*` - A wildcard, which matches all targets of the corresponding type

For example, if we wanted to unload all protocols, we might do something like this:

`POST /api/v1/<api key>/manage/protocols/*/unload`

Or if we wanted to get all the users on our protocols, we might do:

`GET /api/v1/<api key>/protocols/*/users`

..which may return data similar to this:

```json
{
    "irc-esper": [
        {
            "username": "g",
            [...]
        },
        {
            "username": "Kasen",
            [...]
        },

        [...]
    ],
    "mumble": [
        {
            "username": "g",
            [...]
        },
        [...]
    ]
}
```

Complete API calls
------------------

All API calls are listed relative to the API root, eg they go after
`/api/v1/<apikey>`

### Web plugin

* `GET /plugins/web/get_username`: Returns the username associated with the supplied API key
