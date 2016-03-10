# coding=utf-8
import importlib

from plugins.lua.loader import LuaPluginLoader
from system.plugins.plugin import PluginObject

"""
A plugin that provides a loader for working with Lua plugins
"""

__all__ = ["LuaPlugin"]


class LuaPlugin(PluginObject):
    """
    Lua loader plugin.

    Allows loading other plugins written in Lua.
    """

    loader = None

    def setup(self):
        """
        Called when the plugin is loaded. Performs initial setup.
        """

        self.loader = LuaPluginLoader(self.factory_manager, self.plugins)
        self.plugins.add_loader(self.loader)

    def deactivate(self):
        self.plugins.remove_loader(self.loader.name)

