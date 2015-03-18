# coding=utf-8
__author__ = 'Gareth Coles'

import system.plugin as plugin

from system.command_manager import CommandManager
from system.event_manager import EventManager
from system.plugins.manager import PluginManager
from system.storage.manager import StorageManager
from system.storage.formats import YAML


class TwilioPlugin(plugin.PluginObject):

    config = None
    data = None

    commands = None
    events = None
    plugins = None
    storage = None

    @property
    def web(self):
        """
        :rtype: plugins.web.WebPlugin
        """
        return self.plugins.get_plugin("Web")

    def setup(self):
        self.logger.trace("Entered setup method.")

        self.commands = CommandManager()
        self.events = EventManager()
        self.plugins = PluginManager()
        self.storage = StorageManager()

        try:
            self.config = self.storage.get_file(self, "config", YAML,
                                                "plugins/webhooks.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            return self._disable_self()
        else:
            if not self.config.exists:
                self.logger.error("Unable to find config/plugins/webhooks.yml")
                return self._disable_self()

        self._load()
        self.config.add_callback(self._load)

        self.events.add_callback("Web/ServerStartedEvent", self,
                                 self.add_routes,
                                 0)

    def _load(self):
        pass

    def add_routes(self, _=None):
        self.web.add_navbar_entry("Webhooks", "/webhooks", "url")
        self.web.add_handler(
            "/webhooks", "plugins.webhooks.routes.webhooks.Route"
        )
        self.logger.info("Registered route: /webhooks")

    pass  # So the regions work in PyCharm
