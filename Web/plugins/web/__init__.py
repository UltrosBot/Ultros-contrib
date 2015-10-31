# coding=utf-8

"""
Good ol' web interface and REST API plugin.

We're at 1.0.0! Cyclone <3
"""

__author__ = "Gareth Coles"

import os
import re

from cyclone.web import Application, StaticFileHandler

from plugins.web.apikeys import APIKeys
from plugins.web.events import ServerStartedEvent, ServerStoppedEvent
from plugins.web.template_loader import TemplateLoader
from plugins.web.sessions import Sessions
from plugins.web.stats import Stats

from system.command_manager import CommandManager
from system.event_manager import EventManager
from system.plugins.manager import PluginManager
from system.plugins.plugin import PluginObject
from system.storage.formats import YAML, JSON
from system.storage.manager import StorageManager
from system.translations import Translations

from twisted.internet import reactor

from utils.packages.packages import Packages
from utils.password import mkpasswd

_ = Translations().get()
__ = Translations().get_m()


class WebPlugin(PluginObject):
    """
    Web plugin object
    """

    api_log = None
    api_keys = None

    api_key_data = {}
    config = {}
    data = {}

    namespace = {}  # Global, not used right now

    handlers = {}  # Cyclone handlers

    interface = ""  # Listening interface
    listen_port = 8080

    running = False

    application = None  # Cyclone application
    port = None  # Twisted's server port
    storage = None
    template_loader = None

    navbar_items = {}

    ## Stuff plugins might find useful

    commands = None
    events = None
    packages = None
    plugins = None
    sessions = None
    stats = None

    ## Internal(ish) functions

    def setup(self):
        self.storage = StorageManager()

        try:
            self.config = self.storage.get_file(self, "config", YAML,
                                                "plugins/web.yml")
            self.logger.debug("Config loaded")
        except Exception:
            self.logger.exception(_("Error loading configuration"))
            self._disable_self()
            return
        if not self.config.exists:
            self.logger.error(_("Unable to find config/plugins/web.yml"))
            self._disable_self()
            return

        try:
            self.data = self.storage.get_file(self, "data", JSON,
                                              "plugins/web/data.json")
            self.logger.debug("Data loaded")
        except Exception:
            self.logger.exception("Error loading data file!")
            return self._disable_self()

        try:
            _sessions = self.storage.get_file(self, "data", JSON,
                                              "plugins/web/sessions.json")
            self.logger.debug("Sessions loaded")
        except Exception:
            self.logger.exception("Error loading sessions file!")
            return self._disable_self()

        try:
            self.api_log = open("logs/api.log", "w")
        except Exception:
            self.logger.exception("Unable to open api log file!")
            return self._disable_self()

        try:
            self.api_key_data = self.storage.get_file(
                self, "data", JSON, "plugins/web/apikeys.json"
            )
            self.logger.debug("Sessions loaded")
        except Exception:
            self.logger.exception("Error loading API keys!")
            return self._disable_self()

        try:
            self.api_log = open("logs/api.log", "w")
        except Exception:
            self.logger.exception("Unable to open api log file!")
            return self._disable_self()

        self.config.add_callback(self.restart)
        self.data.add_callback(self.restart)

        # Index page

        self.add_handler(r"/", "plugins.web.routes.index.Route")

        # Login-related

        self.add_handler(r"/login", "plugins.web.routes.login.Route")
        self.add_handler(r"/logout", "plugins.web.routes.logout.Route")
        self.add_handler(
            r"/login/reset",
            "plugins.web.routes.login-reset.Route"
        )

        # Accounts-related

        self.add_handler(r"/account", "plugins.web.routes.account.index.Route")
        self.add_handler(
            r"/account/password/change",
            "plugins.web.routes.account.password.change.Route"
        )
        self.add_handler(
            r"/account/apikeys/create",
            "plugins.web.routes.account.apikeys.create.Route"
        )
        self.add_handler(
            r"/account/apikeys/delete",
            "plugins.web.routes.account.apikeys.delete.Route"
        )
        self.add_handler(
            r"/account/users/logout",
            "plugins.web.routes.account.users.logout.Route"
        )

        # Admin-related

        self.add_handler(
            r"/admin",
            "plugins.web.routes.admin.index.Route"
        )
        self.add_handler(
            r"/admin/files",
            "plugins.web.routes.admin.files.Route"
        )
        self.add_handler(
            r"/admin/files/(config|data)/(.*)",
            "plugins.web.routes.admin.file.Route"
        )
        self.add_handler(
            r"/api/admin/get_stats",
            "plugins.web.routes.api.admin.get_stats.Route"
        )

        self.add_navbar_entry("admin", "/admin", "settings")

        # API routes

        self.add_api_handler(
            r"/plugins/web/get_username",
            "plugins.web.routes.api.plugins.web.get_username.Route"
        )

        # Stuff routes might find useful

        self.api_keys = APIKeys(self, self.api_key_data)
        self.commands = CommandManager()
        self.events = EventManager()
        self.packages = Packages(False)
        self.plugins = PluginManager()
        self.sessions = Sessions(self, _sessions)
        self.stats = Stats()

        # Load 'er up!

        r = self.load()

        if not r:
            self._disable_self()
            return

        if not self.factory_manager.running:
            self.events.add_callback(
                "ReactorStarted", self, self.start, 0
            )
        else:
            self.start()

    def load(self):
        if "secret" not in self.data:
            self.logger.warn("Generating secret. DO NOT SHARE IT WITH ANYONE!")
            self.logger.warn("It's stored in data/plugins/web/data.json - "
                             "keep this file secure!")
            with self.data:
                self.data["secret"] = mkpasswd(60, 20, 20, 20)

        self.template_loader = TemplateLoader(self)

        if self.config.get("output_requests", True):
            log_function = self.log_request
        else:
            log_function = self.null_log

        self.application = Application(
            list(self.handlers.items()),  # Handler list

            ## General settings
            xheaders=self.config.get("x_forwarded_for", False),
            log_function=log_function,
            gzip=True,  # Are there browsers that don't support this now?
            # error_handler=ErrorHandler,

            ## Security settings
            cookie_secret=self.data["secret"],
            login_url="/login",

            ## Template settings
            template_loader=self.template_loader,

            ## Static file settings
            static_path="web/static"
        )

        # .well-known file handler

        self.application.add_handlers(
            r".*$",
            [(
                r"/\.well-known/(.*)", StaticFileHandler,
                {"path": "web/static/.well-known"}
            )]
        )

        if self.config.get("hosted", False):
            hosted = self.config["hosted"]

            if isinstance(hosted, dict):
                self.interface = os.environ.get(hosted["hostname"], False)
                self.port = os.environ.get(hosted["port"], False)

                if not self.interface:
                    self.logger.error(
                        "Unknown env var: %s" % hosted["hostname"]
                    )
                    return False
                if not self.port:
                    self.logger.error(
                        "Unknown env var: %s" % hosted["port"]
                    )
                    return False
            else:
                if hosted in ["openshift"]:
                    self.interface = os.environ.get("OPENSHIFT__IP", False)
                    self.port = os.environ.get("OPENSHIFT__PORT", False)

                    if not self.interface:
                        self.logger.error(
                            "Unknown env var: OPENSHIFT__IP - Are you on "
                            "OpenShift?"
                        )
                        return False
                    if not self.port:
                        self.logger.error(
                            "Unknown env var: OPENSHIFT__PORT - Are you on "
                            "OpenShift?"
                        )
                        return False
                else:
                    self.logger.error("Unknown hosted service: %s" % hosted)
                    return False

        else:
            if self.config.get("hostname", "0.0.0.0").strip() == "0.0.0.0":
                self.interface = ""
            else:
                self.interface = self.config["hostname"]

            self.listen_port = self.config.get("port", 8080)

        return True

    def start(self, _=None):
        self.stats.start()

        self.port = reactor.listenTCP(
            self.listen_port, self.application, interface=self.interface
        )

        self.logger.info("Server started")
        self.running = True

        self.events.run_callback(
            "Web/ServerStartedEvent",
            ServerStartedEvent(self, self.application)
        )

    def stop(self):
        self.application.doStop()
        d = self.port.stopListening()

        d.addCallback(lambda _: self.logger.info("Server stopped"))
        d.addCallback(lambda _: setattr(self, "running", False))
        d.addCallback(lambda _: self.events.run_callback(
            "Web/ServerStopped", ServerStoppedEvent(self)
        ))

        d.addErrback(lambda f: self.logger.error("Failed to stop: %s" % f))

        self.stats.stop()

        return d

    def restart(self):
        d = self.stop()

        d.addCallback(lambda _: [self.load(), self.start()])

    def deactivate(self):
        d = self.stop()

        self.handlers.clear()
        self.navbar_items.clear()

        return d

    def log_request(self, request):
        log = self.logger.info

        status_code = request.get_status()

        if status_code >= 500:
            log = self.logger.error
        elif status_code >= 400:
            log = self.logger.warn

        path = request.request.path

        # Check if this is an API method and hide the key if so

        matched = re.match(r"/api/v[0-9]/([a-zA-Z0-9]+)/.*", path)

        if matched:
            key = matched.groups()[0]
            user = self.api_keys.get_username(key)

            if user:
                path = path.replace(key, "<API: %s>" % user)
            else:
                path = path.replace(key, "<API: Invalid key>")

        log(
            "[%s] %s %s -> HTTP %s"
            % (
                request.request.remote_ip,
                request.request.method,
                path,
                request.get_status()
            )
        )

    def null_log(self, *args, **kwargs):
        pass

    ## Public API functions

    def add_api_handler(self, pattern, handler, version=1):
        if not pattern.startswith("/"):
            pattern = "/%s" % pattern
        pattern = "/api/v%s/([A-Za-z0-9]+)%s" % (version, pattern)

        return self.add_handler(pattern, handler)

    def add_handler(self, pattern, handler):
        self.logger.debug("Adding route: %s -> %s" % (pattern, handler))

        if pattern in self.handlers:
            self.logger.debug("Route already exists.")
            return False

        self.handlers[pattern] = handler

        if self.application is not None:
            self.application.add_handlers(r".*$", [(pattern, handler)])

        self.logger.debug("Handlers list: %s" % list(self.handlers.values()))

    def add_navbar_entry(self, title, url, icon="question"):
        if title in self.navbar_items:
            return False
        self.logger.debug("Adding navbar entry: %s -> %s" % (title, url))
        self.navbar_items[title] = {"url": url, "active": False, "icon": icon}
        return True

    def check_permission(self, perm, session=None):
        if session is None:
            username = None
        elif isinstance(session, str) or isinstance(session, unicode):
            username = session
        else:
            username = session["username"]

        return self.commands.perm_handler.check(
            perm, username, "web", "plugin-web"
        )

    def remove_api_handlers(self, *names, **kwargs):
        """
        :param names:
        :param version:
        :return:
        """

        version = kwargs.get("version", 1)
        patterns = []

        for pattern in names:
            if not pattern.startswith("/"):
                pattern = "/%s" % pattern
            pattern = "/api/v%s/([A-Za-z0-9]+)%s" % (version, pattern)

            patterns.append(pattern)

        return self.remove_handlers(*patterns)

    def remove_handlers(self, *names):
        found = False

        for name in names:
            if name in self.handlers:
                found = True
                del self.handlers[name]

        if found:
            self.restart()

    def write_api_log(self, address, key, username, message):
        self.api_log.write(
            "%s | %s (%s) | %s\n" % (address, key, username, message)
        )
