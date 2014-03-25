# coding=utf-8
__author__ = 'Gareth Coles'

import logging
import os
import sys
import webassets

from bottle import default_app, request, hook, abort, static_file
from bottle import mako_template as template

from .events import ServerStartedEvent, ServerStoppedEvent, ServerStoppingEvent

from system.decorators import run_async_daemon
from system.event_manager import EventManager
from system.plugin import PluginObject
from utils.config import YamlConfig
from utils.packages import packages


class BottlePlugin(PluginObject):

    app = None
    host = "127.0.0.1"
    port = 8080
    output_requests = True

    api_routes_list = []
    navbar_items = {}
    additional_headers = []

    config = None
    env = None

    packs = None
    events = None

    # region Internal

    def setup(self):
        self.logger.debug("Entered setup method.")
        try:
            self.config = YamlConfig("plugins/web.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            self.logger.warn("Using the default configuration --> "
                             "http://127.0.0.1:8080")
        else:
            if not self.config.exists:
                self.logger.error("Unable to find config/plugins/web.yml")
                self.logger.warn("Using the default configuration --> "
                                 "http://127.0.0.1:8080")
            else:
                self.host = self.config["hostname"]
                self.port = self.config["port"]
                self.output_requests = self.config["output_requests"]

        self.packs = packages.Packages()

        base_path = "web/static"

        self.logger.info("Compiling and minifying Javascript and CSS..")
        self.env = webassets.Environment(base_path, "/static")
        self.env.debug = "--debug" in sys.argv
        if "--debug" in sys.argv:
            self.logger.warn("Environment is in debug mode, no compilation "
                             "will be done.")

        css = []
        js = []

        assets = os.listdir(base_path)
        for asset in assets:
            if asset.endswith(".css"):
                css.append(asset)
            elif asset.endswith(".js"):
                js.append(asset)

        if js:
            self.logger.info("Optimizing and compiling %s JavaScript files."
                             % len(js))
            js_bundle = webassets.Bundle(*js, filters="rjsmin",
                                         output="generated/packed.js")

            self.env.register("js", js_bundle)

            for url in self.env["js"].urls():
                self._add_javascript(url)
        else:
            self.logger.info("No JavaScript files were found. Nothing to do.")

        if css:
            self.logger.info("Optimizing and compiling %s CSS files."
                             % len(css))
            css_bundle = webassets.Bundle(*css, filters=["cssrewrite",
                                                         "cssmin"],
                                          output="generated/packed.css")

            self.env.register("css", css_bundle)

            for url in self.env["css"].urls():
                self._add_stylesheet(url)
        else:
            self.logger.info("No CSS files were found. Nothing to do.")

        self.app = default_app()
        self.events = EventManager()

        @hook('after_request')
        def log_all():
            ip = request.remote_addr
            method = request.method
            fullpath = request.fullpath

            level = logging.INFO if self.output_requests else logging.DEBUG

            self.logger.log(level, "[%s] %s %s" % (ip, method, fullpath))

        self.logger.info("Starting Bottle app..")
        if self._start_bottle():
            self.app.route("/static/<path:path>", ["GET", "POST"], self.static)
            self.app.route("/static/", ["GET", "POST"], self.static_403)
            self.app.route("/static", ["GET", "POST"], self.static_403)

            self.app.route("/", ["GET", "POST"], self.index)
            self.app.route("/index", ["GET", "POST"], self.index)

            self.add_navbar_entry("Home", "/")

    def deactivate(self):
        if self.app:
            event = ServerStoppingEvent(self, self.app)
            self.events.run_callback("Web/ServerStopping", event)

            self.app.close()
            del self.app
            self.app = None

            event = ServerStoppedEvent(self)
            self.events.run_callback("Web/ServerStopped", event)
        super(PluginObject, self).deactivate()

    @run_async_daemon
    def _start_bottle(self):
        try:
            self.app.run(host=self.host, port=self.port, server='cherrypy',
                         quiet=True)

            event = ServerStartedEvent(self, self.app)
            self.events.run_callback("Web/ServerStartedEvent", event)
            return True
        except Exception:
            self.logger.exception("Exception while running the Bottle app!")
            return False

    def _log_request(self, rq, level=logging.DEBUG):
        ip = rq.remote_addr
        self.logger.log("[%s] %s %s" % (ip, request.method, request.fullpath),
                        level)

    def _add_stylesheet(self, path):
        header = '<link rel="stylesheet" href="%s" />' % path
        self.add_header(header)

    def _add_javascript(self, path):
        header = '<script src="%s"></script>' % path
        self.add_header(header)

    # endregion

    # region Public API functions

    def add_navbar_entry(self, title, url):
        if title in self.navbar_items:
            return False
        self.logger.debug("Adding navbar entry: %s -> %s" % (title, url))
        self.navbar_items[title] = {"url": url, "active": False}
        return True

    def add_header(self, header):
        self.logger.debug("Adding header: %s" % header)
        self.additional_headers.append(header)

    def add_route(self, path, *args, **kwargs):
        if path in self.api_routes_list:
            return False
        self.api_routes_list.append(path)

        self.logger.debug("Adding route: %s" % path)
        self.app.route(path, *args, **kwargs)

        return True

    # endregion

    # region Routes

    def index(self):
        nav_items = self.navbar_items
        nav_items["Home"]["active"] = True
        return template("web/templates/index.html",
                        nav_items=nav_items,
                        headers=self.additional_headers,
                        packages=self.packs.get_installed_packages(),
                        plugins=self.factory_manager.loaded_plugins.values(),
                        factories=self.factory_manager.factories)

    def static(self, path):
        return static_file(path, root="web/static")

    def static_403(self):
        abort(403, "You may not list the static files.")

    # endregion

    pass  # So the regions work in PyCharm
