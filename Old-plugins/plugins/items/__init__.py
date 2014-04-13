# coding=utf-8
__author__ = "Gareth Coles"

from system.command_manager import CommandManager
from system.plugin import PluginObject
from system.storage.formats import YAML
from system.storage.manager import StorageManager

from .json_type import Type as JSONType
from .sqlite_type import Type as SQLiteType


class ItemsPlugin(PluginObject):

    commands = None

    config = None
    data = None
    storage = None

    storage_type = "sqlite"
    handler = None

    def setup(self):
        self.commands = CommandManager()
        self.storage = StorageManager()

        self.logger.debug("Entered setup method.")
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
                if self.config["storage"].lower() == "json":
                    self.storage_type = "json"

                self.logger.info("Using storage type: %s" % self.storage_type)

        if self.storage_type == "sqlite":
            self.handler = SQLiteType(self, self.storage, self.logger)
        else:
            self.handler = JSONType(self, self.storage, self.logger)

        self.commands.register_command("give", self.give_command, self,
                                       "items.give")
        self.commands.register_command("get", self.get_command, self,
                                       "items.get")

    def give_command(self, *args, **kwargs):
        return self.handler.give_command(*args, **kwargs)

    def get_command(self, *args, **kwargs):
        return self.handler.get_command(*args, **kwargs)
