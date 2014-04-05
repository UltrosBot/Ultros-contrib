# coding=utf-8
import json
import urlparse
from system.plugin_manager import YamlPluginManagerSingleton

__author__ = 'Gareth Coles'

import locale
import logging
import urllib
import urllib2

from system.plugin import PluginObject
from utils.config import YamlConfig
from utils.misc import output_exception

# Attempt to guess the locale.
locale.setlocale(locale.LC_ALL, "")


class Plugin(PluginObject):

    config = None
    api_details = {}

    sites = {}
    shorteners = {}

    plugman = None

    YOUTUBE_LOGO = "YOUTUBE"  # Separated for colouring
    OUTPUT_YOUTUBE_VIDEO = "[" + YOUTUBE_LOGO + " Video] %s (%s) by %s, %s l" \
                                                "ikes, %s dislikes, %s views"
    OUTPUT_YOUTUBE_PLAYLIST = "[" + YOUTUBE_LOGO + " Playlist] %s (%s videos" \
                                                   ", total %s) by %s - \"%s\""
    OUTPUT_YOUTUBE_CHANNEL = "[" + YOUTUBE_LOGO + " Channel] %s (%s subscrib" \
                                                  "ers, %s videos with %s to" \
                                                  "tal views) - \"%s\""
    # PEP MOTHERFUCKING 8 ^

    YOUTUBE_DESCRIPTION_LENGTH = 75

    def setup(self):
        try:
            self.config = YamlConfig("plugins/urltools.yml")
        except Exception:
            self.logger.error("Unable to load the configuration!")
            output_exception(self.logger, logging.ERROR)
            self._disable_self()
            return

        self.sites["osu.ppy.sh"] = self.site_osu
        self.sites["youtube.com"] = self.site_youtube

        self.shorteners["is.gd"] = self.shortener_isgd
        self.shorteners["nazr.in"] = self.shortener_nazrin
        self.shorteners["v.gd"] = self.shortener_vgd
        self.shorteners["waa.ai"] = self.shortener_waaai

        self.plugman = YamlPluginManagerSingleton()

        shorteners = self.config["shorteners"]
        sites = self.config["sites"]

        sites_enabled = []
        shorteners_enabled = []

        for site in sites["enabled"]:
            if site.lower() == "osu.ppy.sh":
                if not sites["apikeys"]["osu"]:
                    self.logger.warn("Osu! support enabled, but no API key was"
                                     " configured. You'll need to add one if "
                                     "you want Osu! support.")
                    continue
            sites_enabled.append(site)
        self.logger.info("Enabled support for %s sites."
                         % len(sites_enabled))

        for shortener in shorteners["enabled"]:
            # This is for checking API keys and settings
            shorteners_enabled.append(shortener)

        self.logger.debug("Setting up shorteners with the URLs plugin..")

        urls = self.plugman.getPluginByName("URLs")

        for site in sites_enabled:
            urls.plugin_object.add_handler(site, self.sites[site])

        self.logger.info("Enabled support for %s site(s)."
                         % len(sites_enabled))

        for shortener in shorteners_enabled:
            urls.plugin_object.add_shortener(shortener,
                                             self.shorteners[shortener])

        self.logger.info("Enabled support for %s shortener(s)."
                         % len(shorteners_enabled))

    def do_get(self, url, params):
        query_string = urllib.urlencode(params)
        constructed = url + "?" + query_string
        self.logger.debug("Constructed GET: %s" % constructed)
        r = urllib2.urlopen(constructed)
        data = r.read()
        self.logger.debug("Response: %s" % data)
        return data

    def do_post(self, url, params, header=None):
        if not header:
            header = {}
        request = urllib2.Request(url, params, header)
        self.logger.debug("Constructed POST: %s | %s" % (url, params))
        r = urllib2.urlopen(request)
        data = r.read()
        self.logger.debug("Response: %s" % data)
        return data

    def shortener_isgd(self, url):
        # Domain: is.gd
        # URL: /create.php
        # Params: url, format=simple
        # Response: Text, shortened URL

        params = {"url": url, "format": "simple"}

        data = self.do_get("http://is.gd/create.php", params)

        return data

    def shortener_nazrin(self, url):
        # Domain: nazr.in
        # URL: /api/shorten
        # Params: url
        # Response: Text, shortened URL

        params = {"url": url}

        data = self.do_get("http://nazr.in/api/shorten", params)

        return data

    def shortener_vgd(self, url):
        # Domain: v.gd
        # URL: /create.php
        # Params: url, format=simple
        # Response: Text, shortened URL

        params = {"url": url, "format": "simple"}

        data = self.do_get("http://v.gd/create.php", params)

        return data

    def shortener_waaai(self, url):
        # Domain: api.waa.ai
        # URL: /
        # Params: url
        # Response: Text, shortened URL

        params = {"url": url}

        data = self.do_get("http://api.waa.ai/", params)

        return data

    def site_osu(self, url):
        return url

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
