# coding=utf-8
import os

from plugins.lua.lua_plugin import LuaWrapperPlugin
from system.enums import PluginState
from system.plugins.loaders.base import BasePluginLoader
from twisted.internet.defer import inlineCallbacks, Deferred, returnValue

__all__ = ["LuaPluginLoader"]


class LuaPluginLoader(BasePluginLoader):
    logger_name = "LuaLoader"
    name = "lua"

    @inlineCallbacks
    def load_plugin(self, info):
        # Find the module file
        module = info.get_module()

        filenames = [
            "{}/__init__.lua",
            "{}/init.lua",
        ]

        for filename in filenames:
            filename = filename.format(module.replace(".", "/"))
            if os.path.isfile(filename):
                break
        else:
            self.logger.error(
                "Unable to find __init__.lua for plugin: {}".format(
                    info.name
                )
            )
            returnValue((PluginState.LoadError, None))
            return  # Keep static analysis happy

        # Instantiate the plugin
        try:
            plugin = LuaWrapperPlugin(filename, info, self)
        except Exception:
            self.logger.exception(
                "Error loading plugin: {}".format(info.name)
            )

            returnValue((PluginState.LoadError, None))
            return  # Keep static analysis happy

        # Set up the plugin
        try:
            info.set_plugin_object(plugin)

            d = plugin.setup()

            if isinstance(d, Deferred):
                _ = yield d
        except Exception:
            self.logger.exception("Error setting up plugin: {}".format(
                info.name
            ))
            returnValue((PluginState.LoadError, None))
        else:
            returnValue((PluginState.Loaded, plugin))

    def can_load_plugin(self, info):
        return info.type == "lua"

