Ultros - Web/HTTP plugin
========================

Woah woah woah. What's this? A web interface? You totally didn't see this coming, right?

Well, maybe you did. Anyway..

What the heck?
--------------

The Web plugin provides a web interface, which is accessible to people using web
browsers. Well-known examples of web browsers are Firefox, Chrome, Opera, Safari,
often obtained by using the browser-downloading tool known as Internet Explorer.

It's designed so that plugins may add sections easily, and also allows applications
to be written outside of Ultros that utilize this plugin's REST API.

Installation
------------

You can install this plugin from the package manager.

```sh
python packages.py install Web
```

Following that, you should head over to `config/plugins/` and copy `web.yml.example`
to `web.yml`. Next, open it up, and fill it out as follows..

* `hostname` - The interface to listen on. Use "0.0.0.0" to listen on everything.
* `port` - The port to listen on. Make sure it's accessible!
* `public_address` - An address that can be used to connect. Make sure this is set,
  some plugins need it!
* `reset_message` - A message to show to anyone that attempts to reset their password
  on the login page.
* `hosted` - Using OpenShift or some other provider? This is the place to set up the
  environment variables they require you to use. They're used to determine what
  hostname and port to listen on.
    * Leave this set to false or comment it out if you don't need it.
    * Set it to "openshift" if you're on OpenShift
    * Otherwise, set it up as described in the configuration file.

Add "web" to your plugins config and start up the bot or load the plugin using the 
management commands, and wait for the server to start up. Head to the `public_address`
you specified above, and make sure it works. You should get a page that looks similar
to the following...

![Index page](http://i.imgur.com/TxvxWNd.png)

If so, then you're all set up and ready for use! Note, you won't see the `Factoids`
menu option unless you have the Factoids plugin enabled.

Permissions
-----------

* `web.admin` - Allows access to and use of the admin interface, including..
    * Access to the CPU and RAM graphs
    * Access to view and edit all of the loaded config and data files
* `web.index.plugins` - Allows listing plugins and packages on the index page
* `web.index.protocols` - Allows listing protocols on the index page

Please don't give admin to anyone you wouldn't trust with your passwords and data.

Usage
-----

For most users, the web interface will be purely informational. Indeed, if you're not
logged in, the plugin defaults to only allowing access to the index and login pages.

You may login at the top-right.

![](http://i.imgur.com/ZBkY2mX.png)

Your username and password are the same ones you use to login with the bot on a
chat network.

Once you've logged in, you should see something like the following..

![](http://i.imgur.com/ySwAm4G.png)

If you're an admin or have the `web.admin` permission, you can access the admin
interface on the left. We'll cover this later.

To manage your account details, you can click on your username at the top-right.

![](http://i.imgur.com/QmajuIt.png)

From there, you can edit your password, add and remove API keys, and kill any sessions
you may have logged in on whatever chat networks your bot is connected to. In this case,
I'm logged in on EsperNet's IRC.

![Account page](http://i.imgur.com/VxxZ4BW.png)

---

If you're an admin, you may manage certain aspects of the bot from the admin interface.
Right now, the bot supports three main functions..

#### Resource usage graphs (CPU and RAM used by Ultros)

![Admin index](http://i.imgur.com/Jbbjhkm.png)

#### Listing of files loaded by Ultros

![Admin file list](http://i.imgur.com/tcgqokv.png)

#### Viewing and editing of aforementioned files

![Admin file editor](http://i.imgur.com/9uRTLB3.png)

Note that editing most files will reload them for whatever plugin uses them automatically,
provided the plugin has been written to support this.

Supported plugins
-----------------

So far, we're aware of the following plugins that support the web interface..

* Factoids - List factoids in a table (Permission: `factoids.get.web`)
* Twilio - For SMS message callbacks

Screenshots
-----------

#### Index page

![Index page](http://i.imgur.com/TxvxWNd.png)

#### Account page

![Account page](http://i.imgur.com/VxxZ4BW.png)

#### Factoids view page

![Factoids page](http://i.imgur.com/bQdIOSz.png)

#### Resource usage graphs (CPU and RAM used by Ultros)

![Admin index](http://i.imgur.com/Jbbjhkm.png)

#### Listing of files loaded by Ultros

![Admin file list](http://i.imgur.com/tcgqokv.png)

#### Viewing and editing of aforementioned files

![Admin file editor](http://i.imgur.com/9uRTLB3.png)