# coding=utf-8
import re
from twisted.internet.defer import inlineCallbacks

from plugins.urls.handlers.handler import URLHandler
from plugins.urltools.exceptions import ApiKeyMissing
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

"""
    def site_osu(self, url):
        self.logger.trace("OSU | %s" % url)
        if "osu" not in self.api_details:
            return None

        domain = "https://osu.ppy.sh/api/"

        parsed = urlparse.urlparse(url)
        split = parsed.path.lower().split("/")

        if "" in split:
            split.remove("")

        if len(split) < 2:
            return None

        self.logger.trace("OSU | %s" % split)

        if split[0] == "u":  # User
            args = {"m": "",
                    "t": ""}
            if parsed.fragment:
                for element in parsed.fragment.split("&"):
                    _split = element.split("=")
                    args[_split[0]] = _split[1]
            m = ""
            if "m" in args:
                m = args["m"].lower()
                try:
                    int(m)
                except:
                    if m in self.OSU_MODES:
                        m = self.OSU_MODES[m]

            params = {
                "k": self.api_details["osu"],
                "u": split[1],
                "m": m,
                "t": args["t"]
            }

            d = self.do_get(domain + "get_user", params)

            d = json.loads(d)[0]

            return self.OSU_U_STR % (
                d["username"], int(round(float(d["level"]))),
                d["count_rank_ss"], d["count_rank_s"],
                d["count_rank_a"], d["pp_rank"],
                locale.format(
                    "%d",
                    int(d["ranked_score"]),
                    grouping=True
                ), d["pp_raw"])

        elif split[0] == "s":  # Beatmap set
            params = {
                "k": self.api_details["osu"],
                "s": split[1]
            }

            d = self.do_get(domain + "get_beatmaps", params)
            d = json.loads(d)

            _map = d[0]

            modes = {"0": 0, "1": 0, "2": 0, "3": 0}

            for element in d:
                mode = element["mode"]
                modes[mode] += 1

            to_join = []

            for key, value in modes.items():
                if value > 0:
                    to_join.append("%s x%s" % (self.OSU_MODES[key], value))

            counts = ", ".join(to_join)

            return self.OSU_S_STR % (
                _map["artist"], _map["title"], _map["creator"], counts
            )

        elif split[0] == "b":  # Beatmap
            params = {}

            if parsed.query:
                _split = parsed.query.split("&")
                for element in _split:
                    __split = element.split("=")
                    params[__split[0]] = __split[1]

            if "&" in split[1]:
                ___split = split[1].split("&")
                split[1] = ___split[0]
                ___split = ___split[1:]
                for element in ___split:
                    __split = element.split("=")
                    params[__split[0]] = __split[1]

            params["k"] = self.api_details["osu"]
            params["b"] = split[1]

            _map = self.do_get(domain + "get_beatmaps", params)
            _map = json.loads(_map)[0]

            if "m" not in params:
                params["m"] = _map["mode"]

            try:
                _score = self.do_get(domain + "get_scores", params)
                _score = json.loads(_score)[0]
            except:
                if self.OSU_APPROVALS[_map["approved"]] in [
                    "Pending", "WIP", "Graveyard"
                ]:
                    return self.OSU_B_STR_WIP % (
                        self.OSU_MODES[_map["mode"]],
                        self.OSU_APPROVALS[_map["approved"]], _map["artist"],
                        _map["title"], _map["version"], _map["creator"],
                        float(_map["bpm"]),
                        round(float(_map["difficultyrating"]), 2)
                    )
                return self.OSU_B_STR_NO_SCORE % (
                    self.OSU_MODES[_map["mode"]],
                    self.OSU_APPROVALS[_map["approved"]], _map["artist"],
                    _map["title"], _map["version"], _map["creator"],
                    _map["bpm"], round(float(_map["difficultyrating"]), 2),
                    self.OSU_MODES[params["m"]]
                )

            return self.OSU_B_STR % (
                self.OSU_MODES[_map["mode"]],
                self.OSU_APPROVALS[_map["approved"]], _map["artist"],
                _map["title"], _map["version"], _map["creator"],
                _map["bpm"], round(float(_map["difficultyrating"]), 2),
                _score["username"],
                locale.format("%d", int(_score["score"]), grouping=True),
                _score["count300"], _score["count100"], _score["count50"],
                _score["countmiss"]
            )
        elif split[0] == "p":  # Page
            if split[1] == "beatmap":
                params = {}

                if parsed.query:
                    _split = parsed.query.split("&")
                    for element in _split:
                        __split = element.split("=")
                        params[__split[0]] = __split[1]

                if "&" in split[1]:
                    ___split = split[1].split("&")
                    split[1] = ___split[0]
                    ___split = ___split[1:]
                    for element in ___split:
                        __split = element.split("=")
                        params[__split[0]] = __split[1]

                params["k"] = self.api_details["osu"]

                _map = self.do_get(domain + "get_beatmaps", params)
                _map = json.loads(_map)[0]

                if "m" not in params:
                    params["m"] = _map["mode"]

                try:
                    _score = self.do_get(domain + "get_scores", params)
                    _score = json.loads(_score)[0]
                except:
                    if self.OSU_APPROVALS[_map["approved"]] == "WIP":
                        return self.OSU_B_STR_WIP % (
                            self.OSU_MODES[_map["mode"]],
                            self.OSU_APPROVALS[_map["approved"]],
                            _map["artist"], _map["title"], _map["version"],
                            _map["creator"], float(_map["bpm"]),
                            round(float(_map["difficultyrating"]), 2)
                        )
                    return self.OSU_B_STR_NO_SCORE % (
                        self.OSU_MODES[_map["mode"]],
                        self.OSU_APPROVALS[_map["approved"]], _map["artist"],
                        _map["title"], _map["version"], _map["creator"],
                        float(_map["bpm"]),
                        round(float(_map["difficultyrating"]), 2),
                        self.OSU_MODES[params["m"]]
                    )

                return self.OSU_B_STR % (
                    self.OSU_MODES[_map["mode"]],
                    self.OSU_APPROVALS[_map["approved"]], _map["artist"],
                    _map["title"], _map["version"], _map["creator"],
                    float(_map["bpm"]),
                    round(float(_map["difficultyrating"]), 2),
                    _score["username"],
                    locale.format("%d", int(_score["score"]), grouping=True),
                    _score["count300"], _score["count100"], _score["count50"],
                    _score["countmiss"]
                )

        return None
"""

"""
OSU_LOGO = "osu!"
    OSU_S_STR = "[" + OSU_LOGO + " mapset] %s - %s (by %s) - %s"
    OSU_B_STR = "[" + OSU_LOGO + " %s beatmap] (%s) %s - %s [%s] by %s " \
                                 "[%s BPM] - Difficulty: %.2f | Leader: %s " \
                                 "with %s (%s/%s/%s/%s)"
    OSU_B_STR_NO_SCORE = "[" + OSU_LOGO + " %s beatmap] (%s) %s - %s [%s] " \
                                          "by %s [%s BPM] - Difficulty: %.2f" \
                                          " - Mode '%s' doesn't apply to " \
                                          "this map."
    OSU_B_STR_SCORELESS = "[" + OSU_LOGO + " %s beatmap] (%s) %s - %s [%s] " \
                                           "by %s [%s BPM] - Difficulty: %.2f"
    OSU_B_STR_WIP = "[" + OSU_LOGO + " %s beatmap] (%s) %s - %s [%s] " \
                                     "by %s [%s BPM] - Difficulty: %.2f"
    OSU_U_STR = "[" + OSU_LOGO + " user] %s (L%d) %s/%s/%s - Rank %s | " \
                                 "Ranked score: %s | PP: %s"

    OSU_MODES = {
        0: "Standard",
        1: "Taiko",
        2: "CtB",
        3: "Mania",
        "0": "Standard",
        "1": "Taiko",
        "2": "CtB",
        "3": "Mania",
        "standard": 0,
        "taiko": 1,
        "ctb": 2,
        "mania": 3,
        "osu": 0,
        "osu!": 0,
        "osu!mania": 3,
        "osu! mania": 3,
        "s": 0,  # Standard
        "o": 0,  # Osu!
        "t": 1,  # Taiko
        "c": 2,  # CtB: Catch
        "b": 2,  # CtB: Beat
        "f": 2,  # CtB: Fruit
        "m": 3  # Mania
    }

    OSU_APPROVALS = {
        "3": "Qualified",
        "2": "Approved",
        "1": "Ranked",
        "0": "Pending",
        "-1": "WIP",
        "-2": "Graveyard"
    }
"""


class OsuHandler(URLHandler):

    criteria = {
        "protocol": re.compile(r"http|https", str_to_regex_flags("iu")),
        "domain": re.compile(r"osu\.ppy\.sh", str_to_regex_flags("iu"))
    }

    @property
    def api_key(self):
        return self.plugin.config.get("osu", {}).get("api_key", "")

    def __init__(self, plugin):
        super(OsuHandler, self).__init__(plugin)

        if not self.api_key:
            raise ApiKeyMissing()

    @inlineCallbacks
    def call(self, url, context):
        pass
