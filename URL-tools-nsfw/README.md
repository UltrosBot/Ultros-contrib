URL-tools-nsfw - Extending the URLs plugin (NSFW)
=================================================

This plugin is similar to URL-tools, but the handlers it provdes are all for
sites that are very much not safe for work, or NSFW. This includes:

* URL handlers for these websites:
    * **f-list** (Required authentication)

[See here](FORMATTING.md) for information on customizing the output of the
handlers.

Getting started
===============

Install the package using the package manager, then enter `config/plugins/` and
copy `urltools-nsfw.yml.example` to `urltools-nsfw.yml`. The default configuration will
enable everything, but you may need to provide API keys or authentication for
some of the handlers, or you may like to change their formatting.

---

```yml
handlers:
  - f-list
```

This is the list of handlers that you want to enable. If you'd rather some of
the sites that are handled by these simply have their page titles retrieved
normally, you may remove any handlers that you don't need from this.


---

```yaml
f-list:
  # We recommend you create a separate account and character for your bot to use, instead of using
  # your own personal f-list account - if you have one, that is.

  username: "username"  # Your login username - Remmeber, you need to have a character on your account!
  password: "password"  # Your login password - Don't worry, this is only used for interacting with the API

  formatting: {}  # See https://github.com/UltrosBot/Ultros-contrib/blob/master/URL-tools-nsfw/FORMATTING.md
  kink-sample: 2  # The max number of random kinks to show; could get quite long
```

This section is the configuration for the [F-List](https://f-list.net) handler. If you're not using it,
then you can ignore or remove this section. This handler requires the use of a username and password.

* **username**: Your login username
* **password**: Your login password
* **formatting**: Formatting strings; see [this file](https://github.com/UltrosBot/Ultros-contrib/blob/master/URL-tools-nsfw/FORMATTING.md)
* **kink-sample**: Maximum number of kinks to use for random samples

---

Once you're all set up and ready to go, don't forget to open **config/settings.yml** and add
**URL-tools** to your list of plugins!

Permissions and commands
========================

All handlers in this package will not trigger without the `urls.trigger.nsfw` permission.

Handler quirks
==============

All handlers will fall back to the standard URL title handler if there's a problem, so you should always have
some kind of title to work with. Additionally, you should take note of the following:

F-List
------

The F-List handler can only handle character URLs:
* `http://f-list.net/c/<character-name>`

This may change in future, if the site expands, and improves its awful api.
