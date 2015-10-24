# coding=utf-8
import re
import locale

from twisted.internet.defer import inlineCallbacks, returnValue
from txrequests import Session

from plugins.urls.handlers.handler import URLHandler
from plugins.urltools.exceptions import ApiKeyMissing
from plugins.urltools.handlers.osu.mods import get_mods
from utils.misc import str_to_regex_flags

__author__ = 'Gareth Coles'

URL_BASE = "https://osu.ppy.sh/api"

URL_BEATMAPS = URL_BASE + "/get_beatmaps"
URL_MATCH = URL_BASE + "/get_match"
URL_REPLAY = URL_BASE + "/get_replay"
URL_SCORES = URL_BASE + "/get_scores"
URL_USER = URL_BASE + "/get_user"
URL_USER_BEST = URL_BASE + "/get_user_best"
URL_USER_RECENT = URL_BASE + "/get_user_recent"

# Attempt to guess the locale
locale.setlocale(locale.LC_ALL, "")

strings = {
    "mapset": u"[osu! mapset] {artist} - {title} (by {creator}) - {counts}",

    "beatmap": u"[osu! {mode} beatmap] ({approved}) {artist} - {title} "
               u"[{version}] by {creator} [{bpm} BPM] - Difficulty: "
               u"{difficultyrating} | Leader: {scores[0][username]} with "
               u"{scores[0][score]} ({scores[0][count300]}/"
               u"{scores[0][count100]}/{scores[0][count50]}/"
               u"{scores[0][countmiss]}) - {scores[0][enabled_mods]}",
    "beatmap-mode-mismatch": u"[osu! {mode} beatmap] ({approved}) {artist} - "
                             u"{title} [{version}] by {creator} [{bpm} BPM] - "
                             u"Difficulty: {difficultyrating} - Mode '{mode}' "
                             u"doesn't apply to this map",
    "beatmap-no-scores": u"[osu! {mode} beatmap] ({approved}) {artist} - "
                         u"{title} [{version}] by {creator} [{bpm} BPM] - "
                         u"Difficulty: {difficultyrating}",
    "beatmap-unapproved": u"[osu! {mode} beatmap] ({approved}) {artist} - "
                          u"{title} [{version}] by {creator} [{bpm} BPM] - "
                          u"Difficulty: {difficultyrating}",

    "user": u"[osu! user] {username} (L{level}) "
            u"{count_rank_ss}/{count_rank_s}/{count_rank_a} - Rank {pp_rank} "
            u"| Ranked score: {ranked_score} | PP: {pp_raw}"
}

OSU_MODES = {
    0: u"Standard",
    1: u"Taiko",
    2: u"CtB",
    3: u"Mania",
    "0": u"Standard",
    "1": u"Taiko",
    "2": u"CtB",
    "3": u"Mania",

    # Special/extra modes

    "standard": 0,
    "osu": 0,
    "osu!": 0,

    "taiko": 1,
    "drum": 1,

    "ctb": 2,
    "catchthebeat": 2,
    "catch": 2,
    "beat": 2,
    "fruit": 2,

    "mania": 3,
    "osu!mania": 3,
    "osu! mania": 3,
    "osumania": 3,
    "osu mania": 3,


    # Shortened nodes

    "s": 0,
    "o": 0,
    "t": 1,
    "c": 2,
    "b": 2,
    "f": 2,
    "m": 3
}

OSU_APPROVALS = {
    "3": u"Qualified",
    "2": u"Approved",
    "1": u"Ranked",
    "0": u"Pending",
    "-1": u"WIP",
    "-2": u"Graveyard"
}


class OsuHandler(URLHandler):
    criteria = {
        "protocol": re.compile(r"http|https", str_to_regex_flags("iu")),
        "domain": re.compile(r"osu\.ppy\.sh", str_to_regex_flags("iu"))
    }

    session = None
    name = "osu"

    @property
    def api_key(self):
        return self.plugin.config.get("osu", {}).get("api_key", "")

    def __init__(self, plugin):
        super(OsuHandler, self).__init__(plugin)

        if not self.api_key:
            raise ApiKeyMissing()

        self.reload()

    def reload(self):
        self.teardown()

        self.session = Session()

    def teardown(self):
        if self.session is not None:
            self.session.close()

    def get_string(self, string):
        formatting = self.plugin.config.get("osu", {}).get("formatting", {})

        if string not in formatting:
            return strings[string]
        return formatting[string]

    @inlineCallbacks
    def get(self, *args, **kwargs):
        params = kwargs.get("params", {})
        kwargs["params"] = self.merge_params(params)

        r = yield self.session.get(*args, **kwargs)
        returnValue(r)

    def parse_fragment(self, url):
        """
        Sometimes osu pages have query-style fragments for some reason

        :param url: URL object to parse fragment from
        :type url: plugins.urls.url.URL

        :return: Parsed fragment as a dict
        :rtype: dict
        """

        parsed = {}

        if not url.fragment:
            return parsed

        for element in url.fragment.split("&"):
            if "=" in element:
                left, right = element.split("=", 1)
                parsed[left] = right
            else:
                parsed[element] = None

        return parsed

    def merge_params(self, params):
        params.update({
            "k": self.api_key
        })

        return params

    @inlineCallbacks
    def call(self, url, context):
        target = url.path

        while target.endswith("/"):
            target = target[:-1]

        target = target.split("/")

        if "" in target:
            target.remove("")
        if " " in target:
            target.remove(" ")

        message = ""

        try:
            if len(target) < 2:  # It's the front page or invalid, don't bother
                returnValue(True)
            elif target[0] in [  # Special cases we don't care about
                "forum", "wiki", "news"
            ]:
                returnValue(True)
            elif target[0].lower() == "p":  # Old-style page URL
                if target[1].lower() == "beatmap":
                    if "b" in url.query:
                        message = yield self.beatmap(url, url.query["b"])
            elif target[0].lower() == "u":  # User page
                message = yield self.user(url, target[1])
            elif target[0].lower() == "s":  # Beatmap set
                message = yield self.mapset(url, target[1])
            elif target[0].lower() == "b":  # Specific beatmap
                message = yield self.beatmap(url, target[1])

        except Exception:
            self.plugin.logger.exception("Error handling URL: {}".format(url))
            returnValue(True)

        # At this point, if `message` isn't set then we don't understand the
        # url, and so we'll just allow it to pass down to the other handlers

        if message and isinstance(message, basestring):
            context["event"].target.respond(message)
            returnValue(False)
        else:
            returnValue(True)

    @inlineCallbacks
    def beatmap(self, url, beatmap):
        fragment = self.parse_fragment(url)

        params = {}

        if url.query:
            params.update(url.query)

        if fragment:
            params.update(fragment)

        params["b"] = beatmap

        r = yield self.get(URL_BEATMAPS, params=params)
        beatmap = r.json()[0]

        if "m" not in params:
            params["m"] = beatmap["mode"]

        for key in ["favourite_count", "playcount", "passcount"]:
            beatmap[key] = locale.format(
                "%d", int(beatmap[key]), grouping=True
            )

        for key in ["difficultyrating"]:
            beatmap[key] = int(round(float(beatmap[key])))

        if "approved" in beatmap:
            beatmap["approved"] = OSU_APPROVALS.get(
                beatmap["approved"], u"Unknown approval"
            )

        beatmap["mode"] = OSU_MODES[beatmap["mode"]]

        scores = None

        try:
            r = yield self.get(URL_SCORES, params=params)
            scores = r.json()

            for score in scores:
                for key in ["score", "count50", "count100", "count300",
                            "countmiss", "countkatu", "countgeki"]:
                    score[key] = locale.format(
                        "%d", int(score[key]), grouping=True
                    )
                for key in ["pp"]:
                    score[key] = int(round(float(score[key])))

                score["enabled_mods"] = ", ".join(
                    get_mods(int(score["enabled_mods"]))
                )
        except Exception:
            pass

        data = beatmap

        if beatmap["approved"] in [
            "Pending", "WIP", "Graveyard", u"Unknown approval"
        ]:
            message = self.get_string("beatmap-unapproved")
        elif scores is None:
            message = self.get_string("beatmap-mode-mismatch")
        elif not scores:
            message = self.get_string("beatmap-no-scores")
        else:
            data["scores"] = scores
            message = self.get_string("beatmap")

        returnValue(message.format(**data))

    @inlineCallbacks
    def mapset(self, url, mapset):
        params = {
            "s": mapset
        }

        r = yield self.get(URL_BEATMAPS, params=params)
        data = r.json()

        modes = {}
        to_join = []

        for beatmap in data:
            modes[beatmap["mode"]] = modes.get(beatmap["mode"], 0) + 1
            beatmap["mode"] = OSU_MODES[beatmap["mode"]]

            for key in ["favourite_count", "playcount", "passcount"]:
                beatmap[key] = locale.format(
                    "%d", int(beatmap[key]), grouping=True
                )

            for key in ["difficultyrating"]:
                beatmap[key] = int(round(float(beatmap[key])))

            if "approved" in beatmap:
                beatmap["approved"] = OSU_APPROVALS.get(
                    beatmap["approved"], u"Unknown approval: {}".format(
                        beatmap["approved"]
                    )
                )

        for k, v in modes.iteritems():
            if v:
                to_join.append("{} x{}".format(OSU_MODES[k], v))

        first = data[0]

        data = {
            "beatmaps": data,
            "counts": ", ".join(to_join)
        }

        data.update(first)

        returnValue(self.get_string("mapset").format(**data))

    @inlineCallbacks
    def user(self, url, user):
        fragment = self.parse_fragment(url)

        params = {
            "u": user,
        }

        if "m" in fragment:  # Focused mode
            m = fragment["m"].lower()

            if m in OSU_MODES:
                params["m"] = OSU_MODES[m]

            else:
                try:
                    params["m"] = int(m)
                except ValueError:
                    pass

        # This logic is down to being able to specify either a username or ID.
        # The osu backend has to deal with this and so the api lets us specify
        # either "string" or "id" for usernames and IDs respectively. This
        # may be useful for usernames that are numerical, so we allow users
        # to add this to the fragment if they wish.

        if "t" in fragment:  # This once was called "t"..
            params["type"] = fragment["t"]
        elif "type" in fragment:  # ..but now is "type" for some reason
            params["type"] = fragment["type"]

        r = yield self.get(URL_USER, params=params)
        data = r.json()[0]  # It's a list for some reason

        for key in ["level", "accuracy"]:  # Round floats
            data[key] = int(round(float(data[key])))

        for key in ["ranked_score", "pp_raw", "pp_rank", "count300",
                    "count100", "count50", "playcount", "total_score",
                    "pp_country_rank"]:  # Localize number formatting
            data[key] = locale.format(
                "%d", int(data[key]), grouping=True
            )

        epic_factors = [
            int(event["epicfactor"]) for event in data["events"]
        ]

        epic_total = reduce(sum, epic_factors, 0)
        epic_avg = 0

        if epic_total:
            epic_avg = round(
                epic_total / (1.0 * len(epic_factors)), 2
            )

        data["events"] = "{} events at an average of {}/32 epicness".format(
            len(epic_factors),
            epic_avg
        )

        returnValue(self.get_string("user").format(**data))
