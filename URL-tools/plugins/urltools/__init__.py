# coding=utf-8
import system.plugin as plugin

from system.storage.formats import YAML

from plugins.urls import Priority

from plugins.urltools.exceptions import ApiKeyMissing

from plugins.urltools.handlers import github
from plugins.urltools.handlers.osu import osu
from plugins.urltools.handlers import youtube

from plugins.urltools.shorteners import is_gd
from plugins.urltools.shorteners import nazrin
from plugins.urltools.shorteners import v_gd
from plugins.urltools.shorteners import waa_ai

__author__ = 'Gareth Coles'


class URLToolsPlugin(plugin.PluginObject):
    @property
    def urls(self):
        """
        :rtype: plugins.urls.URLsPlugin
        """

        return self.plugins.get_plugin("URLs")

    def setup(self):
        try:
            self.config = self.storage.get_file(
                self, "config", YAML, "plugins/urltools.yml"
            )
        except Exception:
            self.logger.exception("Unable to load the configuration!")
            self._disable_self()
            return

        reload(github)
        reload(osu)
        reload(youtube)

        reload(is_gd)
        reload(nazrin)
        reload(v_gd)
        reload(waa_ai)

        self.handlers = {
            "github": (github.GithubHandler, Priority.EARLY),
            "osu": (osu.OsuHandler, Priority.EARLY),
            "youtube": (youtube.YoutubeHandler, Priority.EARLY)
        }

        self.shorteners = {
            "is.gd": is_gd.IsGdShortener,
            "nazr.in": nazrin.NazrinShortener,
            "v.gd": v_gd.VGdShortener,
            "waa.ai": waa_ai.WaaAiShortener
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
                    "key".format(handler)
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
                    "key".format(shortener)
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
