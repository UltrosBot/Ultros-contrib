__author__ = 'Sean'

import requests

from system.command_manager import CommandManager
from system.plugin import PluginObject
from utils.config import Config
from utils.data import Data


class Plugin(PluginObject):

    commands = None
    config = None
    timeout = 100

    def setup(self):
        ### Grab important shit
        self.commands = CommandManager.instance()

        ### Initial config load
        try:
            self.config = Config("plugins/lastfm.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            self.logger.error("Disabling...")
            self._disable_self()
            return
        if not self.config.exists:
            self.logger.error("Unable to find config/plugins/lastfm.yml")
            self.logger.error("Disabling...")
            self._disable_self()
            return
            ### Same for the data file (nickname=>lastfmusername map)
        try:
            self.nickmap = Data("plugins/lastfm-nickmap.yml")
        except Exception:
            self.logger.exception("Error loading nickmap!")
            self.logger.error("Disabling...")
            self._disable_self()

        ### Load options from config and nick map from data
        self._load()

        ### Register commands
        self.commands.register_command("nowplaying",
                                       self.nowplaying_cmd,
                                       self,
                                       "lastfm.nowplaying")
        # TODO: Replace np command with nowplaying alias when implemented
        self.commands.register_command("np",
                                       self.nowplaying_cmd,
                                       self,
                                       "lastfm.nowplaying")
        self.commands.register_command("lastfmnick",
                                       self.lastfmnick_cmd,
                                       self,
                                       "lastfm.lastfmnick")

    def reload(self):
        try:
            self.config.reload()
        except Exception:
            self.logger.exception("Error reloading configuration!")
            return False
        self._load()
        return True

    def _load(self):
        self.apikey = self.config["apikey"]
        self.api = LastFM(self.apikey)

    def _get_username(self, user, none_if_unset=False):
        user = user.lower()
        try:
            return self.nickmap[user]
        except KeyError:
            if none_if_unset:
                return None
            else:
                return user

    def _set_username(self, user, lastfm_user):
        with self.nickmap:
            self.nickmap[user.lower()] = lastfm_user

    def nowplaying_cmd(self, caller, source, args, protocol):
        ### Get LastFM username to use
        username = None
        if len(args) == 0:
            username = self._get_username(caller.nickname)
        elif len(args) == 1:
            username = self._get_username(args[0])
        else:
            caller.respond("Usage: {CHARS}nowplaying [lastfm username]")
            return

        ### Query LastFM
        response = None
        try:
            response = self.api.user_get_recent_tracks(username, 1)
        except LastFMError as ex:
            # Some errors will be caused by user input
            if ex.err_code in (6,):
                caller.respond("LastFM: %s" % ex.message)
            else:
                self.logger.exception("Error while fetching nowplaying")
                caller.respond("There was an error while contacting LastFM - "
                               "please alert a bot admin")
            return

        ### Parse the info and print it
        try:
            track = response["recenttracks"]["track"][0]
            if (("nowplaying" in track["@attr"] and
                 bool(track["@attr"]["nowplaying"]))):
                source.respond(u"%s is now playing: %s - %s" %
                               (username,
                                track["artist"]["#text"],
                                track["name"]))
            else:
                source.respond("%s is not currently listening to anything" %
                               username)
        except Exception as ex:
            # If the response is unexpected (example, the user has never
            # listened to anything), then we'll get errors. Log this in case
            # there's actually a bug in there somewhere.
            self.logger.warning(exc_info=ex)
            source.respond("%s is not currently listening to anything" %
                           username)

    def lastfmnick_cmd(self, caller, source, args, protocol):
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


class LastFM(object):
    """
    The only module I could find in pypi for this didn't parse the nowplaying
    part of User.getRecentTracks(), and it used the XML API, so I didn't fancy
    forking it. I'll build on this as necessary, and if it gets to the point
    where it has decent coverage of the LastFM API, I'll split it off into its
    own module and stick it on pypi. That's alsow hy it's in this file and not
    in its own - not sure if the package manager can deal with files being
    removed in updates.
    """

    API_URL = "http://ws.audioscrobbler.com/2.0/"

    def __init__(self, api_key):
        self._api_key = api_key

    def _make_request(self, method, payload):
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
        result = requests.post(self.API_URL, final_payload).json()
        if "error" in result:
            raise LastFMError(result["error"],
                              result["message"],
                              result["links"])
        else:
            return result

    def user_get_recent_tracks(self, username, limit=None, page=None,
                               from_=None, extended=None, to=None):
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
            payload["to"] = from_
        return self._make_request("user.getRecentTracks", payload)


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
