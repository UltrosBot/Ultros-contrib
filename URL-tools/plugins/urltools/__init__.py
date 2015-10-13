# coding=utf-8
import json
import urlparse

import locale
import urllib2

import system.plugin as plugin

from system.plugins.manager import PluginManager
from system.storage.formats import YAML
from system.storage.manager import StorageManager

from plugins.urls import Priority

import handlers.github as github
import handlers.osu.osu as osu
import handlers.youtube as youtube

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

        self.handlers = {
            "github": (github.GithubError, Priority.EARLY),
            "osu": (osu.OsuHandler, Priority.EARLY),
            "youtube": (youtube.YoutubeHandler, Priority.EARLY)
        }

        self.shorteners = {

        }

        self.plugman = PluginManager()

        self._load()
        self.config.add_callback(self._load)

        # TODO: Make handlers etc optional
        self.urls.add_handler(github.GithubHandler(self), Priority.EARLY)

    def _load(self):
        for handler in self.config.get("handlers", []):
            if handler in self.handlers:
                h = self.handlers[handler]
                self.urls.add_handler(h[0](self), h[1])

        for shortener in self.config.get("shorteners", []):
            if shortener in self.shorteners:
                pass  # TODO

    def deactivate(self):
        for shortener in self.shorteners.iterkeys():
            self.urls.remove_shortener(shortener)

        for handler in self.handlers.itervalues():
            self.urls.remove_handler(handler)

    def site_youtube(self, url):
        parsed = urlparse.urlparse(url)
        if parsed.path.lower() == "/watch":
            params = urlparse.parse_qs(parsed.query)
            if "v" in params and len(params["v"]) > 0:
                try:
                    video_data = json.loads(urllib2.urlopen(
                        "http://gdata.youtube.com/feeds/api/videos/%s?v=2&alt="
                        "json" % params["v"][0]).read())
                    entry = video_data["entry"]
                    media_group = entry["media$group"]
                    title = media_group["media$title"]["$t"]
                    uploader = media_group["media$credit"][0]["yt$display"]
                    time = self.seconds_to_time(int(
                        media_group["yt$duration"]["seconds"]))
                    views = entry["yt$statistics"]["viewCount"]
                    views = locale.format("%d", long(views), grouping=True)
                    likes = entry["yt$rating"]["numLikes"]
                    likes = locale.format("%d", long(likes), grouping=True)
                    dislikes = entry["yt$rating"]["numDislikes"]
                    dislikes = locale.format("%d", long(dislikes),
                                             grouping=True)
                    return self.OUTPUT_YOUTUBE_VIDEO % (title,
                                                        time,
                                                        uploader,
                                                        likes,
                                                        dislikes,
                                                        views)
                except:
                    self.logger.exception('Could not get title for "%s"' % url)
        elif parsed.path.lower() == "/playlist":
            params = urlparse.parse_qs(parsed.query)
            if "list" in params and len(params["list"]) > 0:
                try:
                    playlist_data = json.loads(urllib2.urlopen(
                        "http://gdata.youtube.com/feeds/api/playlists/%s?v=2&a"
                        "lt=json" % params["list"][0]).read())
                    feed = playlist_data["feed"]
                    title = feed["title"]["$t"]
                    author = feed["author"][0]["name"]["$t"]
                    description = feed["subtitle"]["$t"]
                    description = self.make_description_nice(
                        description,
                        self.YOUTUBE_DESCRIPTION_LENGTH)
                    count = len(feed["entry"])
                    seconds = 0
                    for entry in feed["entry"]:
                        seconds += int(entry["media$group"]["yt$duration"]
                                            ["seconds"])
                    time = self.seconds_to_time(seconds)
                    return self.OUTPUT_YOUTUBE_PLAYLIST % (title,
                                                           count,
                                                           time,
                                                           author,
                                                           description)
                except:
                    self.logger.exception('Could not get title for "%s"' % url)
        elif parsed.path.lower().startswith("/user/"):
            parts = parsed.path.split("/")
            if len(parts) >= 3:
                try:
                    user_data = json.loads(urllib2.urlopen(
                        "http://gdata.youtube.com/feeds/api/users/%s?v=2&alt=j"
                        "son" % parts[2]).read())
                    entry = user_data["entry"]
                    name = entry["title"]["$t"]
                    description = entry["summary"]["$t"]
                    description = self.make_description_nice(
                        description,
                        self.YOUTUBE_DESCRIPTION_LENGTH)
                    subscribers = entry["yt$statistics"]["subscriberCount"]
                    views = entry["yt$statistics"]["totalUploadViews"]
                    videos = None
                    for entry in entry["gd$feedLink"]:
                        if entry["rel"].endswith("#user.uploads"):
                            videos = entry["countHint"]
                            break
                    return self.OUTPUT_YOUTUBE_CHANNEL % (name,
                                                          subscribers,
                                                          videos,
                                                          views,
                                                          description)
                except:
                    self.logger.exception('Could not get title for "%s"' % url)
        # If we get to here, then it's either a part of youtube we don't
        # handle, or an exception was thrown (and caught) above, so let the
        # regular title fetcher try.
        return None

    def seconds_to_time(self, secs):
        # TODO: Move this into formatting utils
        # There's probably a more "pythonic" way to do this, but I didn't know
        # of one
        m, s = divmod(secs, 60)
        if m >= 60:
            h, m = divmod(m, 60)
            return "%d:%02d:%02d" % (h, m, s)
        else:
            return "%d:%02d" % (m, s)

    def make_description_nice(self, description, max_length=-1):
        """
        Replace newlines with spaces and limit length
        """
        # TODO: Move this into formatting utils
        description = description.strip()
        description = description.replace("\r\n", " ").replace("\r", " ") \
            .replace("\n", " ")
        if 0 < max_length < len(description):
            description = description[:max_length - 3] + "..."
        return description
