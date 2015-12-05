# coding=utf-8

from system.decorators.ratelimit import RateLimiter
from system.plugins.plugin import PluginObject
from system.storage.formats import YAML

from plugins.items.types import json_type
from plugins.items.types import sqlite_type


__author__ = "Gareth Coles"
__all__ = ["ItemsPlugin"]


class ItemsPlugin(PluginObject):

    config = None
    data = None

    handler = None

    @property
    def storage_type(self):
        if self.config["storage"].lower() == "json":
            return "json"
        return "sqlite"

    def setup(self):
        self.logger.trace("Entered setup method.")

        try:
            self.config = self.storage.get_file(self, "config", YAML,
                                                "plugins/items.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            self.logger.warn("Defaulting to SQLite for storage.")
        else:
            if not self.config.exists:
                self.logger.warn("Unable to find config/plugins/items.yml")
                self.logger.warn("Defaulting to SQLite for storage.")
            else:
                self.logger.info("Using storage type: %s" % self.storage_type)

        self._load()
        self.config.add_callback(self._load)

        self.commands.register_command("give", self.give_command, self,
                                       "items.give", default=True)
        self.commands.register_command("get", self.get_command, self,
                                       "items.get", default=True)
        self.commands.register_command("items", self.count_command, self,
                                       "items.count", default=True)

    def _load(self):
        reload(json_type)
        reload(sqlite_type)

        if self.storage_type == "json":
            self.handler = json_type.Type(self, self.storage, self.logger)
        else:
            self.handler = sqlite_type.Type(
                self, self.storage, self.logger
            )

    def deactivate(self):
        del self.handler

    @RateLimiter(5, 0, 10)  # TODO: Real command rate limiter
    def give_command(self, *args, **kwargs):
        return self.handler.give_command(*args, **kwargs)

    @RateLimiter(5, 0, 10)  # TODO: Real command rate limiter
    def get_command(self, *args, **kwargs):
        return self.handler.get_command(*args, **kwargs)

    @RateLimiter(5, 0, 10)  # TODO: Real command rate limiter
    def count_command(self, *args, **kwargs):
        return self.handler.count_command(*args, **kwargs)
