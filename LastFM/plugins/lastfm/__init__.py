from datetime import datetime

__author__ = 'Sean'

import treq

from lib.crypto import newbase60 as nb60

from system.command_manager import CommandManager

import system.plugin as plugin

from system.storage.formats import YAML
from system.storage.manager import StorageManager


# TODO: Bite the bullet and switch to the XML version
# The JSON API appears to just be the XML one run through a converter, which
# gives some weirdness (like empty lists being strings).


class LastFMPlugin(plugin.PluginObject):

    commands = None
    _config = None
    storage = None

    def setup(self):
        ### Grab important shit
        self.commands = CommandManager()
        self.storage = StorageManager()

        ### Initial config load
        try:
            self._config = self.storage.get_file(self, "config", YAML,
                                                 "plugins/lastfm.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            self.logger.error("Disabling...")
            self._disable_self()
            return
        if not self._config.exists:
            self.logger.error("Unable to find config/plugins/lastfm.yml")
            self.logger.error("Disabling...")
            self._disable_self()
            return
            ### Same for the data file (nickname=>lastfmusername map)
        try:
            self._nickmap = self.storage.get_file(self, "data", YAML,
                                                  "plugins/lastfm-nickmap.yml")
        except Exception:
            self.logger.exception("Error loading nickmap!")
            self.logger.error("Disabling...")
            self._disable_self()

        ### Load options from config and nick map from data
        self._load()

        self._config.add_callback(self._load)

        ### Register commands
        self.commands.register_command("nowplaying",
                                       self.nowplaying_cmd,
                                       self,
                                       "lastfm.nowplaying",
                                       aliases=["np"],
                                       default=True)
        self.commands.register_command("lastfmnick",
                                       self.lastfmnick_cmd,
                                       self,
                                       "lastfm.lastfmnick",
                                       default=True)
        self.commands.register_command("lastfmcompare",
                                       self.compare_cmd,
                                       self,
                                       "lastfm.compare",
                                       aliases=["musiccompare", "compare"],
                                       default=True)

    def reload(self):
        try:
            self._config.reload()
            self._nickmap.reload()
        except Exception:
            self.logger.exception("Error reloading configuration!")
            return False
        self._load()
        return True

    def _load(self):
        self.api = LastFM(self._apikey)

    @property
    def _apikey(self):
        return self._config["apikey"]

    @property
    def _recent_play_limit(self):
        # Allow for old configs without this setting
        if "recent_play_limit" in self._config:
            return self._config["recent_play_limit"]
        else:
            return 300  # 5 minutes in seconds

    def _get_username(self, user, none_if_unset=False):
        user = user.lower()
        try:
            return self._nickmap[user]
        except KeyError:
            if none_if_unset:
                return None
            else:
                return user

    def _set_username(self, user, lastfm_user):
        with self._nickmap:
            self._nickmap[user.lower()] = lastfm_user

    def _respond(self, target, msg):
        """
        Convenience function for responding to something with a prefix. Not
        only does this avoid confusion, but it also stops people being able to
        execute other bot commands in the case that we need to put any
        user-supplied data at the start of a message.
        """
        target.respond("LastFM: " + msg)

    def lastfmnick_cmd(self, protocol, caller, source, command, raw_args,
                       parsed_args):
        args = raw_args.split()  # Quick fix for new command handler signature
        if len(args) == 0:
            username = self._get_username(caller.nickname, True)
            if username is None:
                caller.respond("You have no stored username")
            else:
                caller.respond("Your stored username is %s" % username)
        elif len(args) == 1:
            self._set_username(caller.nickname, args[0])
            caller.respond("Your stored username has been updated")
        else:
            caller.respond("Usage: {CHARS}lastfmnick [lastfm username]")

    def nowplaying_cmd(self, protocol, caller, source, command, raw_args,
                       parsed_args):
        self.logger.trace("Entering nowplaying_cmd()")
        args = raw_args.split()  # Quick fix for new command handler signature
        ### Get LastFM username to use
        username = None
        if len(args) == 0:
            username = self._get_username(caller.nickname)
        elif len(args) == 1:
            username = self._get_username(args[0])
        else:
            caller.respond("Usage: {CHARS}nowplaying [lastfm username]")
            return

        ### Query LastFM for user's most recent track
        deferred = self.api.user_get_recent_tracks(username, limit=1)
        deferred.addCallbacks(
            lambda r: self._nowplaying_cmd_recent_tracks_result(caller,
                                                                source,
                                                                username,
                                                                r),
            lambda f: self._nowplaying_cmd_error(caller, f)
        )

    def compare_cmd(self, protocol, caller, source, command, raw_args,
                    parsed_args):
        self.logger.trace("Entering compare_cmd()")
        args = raw_args.split()  # Quick fix for new command handler signature
        ### Get LastFM username to use
        username_one = None
        username_two = None
        if len(args) == 1:
            username_one = self._get_username(caller.nickname)
            username_two = self._get_username(args[0])
        elif len(args) == 2:
            username_one = self._get_username(args[0])
            username_two = self._get_username(args[1])
        else:
            caller.respond(
                "Usage: {CHARS}%s <lastfm username> [lastfm username]" %
                command)
            return

        ### Query LastFM for user taste comparison
        deferred = self.api.tasteometer_compare(
            "user", username_one, "user", username_two
        )
        deferred.addCallbacks(
            lambda r: self._compare_cmd_tasteometer_result(caller,
                                                           source,
                                                           username_one,
                                                           username_two,
                                                           r),
            lambda f: self._compare_cmd_tasteometer_error(caller, f)
        )

    def _nowplaying_cmd_recent_tracks_result(self, caller, source, username,
                                             result):
        """
        Receives the API response for User.getRecentTracks.
        """
        self.logger.trace("Entering _nowplaying_cmd_recent_tracks_result()")
        # Extract track info
        try:
            tracks = result["recenttracks"]["track"]
            if len(tracks) == 0:
                # User has never listened to anything - an extreme edge-case,
                # I know, but we should really handle it - (untested)
                self._respond(source,
                              "%s hasn't listened to anything" % username)
                return
            if isinstance(tracks, list):
                track = tracks[0]
            else:
                track = tracks
            # Check if track is currently playing, or was played recently
            now_playing = ("@attr" in track and "nowplaying" in track["@attr"]
                           and bool(track["@attr"]["nowplaying"]))
            just_played = ("date" in track and (
                datetime.utcnow() - datetime.utcfromtimestamp(
                    float(track["date"]["uts"])
                )).seconds <= self._recent_play_limit)
            if now_playing or just_played:
                track_artist = track["artist"]["#text"]
                track_title = track["name"]
                album = ""
                if "album" in track:
                    album = track["album"]["#text"]
                mbid = None
                if "mbid" in track and track["mbid"]:
                    mbid = track["mbid"]
                ### Query LastFM for track info, then finally send info to chan
                deferred = self.api.track_get_info(track_title,
                                                   track_artist,
                                                   mbid,
                                                   username)
                deferred.addCallbacks(
                    lambda r: self._nowplaying_cmd_end_result(caller,
                                                              source,
                                                              username,
                                                              now_playing,
                                                              track_artist,
                                                              track_title,
                                                              album,
                                                              r),
                    # TODO: If error here, just send the basic info?
                    lambda f: self._nowplaying_cmd_error(caller, f)
                )
            else:
                self._respond(source,
                              "%s is not currently listening to anything" %
                              username)
        except:
            self.logger.exception("Please tell the developer about this error")

    def _nowplaying_cmd_end_result(self, caller, source, username, now_playing,
                                   track_artist, track_title, album, result):
        self.logger.trace("Entering _nowplaying_cmd_end_result()")
        try:
            ### Extract track info
            user_loved = False
            user_play_count = 0
            total_play_count = 0
            listener_count = 0
            duration = 0
            url = ""
            tags = []
            track = result["track"]
            # I don't know if any of these may not exist
            if "userloved" in track:
                user_loved = track["userloved"] == "1"
            if "userplaycount" in track:
                user_play_count = int(track["userplaycount"])
            if "playcount" in track:
                total_play_count = int(track["playcount"])
            if "listeners" in track:
                listener_count = int(track["listeners"])
            if "duration" in track:
                duration = int(track["duration"])
            if "url" in track:
                url = track["url"]
            if "id" in track:
                try:
                    fragment = nb60.numtosxg(int(track["id"]))
                    url = "http://last.fm/+t{}".format(fragment)
                except:
                    self.logger.exception(
                        "Error getting short URL; using long one."
                    )

            if "toptags" in track and isinstance(track["toptags"], dict):
                # type check due to an irregularity in the LastFM API: http://
                # www.last.fm/group/Last.fm+Web+Services/forum/21604/_/2231458
                if isinstance(track["toptags"]["tag"], dict):
                    # If the list only contains one item, it gets turned into
                    # a dict, so reverse that shit
                    track["toptags"]["tag"] = [track["toptags"]["tag"]]
                for tag in track["toptags"]["tag"]:
                    # TODO: Make these clickable links for protocols that can?
                    if not isinstance(tag, dict):
                        self.logger.error("Tag isn't a dict!? - %s" % tag)
                        continue
                    tags.append(tag["name"])

            ### Finally, we send the message
            # TODO: This could do with a cleanup
            status_text = u"just listened to"
            if now_playing:
                status_text = u"is now playing"
            output = [u'%s %s: "%s" by %s' % (username,
                                              status_text,
                                              track_title,
                                              track_artist)]
            if album:
                output.append(u" [%s]" % album)
            output.append(u" - ")
            if user_loved:
                output.append(u"\u2665 ")  # Heart
            output.append(u"%s listens by %s, %s listens by %s listeners" % (
                # Localisation support? What's that?
                "{:,}".format(user_play_count),
                username,
                "{:,}".format(total_play_count),
                "{:,}".format(listener_count)
            ))
            if len(tags) > 0:
                output.append(u" - Tags: %s" % u", ".join(tags))
            if url:
                output.append(u" - %s" % url)
            self._respond(source, u"".join(output))
        except:
            self.logger.exception("Please tell the developer about this error")

    def _compare_cmd_tasteometer_result(self, caller, source, username_one,
                                        username_two, response):
        """
        Receives the API response for User.getRecentTracks.
        """
        self.logger.trace("Entering _compare_cmd_tasteometer_result()")
        try:
            ### Extract info
            result = response["comparison"]["result"]
            score = float(result["score"])
            score_percent = score * 100
            # More weird shit caused by using the JSON API... <_<
            artist_count = -1
            if "@attr" in result["artists"]:
                artist_count = int(result["artists"]["@attr"]["matches"])
            else:
                artist_count = int(result["artists"]["matches"])
            artists = []
            if artist_count > 0:
                _json_artists = result["artists"]["artist"]
                if isinstance(_json_artists, dict):
                    _json_artists = [_json_artists]
                for artist in _json_artists:
                    artists.append(artist["name"])

            ### Send the message
            output = [u'%s and %s are %.0f%% compatible.' % (username_one,
                                                             username_two,
                                                             score_percent)]

            if len(artists) > 0:
                output.append(u" Some artists they share: ")
                output.append(u", ".join(artists))

            self._respond(source, u"".join(output))
        except:
            # TODO: Remove this debug dump line
            print __import__("json").dumps(response)
            self.logger.exception("Please tell the developer about this error")

    def _nowplaying_cmd_error(self, caller, failure):
        """
        :type failure: twisted.python.failure.Failure
        """
        # Some errors will be caused by user input
        if failure.check(LastFMError) and failure.value.err_code in (6,):
            self._respond(caller, failure.value.message)
        else:
            self.logger.debug("Error while fetching nowplaying",
                              exc_info=(
                                  failure.type,
                                  failure.value,
                                  failure.tb
                              ))
            caller.respond("There was an error while contacting LastFM - "
                           "please alert a bot admin or try again later")

    def _compare_cmd_tasteometer_error(self, caller, failure):
        """
        :type failure: twisted.python.failure.Failure
        """
        # Some errors will be caused by user input
        if failure.check(LastFMError) and failure.value.err_code in (6, 7):
            self._respond(caller, failure.value.message)
        else:
            self.logger.debug("Error while fetching comparison",
                              exc_info=(
                                  failure.type,
                                  failure.value,
                                  failure.tb
                              ))
            caller.respond("There was an error while contacting LastFM - "
                           "please alert a bot admin or try again later")


class LastFM(object):
    """
    The only module I could find in pypi for this didn't parse the nowplaying
    part of User.getRecentTracks(), and it used the XML API, so I didn't fancy
    forking it. I'll build on this as necessary, and if it gets to the point
    where it has decent coverage of the LastFM API, I'll split it off into its
    own module and stick it on pypi. That's also why it's in this file and not
    in its own - not sure if the package manager can deal with files being
    removed in updates yet.
    """

    API_URL = "http://ws.audioscrobbler.com/2.0/"

    def __init__(self, api_key):
        self._api_key = api_key

    def _handle_response(self, response):
        deferred = response.json()
        deferred.addCallback(self._handle_content)
        return deferred

    def _handle_content(self, result):
        if "error" in result:
            raise LastFMError(result["error"],
                              result["message"],
                              result["links"])
        else:
            return result
        # TODO: This return doesn't seem to actually go anywhere

    def _make_request(self, method, payload):
        """
        Actually make the HTTP request.
        :rtype : twisted.internet.defer.Deferred
        """
        # user.getRecentTracks works
        # user.getrecenttracks works
        # User.getRecentTracks doesn't work, but doesn't error sensibly
        # So fuck that, send it lower() to make sure
        method = method.lower()
        final_payload = {
            "api_key": self._api_key,
            "format": "json",
            "method": method
        }
        final_payload.update(payload)
        # Convert unicode strings to utf8-encoded bytestrings (treq doesn't
        # seem to be able to encode unicode strings properly)
        for k, v in final_payload.iteritems():
            if isinstance(v, unicode):
                final_payload[k] = v.encode("utf8")
        deferred = treq.post(self.API_URL,
                             final_payload,
                             headers={"User-Agent": "Ultros-contrib/LastFM"})
        deferred.addCallback(self._handle_response)
        return deferred

    def user_get_recent_tracks(self, username, limit=None, page=None,
                               from_=None, extended=None, to=None):
        """
        :rtype : twisted.internet.defer.Deferred
        """
        payload = {
            "user": username
        }
        if limit is not None:
            payload["limit"] = limit
        if page is not None:
            payload["page"] = page
        if from_ is not None:
            payload["from"] = from_
        if extended is not None:
            payload["extended"] = bool(extended)
        if to is not None:
            payload["to"] = to
        return self._make_request("user.getRecentTracks", payload)

    def track_get_info(self, track=None, artist=None, mbid=None, username=None,
                       autocorrect=None):
        """
        :rtype : twisted.internet.defer.Deferred
        """
        if mbid is None and (track is None or artist is None):
            return ValueError("Must specify either mbid or artist and track")
        payload = {}
        if mbid is not None:
            payload["mbid"] = mbid
        if track is not None:
            payload["track"] = track
        if artist is not None:
            payload["artist"] = artist
        if username is not None:
            payload["username"] = username
        if autocorrect is not None:
            payload["autocorrect"] = autocorrect
        return self._make_request("track.getInfo", payload)

    def tasteometer_compare(self, type1, value1, type2, value2, limit=None):
        """
        :rtype : twisted.internet.defer.Deferred
        """
        payload = {
            "type1": type1,
            "value1": value1,
            "type2": type2,
            "value2": value2,
        }
        if limit is not None:
            payload["limit"] = limit
        return self._make_request("tasteometer.compare", payload)


class LastFMError(Exception):
    # Descriptions of error codes can be found here:
    # http://www.last.fm/api/errorcodes
    ERROR_CODES = {
        1: "Non-existent error",
        2: "Invalid service",
        3: "Invalid method",
        4: "Authentication failed",
        5: "Invalid format",
        6: "Invalid parameters",
        7: "Invalid resource",
        8: "Operation failed (try again)",
        9: "Invalid session key (re-authenticate)",
        10: "Invalid API key",
        11: "Service offline (try again later)",
        12: "Subscribers only",
        13: "Invalid method signature",
        14: "Unauthorised token",
        15: "This item is not available for streaming",
        16: "Service temporarily unavailable (try again later)",
        17: "Login required",
        18: "Trial expired",
        19: "Non-existent error",
        20: "Not enough content",
        21: "Not enough members",
        22: "Not enough fans",
        23: "Not enough neighbours",
        24: "No peak radio",
        25: "Radio not found",
        26: "API key suspended",
        27: "Deprecated",
        29: "Rate limit exceeded"
    }

    def __init__(self, err_code, message, links):
        Exception.__init__(self, message)
        self.err_code = err_code
        self.message = message
        self.links = links

    def __str__(self):
        return "%s: [%s] %s" % (self.__class__, self.err_code, self.message)
