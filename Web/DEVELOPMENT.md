Writing a plugin that supports Web
==================================

So, you want to work with the web API? Great, let's get started!

Requirements:

* A Python development environment
* Knowledge of how to program in Python
* An idea of what you actually want to do
* A copy of Ultros with the web plugin installed

Got that? Great, let's get started!

### Checking for the presence of the Web plugin

Assuming you've imported `system.plugins.manager.PluginManager`...

```python
    
    class MyPlugin(PluginObject):
    
        @property
        def web(self):
            # We do a property to avoid reference loops
            # If you don't do this, plugins will be un-reloadable
    
            return self.plugman.get_plugin("web")
            
        def setup(self):
            self.plugman = PluginManager()  # Grab the plugin manager
            
            if self.web is None:  # If it's None, it's not loaded
                self.logger.error("Please load the Web plugin.")
                self._disable_self()
                return
```

### Creating your own Web route

In previous versions of the plugin, we had a rather nasty function-passing
routes method. We grew out of that, however, and now we have something much 
nicer.

To do this, you'll need to follow the following plan..

* Work out what module your plugin is. We'll use `plugins.myplugin.MyPlugin` as
  an example plugin class location in this case.
* Create a class subclassing `plugins.web.request_handler.RequestHandler`.
* Register it using a string - in this case, `plugins.myplugin.route.Route`
* Add navbar entries, if any

#### An example class

We'd create this as part of `myplugin` - in `routes.py`

```python

    """
    Example page - /hello
    """
    
    from plugins.web.request_handler import RequestHandler
    
    
    class Route(RequestHandler):
    
        name = "hello"  # Name of the navbar entry (for display purposes)
    
        def get(self):  # The HTTP method to respond to. Could be PUT, POST, etc.
            self.finish("Hello, world!")
```

#### Registering it

```python
    
    class MyPlugin(PluginObject):
    
        @property
        def web(self):
            # We do a property to avoid reference loops
            # If you don't do this, plugins will be un-reloadable
    
            return self.plugman.get_plugin("web")
            
        def setup(self):
            self.plugman = PluginManager()  # Grab the plugin manager
            
            if self.web is None:  # If it's None, it's not loaded
                self.logger.error("Please load the Web plugin.")
                self._disable_self()
                return
            
            self.web.add_handler(
                r"/hello",  # The path to our route
                "plugins.myplugin.route.Route"  # Route's module name, including class
            )
            
            self.web.add_navbar_entry(  # If we need a navbar entry at all
                "hello",  # The navbar name, needs to match the route
                "/hello",  # The path to our route
                "info letter"  # A semantic-ui icon name
            )
```

**Remember**: Your route's path is a regular expression! Bear that in mind if you're
getting strange routing behavior!

### Conditional routes

Sometimes, you'll need more than just a simple route. Our admin interface is a good
example of this - we could register a route for each file separately, but it would make
more sense to have a route that could handle all of those files.

#### Registering such a route

```python

        # In our plugin's setup()...
        
        self.web.add_handler(
            r"/hello/([^/]{0,})",
            "plugins.myplugin.route.MyRoute" 
        )
```

The route's path is a regular expression. Capture groups are passed as parameters
to the HTTP request function in your route class. Anonymous capture groups are
passed as simple arguments, while named capture groups are passed as keyword
arguments.

#### Creating such a route

```python

    """
    Example page - /hello/{username}
    """
    
    from plugins.web.request_handler import RequestHandler
    
    
    class Route(RequestHandler):
    
        name = "hello"  # Name of the navbar entry (for display purposes)
    
        def get(self, username):  # The HTTP method to respond to. Cold be PUT, POST, etc.
            self.finish("Hello, %s!" % username)
```

### Templates

Instead of writing your HTML inside your classes, which isn't recommended, you
may use a template, placed in the `web/templates` folder. All templates should
end in `.html` and must be in [Mako template format](docs.makotemplates.org/en/latest/).

```python

    """
    Example page - /hello/{username}
    """
    
    from plugins.web.request_handler import RequestHandler
    
    
    class Route(RequestHandler):
    
        name = "hello"  # Name of the navbar entry (for display purposes)
    
        def get(self, username):  # The HTTP method to respond to. Cold be PUT, POST, etc.
            self.render(
                "message.html",  # Path to your template, relative to web/templates
                
                # kwargs to pass to the template
                message="Hello, %s!" % username
            )
```

Our template system inserts various arguments into the template for you. Consider
this list before you attempt to insert them yourself. Also, note that you cannot
override any of these directly.

* `extra_css` - A list of extra CSS files to load, used internally. 
    * This is gotten from the `css` attribute of the class. You may append to 
        that if needed. We recommend you do that in the `initialize` method.
* `extra_js` - A list of extra JS files to load, used internally.
    * This is gotten from the `js` attribute of the class. You may append to 
        that if needed. We recommend you do that in the `initialize` method.
* `nav_items` - A list of navbar items, used to generate the navbar. 
* `nav_name` - The name of the page as defined in the class. This is used to
    work out which nav item should be marked as active.
* `plugin` - The instance of the Web plugin. Also available as `self.plugin`.
* `session` - The session object, as detailed in the next section. 
* `sessions` - Sessions manager instance.
* `xsrf` - A function for making forms XSRF-protected.
* `_message` - Gotten from the request arguments, a message to display at the
    top of the page (if present).
* `_message_type` -  Gotten from the request arguments, the colour of the above 
    message.

Additionally, some other arguments are used by the base template, if present.

* `headers` - A list of raw HTML headers to add to the page

### Sessions and permissions

We've implemented what we hope is a fairly simplistic sessions system. To work
with it, you can use the following route class attributes..

* `.sessions` - Direct access to the plugin's SessionManager object.
  You probably won't need to use most of these yourself.
    * `.check_login(username, password)` - Checks if a username and password match
    * `.check_session(s)` - Check whether a session object is valid
    * `.clear_old()` - Iterate over and remove invalid sessions
    * `.create_session(username, remember=False)` - Create and return a new session key
    * `.delete_session(key)` - Delete a session corresponding to a key
    * `.delete_sessions_for_user(username)` - Invalidate all of one user's sessions
    * `.get_session(key)` - Get a session object for a session key
    * `.update_session_time(key)` - Update a session key's validity period using the current time
* `.clear_session()` - Clears the session cookie
* `.get_session_key()` - Get the current session key
* `.get_session_object()` - Get the current session object
* `.set_session(key, remember=False)` - Set the current session key

For the most part, all you're going to need here is `get_session_object()`. This will return `None`
if there's no session, and a `dict` of the following form if there's an active, verified session.

```python

    {
        "remember": False,      # Boolean, whether the user logged in with the "Remember me" option
        "time": 1413449203.0,   # UNIX timestamp, when the session was last used
        "username": "username"  # String, the user this session belongs to
    }
```

If you need to check a permission against a session, the plugin has a handy function for doing just that.

```python

        def get(self):
            s = self.get_session_object()
            
            if self.plugin.check_permission("web.perms.other", s):
                return self.finish("Yay!")
            
            self.finish("Nay!")
```

This will even work when the session is `None` - Allowing you to check the default permissions group. You
can also pass a string in here, which is useful if you're using API keys - which are covered later on.

### Cross-site request forgery protection (XSRF)

A fairly common attack vector nowadays is cross-site request forgery - For example, tricking a user
into clicking a link that submits a form on a target site, making the attacker admin, or.. Embedding
a form into a page controlled by the attacker that gets submitted on page load.

To help combat this, we've added some easy tools to enable XSRF protection for any forms in your templates.
This works by adding a required value to a form that the attacker is unable to guess.

1. Use the `@check_xsrf` decorator with your `post()` and `put()` functions
2. Within the declaration of your form in the page template, insert `${xsrf()}`
3. That's it, your route is now XSRF-protected!

### Asynchronous routes

Ultros is built on Twisted, so you may wish (or need) to use Deferreds and other asynchronous calls
and tools. As the web plugin uses Cyclone internally, you can simply use Cyclone's methods for doing
this - a good example is in the [Factoids plugin](https://github.com/UltrosBot/Ultros/blob/master/plugins/factoids/route.py),
but there's a simplified example here as well.

```python

    from cyclone.web import asynchronous
    
    from plugins.web.request_handler import RequestHandler
    
    class Route(RequestHandler):
    
        name = "hello"
    
        @asynchronous
        def get(self, *args, **kwargs):
            d = some_long_running_task()
    
            d.addCallbacks(self.success_callback, self.fail_callback)
    
        def success_callback(self, result):
            self.finish("Result: %s" % result)
    
        def fail_callback(self, failure):
            self.set_status(500)
    
            self.write_error(500, exception=failure)
```

### Convenience functions and properties

Each route has a bunch of functions you can use. They're designed to make certain
tasks easier, and should be used instead of reimplementing the things they do.

* `add_css(path)` - Add an extra CSS file
* `add_js(path)` - Add an extra JS file
* `clear_session()` - See the **Sessions and permissions** section
* `finish_json(_dict)` - Sets the `Content-Type` header to `application/json`, and sends a dict serialized
  as JSON to the client, finishing the response.
* `get_session_key()` - See the **Sessions and permissions** section
* `get_session_object()` - See the **Sessions and permissions** section
* `redirect(url, permanent=False, status=None, message=None, message_colour="green", redirect=None)` - 
  Send a redirect to the client.
    * `permanent` - Whether this should be a temporary or permanent redirect
    * `status` - The status code to use, if `permanent` is None
    * `message` - A message to be shown on the top of the page you're sending the client to, provided it's
      a part of the web interface
    * `message_colour` - Colour of the above message, uses the colours from Semantic UI
    * `redirect` - For the login page only, the page to go to after the user has logged in
* `render(template_name, **kwargs)` - Render a template with the given arguments, and finish the response.
* `set_session(key, remember=False)` - See the **Sessions** section
* `write_error(status_code, **kwargs)` - Write an error message. You can usually just throw an exception instead.

Additionally, the following properties are available on each route.

* `plugin` - The current instance of the Web plugin
* `sessions` - Sessions manager instance

### API keys and routes

A new feature with Web 1.0.0 is the ability for users to add and manage API keys from their
account page. These API keys are to be used with any REST API methods you create, whether
they're for controlling the bot, or part of a plugin. Never use sessions for API stuff, as
doing so will make your API routes vulnerable to XSRF attacks.

Any API route requiring authentication should take an `api_key` GET or POST parameter. Where
relevant, this should not be an optional parameter, and can be used to identify the username
associated with the API key - and thus, what permissions they have.

To validate a key, you may do something similar to the following.

```python

        def get(self):
            api_key = self.get_argument("api_key", default=None)
            
            if api_key is None:
                return self.finish_json({"error": "An API key is required"})
            
            username = self.plugin.api_keys.get_username(key)
            
            if username is None:
                return self.finish_json({"error": "API key not found"})
            
            if not self.plugin.check_permission("web.api.hello", username):
                return self.finish_json({"error": "You don't have permission to access this"})
            
            self.finish_json({"messsage": "Hello, %s!" % username})
```

### Other stuff

* Any raised exceptions will result in an error page that attempts to extract
  and display the traceback. If that's not what you want, catch any exceptions
  yourself.
* The Web plugin uses Cyclone internally, and the RequestHandler class is
  based on the standard Cyclone one. Therefore, a lot of Cyclone's documentation
  is relevant here as well.
    * You can find that here: [Cyclone documentation](http://cyclone.io/documentation/)
* If there's any information that should be here that you feel might be useful to
  people starting out with this plugin, please raise a ticket.