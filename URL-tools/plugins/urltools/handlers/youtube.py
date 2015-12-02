# coding=utf-8
import re
import isodate
from twisted.internet.defer import Deferred
from txrequests import Session
from plugins.urls.constants import CASCADE, STOP_HANDLING

from plugins.urls.handlers.handler import URLHandler
from plugins.urltools import ApiKeyMissing

__author__ = 'Sean'
__all__ = ["YoutubeHandler", "YoutubeAPIError"]

class YoutubeAPIError(Exception):

    def __init__(self, message, code, errors, *args, **kwargs):
        self.errors = errors
        message_parts = []
        for error in errors:
            message_parts.append(
                u'Domain: "{domain}", Reason: "{reason}", Message "{message}"'
                    .format(**error)
            )
        full_message = u"%s %s [%s]" % (message, code,
                                        u" | ".join(message_parts))
        super(YoutubeAPIError, self).__init__(full_message, *args, **kwargs)


class YoutubeHandler(URLHandler):
    name = "youtube"

    criteria = {
        "protocol": re.compile(r"http|https", re.I),
        "domain": re.compile(r"(www\.)?(youtube\.com|youtu\.be)", re.I),
    }

    VIDEO_LINK, CHANNEL_LINK, PLAYLIST_LINK = xrange(3)

    BASE_URL = "https://www.googleapis.com/youtube/v3/"
    VIDEOS_URL = BASE_URL + "videos"
    CHANNELS_URL = BASE_URL + "channels"
    PLAYLISTS_URL = BASE_URL + "playlists"

    DEFAULT_FORMATS = {
        "video": u'[YouTube Video] "{title}" by {channel} - {description} - '
                 u'length {duration_formatted} - rated {rating_percent:.0f}%'
                 u' - {views} views',
        "channel": u'[YouTube Channel] {title} - {description} - {videos} '
                   u'videos - {subscribers} subscribers - {views} views',
        "playlist": u'[YouTube Playlist] "{title}" by {channel} - '
                    u'{description} - {videos} videos',
    }

    def __init__(self, *args, **kwargs):
        super(YoutubeHandler, self).__init__(*args, **kwargs)

        if not self.api_key:
            raise ApiKeyMissing()

        self.session = Session()

    @property
    def api_key(self):
        return self.plugin.config.get("youtube", {}).get("api_key", "")

    @property
    def api_key_referrer(self):
        youtube_conf = self.plugin.config.get("youtube", {})
        return youtube_conf.get("api_key_referrer", "")

    @property
    def description_length(self):
        youtube_conf = self.plugin.config.get("youtube", {})
        return youtube_conf.get("description_length", 75)

    def get_format_string(self, key):
        youtube_conf = self.plugin.config.get("youtube", {})
        format_conf = youtube_conf.get("formatting", {})

        if key not in format_conf:
            return self.DEFAULT_FORMATS[key]
        return format_conf[key]

    def call(self, url, context):
        domain = url.domain.lower()
        if domain.startswith(u"www."):
            domain = domain[4:]

        if domain == u"youtu.be":
            link_type, data = self._parse_youtu_be(url)
        else:
            link_type, data = self._parse_youtube_com(url)

        if link_type == self.VIDEO_LINK:
            self.handle_video(data, context)
            return STOP_HANDLING
        elif link_type == self.CHANNEL_LINK:
            self.handle_channel(data, context)
            return STOP_HANDLING
        elif link_type == self.PLAYLIST_LINK:
            self.handle_playlist(data, context)
            return STOP_HANDLING
        else:
            return CASCADE

    def _parse_youtu_be(self, url):
        return self.VIDEO_LINK, url.path.strip("/")

    def _parse_youtube_com(self, url):
        # Video: https://www.youtube.com/watch?v=orvJo3nNZuI
        # Channel:
        #  Username:   https://www.youtube.com/user/Mtvnoob
        #  Channel ID: https://www.youtube.com/channel/UCmkoMt2VCc3TaFSE5MKrkpQ
        # Playlist: https://www.youtube.com/playlist?list=PLE6Wd9FR--EfW8dtjAuPoTuPcqmOV53Fu  # noqa
        try:
            path_split = url.path.strip("/").split("/")
            root_path = path_split[0]
            if root_path == u"watch":
                return self.VIDEO_LINK, url.query["v"]
            elif root_path == u"user":
                return self.CHANNEL_LINK, {u"username": path_split[1]}
            elif root_path == u"channel":
                return self.CHANNEL_LINK, {u"channel_id": path_split[1]}
            elif root_path == u"playlist":
                return self.PLAYLIST_LINK, url.query[u"list"]
        except Exception:
            self.plugin.logger.exception("Error parsing youtube.com URL")
        return None, None

    def _get(self, url, params, **kwargs):
        referrer = self.api_key_referrer
        if referrer:
            headers = {"referer": referrer}
            if "headers" in kwargs:
                headers.update(kwargs["headers"])
            kwargs["headers"] = headers
        params["key"] = self.api_key
        return self.session.get(url, params=params, **kwargs)

    def handle_video(self, video_id, context):
        req_def = self._get(self.VIDEOS_URL, params={
            "part": "snippet,contentDetails,statistics",
            "id": video_id,
        })
        return self._add_callbacks(self._handle_video_response,
                                   self._handle_request_failure,
                                   context, req_def)

    def handle_channel(self, data, context):
        params = {
            "part": "snippet,statistics",
        }
        if "channel_id" in data:
            params["id"] = data["channel_id"]
        elif "username" in data:
            params["forUsername"] = data["username"]
        else:
            raise ValueError("Must specify channel_id or username")
        req_def = self._get(self.CHANNELS_URL, params=params)
        return self._add_callbacks(self._handle_channel_response,
                                   self._handle_request_failure,
                                   context, req_def)

    def handle_playlist(self, playlist_id, context):
        req_def = self._get(self.PLAYLISTS_URL, params={
            "part": "snippet,contentDetails",
            "id": playlist_id,
        })
        return self._add_callbacks(self._handle_playlist_response,
                                   self._handle_request_failure,
                                   context, req_def)

    def _add_callbacks(self, callback, errback, context, req_def):
        result_def = Deferred()
        req_def.addCallback(callback, context, result_def)
        req_def.addErrback(errback, context, result_def)
        return result_def

    def _handle_video_response(self, response, context, result_def):
        data = response.json()

        items = self._get_items(data)

        content_details = items["contentDetails"]
        snippet = items["snippet"]
        statistics = items["statistics"]

        description = snippet["description"].strip()
        if len(description) == 0:
            description = "No description"
        description_snippet = self.snip_description(description)
        duration = isodate.parse_duration(content_details["duration"])
        likes_count = int(statistics["likeCount"])
        dislike_count = int(statistics["dislikeCount"])
        ratings_total = likes_count + dislike_count
        rating_percentage = (float(likes_count) / ratings_total) * 100
        tags = snippet.get("tags", [])

        if len(tags) > 0:
            tags_formatted = ", ".join(tags[:5])
        else:
            tags_formatted = "No tags"

        duration_formatted = self.format_time_period(duration)

        format_data = {
            "full_response": data,

            "title": snippet["title"],
            "channel": snippet["channelTitle"],
            "duration": duration,
            "duration_formatted": duration_formatted,
            "description": description_snippet,
            "full_description": description,
            "tags": tags,
            "tags_formatted": tags_formatted,

            "likes": likes_count,
            "dislikes": dislike_count,
            "favourites": int(statistics["favoriteCount"]),
            "views": int(statistics["viewCount"]),
            "comments": int(statistics["commentCount"]),
            "rating_percent": rating_percentage,
            "rating_total": ratings_total
        }

        message = self.get_format_string("video").format(**format_data)
        self._handle_message(message, context)
        result_def.callback(STOP_HANDLING)

    def _handle_channel_response(self, response, context, result_def):
        data = response.json()

        items = self._get_items(data)

        snippet = items["snippet"]
        statistics = items["statistics"]

        description = snippet["description"]
        if len(description) == 0:
            description = "No description"
        description_snippet = self.snip_description(description)
        try:
            # I'm not sure what happens here if hiddenSubscriberCount is true
            subscribers = int(statistics["subscriberCount"])
        except ValueError:
            subscribers = 0
        hidden_subscribers = statistics["hiddenSubscriberCount"]  # noqa
        country = snippet.get("country", "Unknown")

        format_data = {
            "full_response": data,

            "title": snippet["title"],
            "subscribers": subscribers,
            "videos": statistics["videoCount"],
            "views": statistics["viewCount"],
            "comments": statistics["commentCount"],
            "country": country,
            "description": description_snippet,
            "full_description": description,
        }

        message = self.get_format_string("channel").format(**format_data)
        self._handle_message(message, context)
        result_def.callback(STOP_HANDLING)

    def _handle_playlist_response(self, response, context, result_def):
        data = response.json()

        items = self._get_items(data)

        content_details = items["contentDetails"]
        snippet = items["snippet"]

        description = snippet["description"].strip()
        if len(description) == 0:
            description = "No description"
        description_snippet = self.snip_description(description)

        format_data = {
            "full_response": data,

            "title": snippet["title"],
            "channel": snippet["channelTitle"],
            "videos": content_details["itemCount"],
            "description": description_snippet,
            "full_description": description,
        }

        message = self.get_format_string("playlist").format(**format_data)
        self._handle_message(message, context)
        result_def.callback(STOP_HANDLING)

    def _get_items(self, data):
        if "error" in data:
            error = data["error"]
            raise YoutubeAPIError(
                error["message"], error["code"], error["errors"])
        return data["items"][0]

    def _handle_request_failure(self, fail, context, result_def):
        if fail.check(YoutubeAPIError):
            self.plugin.logger.error(fail.getErrorMessage())
        else:
            self.plugin.logger.error(fail.getTraceback())
        result_def.callback(CASCADE)

    def _handle_message(self, message, context):
        context["event"].target.respond(message)

    def reload(self):
        self.teardown()
        self.session = Session()

    def teardown(self):
        if self.session is not None:
            self.session.close()

    def format_time_period(self, duration):
        secs = duration.total_seconds()
        m, s = divmod(secs, 60)
        if m >= 60:
            h, m = divmod(m, 60)
            return "%d:%02d:%02d" % (h, m, s)
        else:
            return "%d:%02d" % (m, s)

    def snip_description(self, description, length=0):
        if not length:
            length = self.description_length
        split = description.strip().split(u"\n")
        desc = split[0].strip()
        if len(desc) > length:
            return desc[:length - 3].strip() + u"..."
        return desc
