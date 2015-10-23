# coding=utf-8
import json
import locale
import urllib2
import urlparse

import system.plugin as plugin

from system.plugins.manager import PluginManager
from system.storage.formats import YAML
from system.storage.manager import StorageManager

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

# Attempt to guess the locale.
locale.setlocale(locale.LC_ALL, "")


class URLToolsPlugin(plugin.PluginObject):

    YOUTUBE_LOGO = "YouTube"  # Separated for colouring
    OUTPUT_YOUTUBE_VIDEO = "[" + YOUTUBE_LOGO + " Video] %s (%s) by %s, %s l" \
                                                "ikes, %s dislikes, %s views"
    OUTPUT_YOUTUBE_PLAYLIST = "[" + YOUTUBE_LOGO + " Playlist] %s (%s videos" \
                                                   ", total %s) by %s - \"%s\""
    OUTPUT_YOUTUBE_CHANNEL = "[" + YOUTUBE_LOGO + " Channel] %s (%s subscrib" \
                                                  "ers, %s videos with %s to" \
                                                  "tal views) - \"%s\""
    # PEP MOTHERFUCKING 8 ^

    YOUTUBE_DESCRIPTION_LENGTH = 75

    @property
    def urls(self):
        """
        :rtype: plugins.urls.URLsPlugin
        """

        return self.plugman.get_plugin("URLs")

    def setup(self):
        self.storage = StorageManager()

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

        self.plugman = PluginManager()

        self._load()
        self.config.add_callback(self._load)

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

    def deactivate(self):
        for shortener in self.shorteners.iterkeys():
            self.urls.remove_shortener(shortener)

        for handler in self.handlers.itervalues():
            self.urls.remove_handler(handler)
