# coding=utf-8
import json
import urlparse
from system.plugin_manager import YamlPluginManagerSingleton

__author__ = 'Gareth Coles'

import locale
import requests
import urllib
import urllib2

import system.plugin as plugin

from system.storage.formats import YAML
from system.storage.manager import StorageManager

# Attempt to guess the locale.
locale.setlocale(locale.LC_ALL, "")


class URLToolsPlugin(plugin.PluginObject):

    config = None
    storage = None

    api_details = {}
    sites = {}
    shorteners = {}

    plugman = None

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

    OSU_LOGO = "osu!"
    OSU_S_STR = "[" + OSU_LOGO + " mapset] %s - %s (by %s) - %s"
    OSU_B_STR = "[" + OSU_LOGO + " %s beatmap] (%s) %s - %s [%s] by %s " \
                                 "[%s BPM] - Difficulty: %.2f | Leader: %s " \
                                 "with %s (%s/%s/%s/%s)"
    OSU_B_STR_NO_SCORE = "[" + OSU_LOGO + " %s beatmap] (%s) %s - %s [%s] " \
                                          "by %s [%s BPM] - Difficulty: %.2f" \
                                          " - Mode '%s' doesn't apply to " \
                                          "this map."
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

    GITHUB_URL = "https://api.github.com"

    GITHUB_USER = "[GitHub user] %s (%s followers) - %s repos, %s gists"
    GITHUB_USER_ADMIN = "[GitHub admin] %s (%s followers) - %s repos, %s gists"
    GITHUB_ORG = "[GitHub org] %s (%s followers) - %s repos, %s gists"

    GITHUB_REPO = "[GitHub repo / No forks] %s (%s stars / %s watchers) - " \
                  "%s open issues - %s"
    GITHUB_REPO_FORKS = "[GitHub repo / %s forks] %s (%s stars / %s " \
                        "watchers) - %s open issues - %s"
    GITHUB_REPO_FORK = "[GitHub repo / fork of %s] %s (%s stars / %s " \
                       "watchers) - %s open issues - %s"

    GITHUB_RELEASES = "[GitHub repo / %s releases] %s/%s - Latest: %s by %s " \
                      "(%s downloads)"
    GITHUB_RELEASE = "[GitHub release] %s/%s/%s by %s - %s assets, %s " \
                     "downloads"
    GITHUB_RELEASE_NONE = "[GitHub repo] %s/%s - No releases found"

    GITHUB_ISSUES = "[GitHub repo / %s issues] %s/%s - %s open, %s closed"
    GITHUB_ISSUE = "[GitHub issue] %s/%s/%s by %s (%s) - %s (%s)"
    GITHUB_ISSUE_MILESTONE = "[GitHub issue] %s/%s/%s %s by %s (%s) - %s (%s)"
    GITHUB_ISSUE_ASSIGNED = "[GitHub issue] %s/%s/%s by %s (%s) - %s (%s) " \
                            "- Assigned to %s"
    GITHUB_ISSUE_ASSIGNED_MILESTONE = "[GitHub issue] %s/%s/%s %s by %s " \
                                      "(%s) - %s (%s) - Assigned to %s"

    # GITHUB_COMMITS = u"[GitHub repo / last %s commits] %s/%s - +%s/-%s/±%s" \
    #                  u" (%s individual file edits) by %s authors."
    GITHUB_COMMITS = u"[GitHub repo / last %s commits] %s/%s - %s commits by" \
                     u" %s authors."
    GITHUB_COMMITS_COMMIT = u"[GitHub commit] %s/%s +%s/-%s/±%s (%s files) " \
                            u"by %s - %s"
    GITHUB_COMMITS_COMPARE = "[GitHub commit comparison] %s/%s - Comparing " \
                             "%s by %s and %s by %s with %s intermediary " \
                             "commits"

    GITHUB_PULLS = "[GitHub repo / %s pull requests] %s/%s - %s open, %s " \
                   "closed"
    GITHUB_PULLS_PULL = "[GitHub pull request] %s/%s/%s by %s (%s) - %s"

    def setup(self):
        self.storage = StorageManager()
        try:
            self.config = self.storage.get_file(self, "config", YAML,
                                                "plugins/urltools.yml")
        except Exception:
            self.logger.exception("Unable to load the configuration!")
            self._disable_self()
            return

        self.sites["osu.ppy.sh"] = self.site_osu
        self.sites["youtube.com"] = self.site_youtube
        self.sites["github.com"] = self.site_github

        self.shorteners["is.gd"] = self.shortener_isgd
        self.shorteners["nazr.in"] = self.shortener_nazrin
        self.shorteners["v.gd"] = self.shortener_vgd
        self.shorteners["waa.ai"] = self.shortener_waaai

        self.plugman = YamlPluginManagerSingleton()

        self._load()
        self.config.add_callback(self._load)

    def _load(self):
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
                self.api_details["osu"] = sites["apikeys"]["osu"]
            sites_enabled.append(site)

        for shortener in shorteners["enabled"]:
            # This is for checking API keys and settings
            shorteners_enabled.append(shortener)

        self.logger.debug("Registering with the URLs plugin..")

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
        self.logger.trace("URL: %s" % url)
        self.logger.trace("Params: %s" % params)
        query_string = urllib.urlencode(params)
        constructed = url + "?" + query_string
        self.logger.trace("Constructed GET: %s" % constructed)
        r = urllib2.urlopen(constructed)
        data = r.read()
        self.logger.trace("Response: %s" % data)
        return data

    def do_post(self, url, params, header=None):
        if not header:
            header = {}
        request = urllib2.Request(url, params, header)
        self.logger.trace("Constructed POST: %s | %s" % (url, params))
        r = urllib2.urlopen(request)
        data = r.read()
        self.logger.trace("Response: %s" % data)
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

    def gh_user(self, d):
        if d.get("site-admin", False):
            return self.GITHUB_USER_ADMIN % (
                d["name"],
                d["followers"],
                d["public_repos"],
                d["public_gists"]
            )
        return self.GITHUB_USER % (
            d["name"],
            d["followers"],
            d["public_repos"],
            d["public_gists"]
        )

    def gh_org(self, d):
        return self.GITHUB_ORG % (
            d["name"],
            d["followers"],
            d["public_repos"],
            d["public_gists"]
        )

    def site_github(self, url):
        self.logger.trace("GITHUB | %s" % url)

        if url[-1] == "/":
            url = url[:-1]

        parsed = urlparse.urlparse(url)
        split = parsed.path.lower().split("/")

        if "" in split:
            split.remove("")

        if " " in split:
            split.remove(" ")

        if len(split) == 1:
            # User or org
            # First, check if it's a user..
            try:
                r = requests.get(
                    "%s/users/%s" % (self.GITHUB_URL, split[0])
                )
                data = r.json()
            except Exception as e:  # If not, let's see if it's an org
                self.logger.debug(
                    "Error getting GitHub user %s: %s" % (split[0], e)
                )
                self.logger.debug(
                    "Checking to see if they're an org instead.."
                )
                try:
                    r = requests.get(
                        "%s/orgs/%s" % (self.GITHUB_URL, split[0])
                    )
                    data = r.json()
                except Exception:  # It's.. I have no idea.
                    self.logger.exception(
                        "Error getting GitHub user/org %s" % split[0]
                    )
                    return None
                else:  # It's an org!
                    return self.gh_org(data)

            else:  # It's a user!
                if data["type"] == "User":
                    return self.gh_user(data)
                else:
                    return self.gh_org(data)

        elif len(split) == 2:
            owner = split[0]
            repo = split[1]
            try:
                r = requests.get("%s/repos/%s/%s" % (
                    self.GITHUB_URL, owner, repo
                ))

                d = r.json()
            except Exception:
                self.logger.exception(
                    "Error getting GitHub repo %s/%s" % (owner, repo)
                )
            else:
                if d["fork"]:
                    return self.GITHUB_REPO_FORK % (
                        d["parent"]["full-name"],
                        d["full-name"],
                        d["stargazers_count"],
                        d["watchers_count"],
                        d["open_issues_count"],
                        d["description"]
                    )
                elif d["forks_count"] > 0:
                    return self.GITHUB_REPO_FORKS % (
                        d["forks_count"],
                        d["full-name"],
                        d["stargazers_count"],
                        d["watchers_count"],
                        d["open_issues_count"],
                        d["description"]
                    )
                else:
                    return self.GITHUB_REPO % (
                        d["full-name"],
                        d["stargazers_count"],
                        d["watchers_count"],
                        d["open_issues_count"],
                        d["description"]
                    )
        elif len(split) >= 3:  # Commit, issue, etc
            owner = split[0]
            repo = split[1]
            if split[2] == "releases":  # Releases
                if len(split) == 3:  # Releases list
                    try:
                        r = requests.get("%s/repos/%s/%s/releases" % (
                            self.GITHUB_URL, owner, repo
                        ))
                        d = r.json()
                    except Exception:
                        self.logger.exception(
                            "Error getting releases for GitHub repo %s/%s"
                            % (owner, repo)
                        )
                    else:
                        count = len(d)
                        if count > 0:
                            current = d[0]
                            dls = 0

                            for asset in current["assets"]:
                                dls += asset["download_count"]

                            return self.GITHUB_RELEASES % (
                                count, owner, repo,
                                current["name"], current["author"]["login"],
                                dls
                            )
                        else:
                            return self.GITHUB_RELEASE_NONE % (
                                owner, repo
                            )
                else:  # Specific release
                    release = split[3]
                    try:
                        r = requests.get("%s/repos/%s/%s/releases/%s" % (
                            self.GITHUB_URL, owner, repo, release
                        ))
                        d = r.json()
                    except Exception:
                        self.logger.exception(
                            "Error getting release for GitHub repo %s/%s/%s"
                            % (owner, repo, release)
                        )
                    else:
                        dls = 0

                        if "asset" in d:
                            for asset in d["assets"]:
                                dls += asset["download_count"]
                        else:
                            dls = "N/A"

                        return self.GITHUB_RELEASE % (
                            owner, repo, release,
                            d["author"]["login"],
                            len(d["assets"]), dls
                        )
            elif split[2] == "issues" or split[2] == "issue":  # Issues
                if len(split) == 3:  # Issues list
                    try:
                        open_r = requests.get(
                            "%s/repos/%s/%s/issues?state=open" % (
                                self.GITHUB_URL, owner, repo
                            ))
                        open_d = open_r.json()

                        closed_r = requests.get(
                            "%s/repos/%s/%s/issues?state=closed" % (
                                self.GITHUB_URL, owner, repo
                            ))
                        closed_d = closed_r.json()
                    except Exception:
                        self.logger.exception("Error getting issues for "
                                              "GitHub repository %s/%s" %
                                              (repo, owner))
                    else:
                        _open = len(open_d)
                        _closed = len(closed_d)
                        _total = _open + _closed
                        return self.GITHUB_ISSUES % (
                            _total, owner, repo, _open, _closed
                        )
                else:  # Specific issue
                    issue = split[3]

                    try:
                        r = requests.get("%s/repos/%s/%s/issues/%s" % (
                            self.GITHUB_URL, owner, repo, issue
                        ))
                        d = r.json()
                    except Exception:
                        self.logger.exception(
                            "Error getting GitHub issue %s/%s/%s"
                            % (owner, repo, issue)
                        )
                    else:
                        labels = []

                        for label in d["labels"]:
                            labels.append(label["name"])

                        labels = sorted(labels)

                        if d["milestone"] is None:
                            if d["assignee"] is None:
                                return self.GITHUB_ISSUE % (
                                    owner, repo, issue,
                                    d["user"]["login"],
                                    d["state"].title(),
                                    d["title"], ", ".join(labels)
                                )
                            else:
                                return self.GITHUB_ISSUE_ASSIGNED % (
                                    owner, repo, issue,
                                    d["user"]["login"],
                                    d["state"].title(),
                                    d["title"], ", ".join(labels),
                                    d["assignee"]["login"]
                                )
                        elif d["assignee"] is None:
                            return self.GITHUB_ISSUE_MILESTONE % (
                                owner, repo, issue, d["milestone"],
                                d["user"]["login"],
                                d["state"].title(),
                                d["title"], ", ".join(labels)
                            )
                        else:
                            return self.GITHUB_ISSUE_ASSIGNED_MILESTONE % (
                                owner, repo, issue, d["milestone"],
                                d["user"]["login"],
                                d["state"].title(),
                                d["title"], ", ".join(labels),
                                d["assignee"]["login"]
                            )
            elif split[2] == "commits" or split[2] == "commit":  # Commits
                if len(split) == 3:  # Commits list
                    try:
                        r = requests.get("%s/repos/%s/%s/commits" % (
                            self.GITHUB_URL, owner, repo
                        ))
                        d = r.json()
                    except Exception:
                        self.logger.exception(
                            "Error loading commits for GitHub repo %s/%s"
                            % (owner, repo)
                        )
                    else:
                        # additions = 0
                        # deletions = 0
                        # totals = 0
                        # file_edits = 0
                        authors = set()

                        for commit in d:
                            # additions += commit["stats"]["additions"]
                            # deletions += commit["stats"]["deletions"]
                            # totals += commit["stats"]["total"]
                            # file_edits += len(commit["files"])
                            authors.add(commit["author"]["login"])

                        num_authors = len(authors)

                        return self.GITHUB_COMMITS % (
                            len(d), owner, repo, len(d), num_authors
                        )
                else:  # Specific commit
                    commit = split[3]
                    if "..." not in commit:
                        try:
                            r = requests.get("%s/repos/%s/%s/commits/%s" % (
                                self.GITHUB_URL, owner, repo, commit
                            ))
                            d = r.json()
                        except Exception:
                            self.logger.exception(
                                "Error loading GitHub commit %s/%s/%s"
                                % (owner, repo, commit)
                            )
                        else:
                            message = d["commit"]["message"]
                            if "\n" in message:
                                messages = message.strip("\r").split("\n")
                                if "" in messages:
                                    messages.remove("")
                                message = messages.pop(0)
                                message += " ...and %s more lines" \
                                           % len(messages)
                            return self.GITHUB_COMMITS_COMMIT % (
                                owner, repo,
                                d["stats"]["additions"],
                                d["stats"]["deletions"],
                                d["stats"]["total"],
                                len(d["files"]),
                                d["author"]["login"],
                                message
                            )
                    else:
                        commits = commit.split("...")
                        left = commits[0]
                        right = commits[1]

                        try:
                            r = requests.get(
                                "%s/repos/%s/%s/commits/%s...%s" % (
                                    self.GITHUB_URL, owner, repo, left, right
                                )
                            )
                            d = r.json()
                        except Exception:
                            self.logger.exception(
                                "Error loading GitHub commit comparison "
                                " for %s/%s - %s...%s"
                                % (owner, repo, left, right)
                            )
                        else:
                            if ":" in left:
                                left_split = left.split(":", 1)
                                left_hash = left_split[0] + \
                                    ":" + \
                                    left_split[1][:6]
                            else:
                                left_hash = "%s/%s:%s" \
                                    % (owner, repo, left[:6])

                            if ":" in right:
                                right_split = right.split(":", 1)
                                right_hash = right_split[0] + \
                                    ":" + \
                                    right_split[1][:6]
                            else:
                                right_hash = "%s/%s:%s" \
                                    % (owner, repo, right[:6])

                            return self.GITHUB_COMMITS_COMPARE % (
                                owner, repo,
                                left_hash, d["base_commit"]["author"]["login"],
                                right_hash, d["commits"][0]["author"]["login"],
                                d["total_commits"]
                            )
            elif split[2] == "pulls":  # Pull requests
                if len(split) == 3:  # PRs list
                    try:
                        open_r = requests.get(
                            "%s/repos/%s/%s/pulls?state=open" % (
                                self.GITHUB_URL, owner, repo
                            )
                        )
                        open_d = open_r.json()

                        closed_r = requests.get(
                            "%s/repos/%s/%s/pulls?state=closed" % (
                                self.GITHUB_URL, owner, repo
                            )
                        )
                        closed_d = closed_r.json()
                    except Exception:
                        self.logger.exception(
                            "Error getting pull requests for GitHub repo %s/%s"
                            % (owner, repo)
                        )
                    else:
                        return self.GITHUB_PULLS % (
                            len(open_d) + len(closed_d),
                            owner, repo,
                            len(open_d), len(closed_d)
                        )
                else:  # Specific PR
                    pr = split[3]
                    try:
                        r = requests.get(
                            "%s/repos/%s/%s/pulls/%s" % (
                                self.GITHUB_URL, owner, repo, pr
                            )
                        )
                        d = r.json()
                    except Exception:
                        self.logger.exception(
                            "Error getting pull requests for GitHub repo %s/%s"
                            % (owner, repo)
                        )
                    else:
                        return self.GITHUB_PULLS_PULL % (
                            owner, repo, pr,
                            d["user"]["login"],
                            d["state"].title(),
                            d["title"]
                        )
            # TODO: Branches and perhaps wiki
            # elif split[2] == "branches":  # Branches
            #     if len(split) == 3:  # Branches list
            #         pass
            #     else:  # Specific branch
            #         pass

        return None

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
                if self.OSU_APPROVALS[_map["approved"]] == "WIP":
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
