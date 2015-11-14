URL-tools - Extending the URLs plugin
=====================================

This plugin adds various shorteners and URL handlers which interface with the
URLs plugin that comes bundled with Ultros. Right now, these are as follows:

* URL handlers for these websites:
    * **GitHub** (Optional authentication)
    * **osu!** (Required authentication)
* URL shorteners using these services:
    * **is.gd**
    * **nazr.in** (Note: Down a lot)
    * **v.g**
    * **waa.ai**

[See here](FORMATTING.md) for information on customizing the output of the
handlers.

Getting started
===============

Install the package using the package manager, then enter `config/plugins/` and
copy `urltools.yml.example` to `urltools.yml`. The default configuration will
enable everything, but you may need to provide API keys or authentication for
some of the handlers, or you may like to change their formatting.

---

```yml
handlers:
  - github
  - osu
```

This is the list of handlers that you want to enable. If you'd rather some of
the sites that are handled by these simply have their page titles retrieved
normally, you may remove any handlers that you don't need from this.

---

```yaml
shorteners:
  - is.gd
  - nazr.in
  - v.gd
  - waa.ai
```

If you'd like to disable one of the included URL shorteners, then you can remove
them from this list.

---

```yaml
github:
  zen: false  # Whether to use GitHub Zen for URLs that are unhandleable
              # Disable and the bot will be silent for them
  formatting: {}  # See documentation if you want to change the formatting and remember to prefix each value  with !!python/unicode
  random_sample_size: 5  # Maximum watchers/stargazers/tags/etc to use when a random sample is taken

  # You need to authenticate if you want to raise the API limits, which is highly recommended.
  # Make your own application at https://github.com/settings/applications/new and enter the client ID and secret here.

  # client_id = ""
  # client_secret = ""
```

This section is the configuration for the [GitHub](https://github.com) handler. If you're not using it,
then you can ignore or remove this section. It also does have some sane defaults if you
just want to install the plugin and go.

* **zen**: GitHub doesn't have usable APIs for all types of pages. Enable this 
  if you'd like the bot to output some GitHub Zen for those instead - otherwise, 
  the bot will remain silent
* **formatting**: See [FORMATTING.md](FORMATTING.md) for more information on this section.
* **random_sample_size**: The maximum number of watchers, stargazers, tags, and so on to show when picking a random sample when the following URLs are handled:
    * `https://github.com/[Repository]/watchers`
    * `https://github.com/[Repository]/stargazers`
    * `https://github.com/[Repository]/tags`
* **Authentication**: You can get a client ID and secret by [making an application here](https://github.com/settings/applications/new)
    * Adding a client ID and secret will significantly raise your API limits, so we highly recommend doing so
    * **client_id**: The Client ID from your application
    * **client_secret**: The Client Secret from your application

---

```yaml
osu:
  api_key: ""  # Required; see https://osu.ppy.sh/p/api (Requires an account)
  formatting: {}  # See documentation if you want to change the formatting and remember to prefix each value  with !!python/unicode
```

This section is the configuration for the [osu!](https://osu.ppy.sh) handler. If you're not using it,
then you can ignore or remove this section. The osu! API requires that you have an
API key, so create an account and [grab your API key here](https://osu.ppy.sh/p/api).

* **api_key**: Your osu! API key
* **formatting**: See [FORMATTING.md](FORMATTING.md) for more information on this section

---

Once you're all set up and ready to go, don't forget to open **config/settings.yml** and add
**URL-tools** to your list of plugins!

Permissions and commands
========================

There are no permissions or commands for this plugin.

Handler quirks
==============

All handlers will fall back to the standard URL title handler if there's a problem, so you should always have
some kind of title to work with. Additionally, you should take note of the following:

GitHub
------

The GitHub API only refers to milestones by ID - the milestone names given in milestone URLs are not supported.
As such, you will still be able to use these URLs, but you'll have to replace the name with the milestone ID - starting
with `1` for the earliest milestone. This is less than ideal, but I'm told that they're working on it.

The GitHub handler is unable to handle certain types of URLs. The following URLs and any others under them
will fall through to the next handler - unless zen has been enabled, which will cause the bot to output
GitHub Zen instead.

* https://github.com/about
* https://github.com/blog
* https://github.com/contact
* https://github.com/explore
* https://github.com/integrations
* https://github.com/issues
* https://github.com/pricing
* https://github.com/pulls
* https://github.com/security
* https://github.com/settings
* https://github.com/showcases
* https://github.com/site
* https://github.com/stars
* https://github.com/trending

The following URLs always fall through to the next handler.

* https://github.com/

The following repository sections will simply return the basic repository info.

* Blame
* Graphs
* Pulse
* Settings
* Wiki

osu!
----

The following sections always fall through to the next handler.

* Forum
* Main page
* News
* Wiki

Some URLs support fragments or query parameters.

* A query string is seen at the end of a URL, starting with a `?` and going to the end of the URL, or the first `#`, if any.
* A fragment is seen at the end of a URL, starting with `#` and going to the end of the URL.

These are as seen on the site, and are taken into account by this handler.

* `m`: The selected gamemode. The site only uses numbers, but the plugin supports a number of alternative placeholders, if users would prefer to use them. These work on user, mapset and beatmap pages.
    * **Standard**: `0`, `standard`, `osu`, `osu!`
    * **Taiko**: `1`, `taiko`, `drum`
    * **Catch the Beat**: `2`, `ctb`, `catchthebeat`, `catch`, `beat`, `fruit`
    * **Mania**: `3`, `mania`, `osu!mania`, `osumania`
* `t` or `type`: To specify whether the user provided is a username or a user ID. This is to resolve discrepancies with numerical usernames.
    * `string`: To specify that the user specified is a username.
    * `id`: To specify that the user specified is a numerical ID.
