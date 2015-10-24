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

Getting started
===============

Install the package using the package manager, then enter `config/plugins/` and
copy `urltools.yml.example` to `urltools.yml`. Open the file, and fill it out
as follows..

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
API key, so create an account and [grab your API key here[(https://osu.ppy.sh/p/api).

* **api_key**: Your osu! API key
* **formatting**: See [FORMATTING.md](FORMATTING.md) for more information on this section

---

Once you're all set up and ready to go, don't forget to open **config/settings.yml** and add
**URL-tools** to your list of plugins!

Permissions and commands
========================

There are no permissions or commands for this plugin.
