# coding=utf-8
import importlib

from lupa import LuaRuntime
from system.plugins.plugin import PluginObject

__all__ = ["LuaWrapperPlugin"]

# TODO: Check how require works - we need to be able to set its base directory
# ^ seems to just be vanilla Lua stuff (package.path/cpath)


class LuaWrapperPlugin(PluginObject):
    def __init__(self, lua_file, *args, **kwargs):
        super(LuaWrapperPlugin, self).__init__(*args, **kwargs)
        self.runtime = LuaRuntime(unpack_returned_tuples=True)

        self.setup_globals()

        base_plugin = self.create_base_plugin()
        with open(lua_file, "r") as fh:
            data = fh.read()
        # Pass base plugin as arg to module
        self.lua_plugin = self.runtime.execute(data, base_plugin)

        # If the module doesn't return anything, use the base plugin reference
        # and assume it modified it anyway.
        if self.lua_plugin is None:
            self.lua_plugin = base_plugin

    def setup_globals(self):
        lua_globals = self.runtime.globals()
        lua_globals["import"] = self.import_python
        lua_globals["print"] = self.print_function

    def create_base_plugin(self):
        """
        Create a base plugin Lua table that other plugins may "sub-class"
        :return:
        """

        # table() and table_from() break the debugger somehow (breakpoints
        # stop working - pydevd.settrace() sometimes fixes it) so just make the
        # table in Lua from the start.
        table = self.runtime.execute("return {}")

        # Reference to self
        table["python_plugin"] = self
        # Basic plugin attributes
        table["info"] = self.info
        table["module"] = self.module
        table["logger"] = self.logger
        table["commands"] = self.commands
        table["events"] = self.events
        table["factory_manager"] = self.factory_manager
        table["plugins"] = self.plugins
        table["storage"] = self.storage
        # Helper methods
        table["import"] = self.import_python

        return table

    def __getattr__(self, item):
        return getattr(self.lua_plugin, item)

    def import_python(self, module, package=None):
        return importlib.import_module(module, package)

    def print_function(self, *args):
        self.logger.info("\t".join(str(arg) for arg in args))

    def _run_from_lua_plugin(self, func_name, *args):
        """
        Helper method to call functions from the Lua plugin, if they exist.
        :param func_name:
        :param args: Args to pass to Lua function
        :return:
        """
        func = getattr(self.lua_plugin, func_name)
        if callable(func):
            return func(*args)
        return None

    def deactivate(self):
        return self._run_from_lua_plugin("deactivate")

    def setup(self):
        return self._run_from_lua_plugin("setup")

    def reload(self):
        return self._run_from_lua_plugin("reload")
