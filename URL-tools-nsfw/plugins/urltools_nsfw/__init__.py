# coding=utf-8
import system.plugin as plugin

from system.storage.formats import YAML

from plugins.urls import Priority

from plugins.urltools_nsfw.exceptions import ApiKeyMissing
from plugins.urltools_nsfw.handlers.flist import flist

__author__ = 'Gareth Coles'


class URLToolNSFWPlugin(plugin.PluginObject):
    @property
    def urls(self):
        """
        :rtype: plugins.urls.URLsPlugin
        """

        return self.plugins.get_plugin("URLs")

    def setup(self):
        try:
            self.config = self.storage.get_file(
                self, "config", YAML, "plugins/urltools-nsfw.yml"
            )
        except Exception:
            self.logger.exception("Unable to load the configuration!")
            self._disable_self()
            return

        reload(flist)

        self.handlers = {
            "f-list": (flist.FListHandler, Priority.EARLY),
        }

        self.shorteners = {

        }

        self._load()
        self.config.add_callback(self._reload)

    def _reload(self):
        self._unload()
        self._load()

    def _load(self):
        for handler in self.config.get("handlers", []):
            try:
                if handler in self.handlers:
                    h = self.handlers[handler]
                    self.urls.add_handler(h[0](self), h[1])
            except ApiKeyMissing:
                self.logger.error(
                    "Unable to load handler {}: Missing required API "
                    "key or login details".format(handler)
                )
            except Exception:
                self.logger.exception(
                    "Unable to load handler {}".format(handler)
                )

        for shortener in self.config.get("shorteners", []):
            try:
                if shortener in self.shorteners:
                    s = self.shorteners[shortener]
                    self.urls.add_shortener(s(self))

            except ApiKeyMissing:
                self.logger.error(
                    "Unable to load shortener {}: Missing required API "
                    "key or login details".format(shortener)
                )
            except Exception:
                self.logger.exception(
                    "Unable to load shortener {}".format(shortener)
                )

    def _unload(self):
        for shortener in self.shorteners.iterkeys():
            self.urls.remove_shortener(shortener)

        for handler in self.handlers.itervalues():
            self.urls.remove_handler(handler[0].name)

    def deactivate(self):
        self._unload()
