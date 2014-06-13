# coding=utf-8
__author__ = "Gareth Coles"

from system.command_manager import CommandManager
from system.decorators.ratelimit import RateLimiter

import system.plugin as plugin

from system.storage.formats import YAML
from system.storage.manager import StorageManager

from .json_type import Type as JSONType
from .sqlite_type import Type as SQLiteType


class ItemsPlugin(plugin.PluginObject):

    commands = None

    config = None
    data = None
    storage = None

    handler = None

    @property
    def storage_type(self):
        if self.config["storage"].lower() == "json":
            return "json"
        return "sqlite"

    def setup(self):
        self.commands = CommandManager()
        self.storage = StorageManager()

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
                                       "items.give")
        self.commands.register_command("get", self.get_command, self,
                                       "items.get")

    def _load(self):
        if self.storage_type == "json":
            self.handler = JSONType(self, self.storage, self.logger)
        else:
            self.handler = SQLiteType(self, self.storage, self.logger)

    @RateLimiter(5, 0, 10)
    def give_command(self, *args, **kwargs):
        return self.handler.give_command(*args, **kwargs)

    @RateLimiter(5, 0, 10)
    def get_command(self, *args, **kwargs):
        return self.handler.get_command(*args, **kwargs)
