# coding=utf-8
__author__ = 'Gareth Coles'

import logging
from bottle import default_app, request, hook, abort, static_file
from bottle import mako_template as template

from system.decorators import run_async_daemon
from system.plugin import PluginObject
from utils.config import Config


class BottlePlugin(PluginObject):

    app = None
    host = "127.0.0.1"
    port = 8080
    output_requests = True

    api_routes_list = []

    config = None

    # region Internal

    def setup(self):
        self.logger.debug("Entered setup method.")
        try:
            self.config = Config("plugins/web.yml")
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

        self.app = default_app()

        # region Hooks and default routes

        @hook('after_request')
        def log_all():
            ip = request.remote_addr
            method = request.method
            fullpath = request.fullpath

            level = logging.INFO if self.output_requests else logging.DEBUG

            self.logger.log(level, "[%s] %s %s" % (ip, method, fullpath))

        self.app.route("/static/<path:path>", ["GET", "POST"], self.static)
        self.app.route("/static/", ["GET", "POST"], self.static_403)
        self.app.route("/static", ["GET", "POST"], self.static_403)
        self.app.route("/", ["GET", "POST"], self.index)
        self.app.route("/index", ["GET", "POST"], self.index)

        # endregion

        self._start_bottle()

    def deactivate(self):
        self.app.close()
        super(PluginObject, self).deactivate()

    @run_async_daemon
    def _start_bottle(self):
        self.logger.info("Starting Bottle app..")
        try:
            self.app.run(host=self.host, port=self.port, server='cherrypy',
                         quiet=True)
        except Exception:
            self.logger.exception("Exception while running the Bottle app!")

    def _log_request(self, rq, level=logging.DEBUG):
        ip = rq.remote_addr
        self.logger.log("[%s] %s %s" % (ip, request.method, request.fullpath),
                        level)

    # endregion

    # region Routes

    def index(self):
        return template("web/templates/index.html")

    def static(self, path):
        return static_file(path, root="web/static")

    def static_403(self):
        abort(403, "You may not list the static files.")

    # endregion

    pass  # So the regions work in PyCharm
