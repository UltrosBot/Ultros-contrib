# coding=utf-8

import datetime
import random
import re

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
from txrequests import Session

from plugins.urls.handlers.handler import URLHandler
from plugins.urls.matching import extract_urls

from utils.misc import str_to_regex_flags

__author__ = 'Gareth Coles'

BASE_URL = "https://api.github.com"

URL_ZEN = BASE_URL + "/zen"

URL_USER = BASE_URL + "/users/{0}"
URL_ORG = BASE_URL + "/orgs/{0}"
URL_REPO = BASE_URL + "/repos/{0}/{1}"

URL_RELEASES = URL_REPO + "/releases"
URL_RELEASE = URL_RELEASES + "/{2}"
URL_RELEASE_TAGS = URL_RELEASES + "/tags/{2}"
URL_RELEASE_FILE = URL_RELEASES + "/assets/{2}"

URL_TAGS = URL_REPO + "/tags"

URL_GET_CONTENTS = URL_REPO + "/contents/{2}"

URL_ISSUES = URL_REPO + "/issues"
URL_ISSUES_OPEN = URL_ISSUES + "?state=open"
URL_ISSUES_CLOSED = URL_ISSUES + "?state=closed"
URL_ISSUE = URL_ISSUES + "/{2}"

URL_LABELS = URL_REPO + "/labels"
URL_LABEL = URL_LABELS + "/{2}"

URL_MILESTONES = URL_REPO + "/milestones"
URL_MILESTONE = URL_MILESTONES + "/{2}"

URL_TREE = URL_REPO + "/git/trees/{2}"

URL_BLOB = URL_REPO + "/git/blobs/{2}"

URL_WATCHERS = URL_REPO + "/subscribers"  # Sigh
URL_STARGAZERS = URL_REPO + "/stargazers"

URL_COMMITS = URL_REPO + "/commits"
URL_COMMIT = URL_COMMITS + "/{2}"
URL_COMMIT_RANGE = URL_REPO + "/compare/{2}...{3}"

URL_PULLS = URL_REPO + "/pulls"
URL_PULLS_OPEN = URL_PULLS + "?state=open"
URL_PULLS_CLOSED = URL_PULLS + "?state=closed"
URL_PULL = URL_PULLS + "/{2}"

URL_STATS = URL_REPO + "/stats"
URL_STATS_CONTRIBUTORS = URL_STATS + "/contributors"

strings = {
    "user": u"[GitHub user] {name} ({login}) - {public_repos} repos / "
            u"{public_gists} gists - {followers} followers / {following} "
            u"following - {blog}",
    "org": u"[GitHub org] {name}: {description} - {public_repos} repos / "
           u"{public_gists} gists - {followers} followers - {blog}",

    "repo": u"[GitHub repo] {full_name}: {description} - {forks_count} "
            u"forks / {watchers_count} watchers, {subscribers_count} stars",
    "repo-fork": u"[GitHub fork] {full_name} (Fork of {parent[full_name]}): "
                 u"{description} - {forks_count} forks / {watchers_count} "
                 u"watchers, {subscribers_count} stars",

    "repo-blob-branch-path": u"[GitHub file] {given[owner]}/{given[repo]}/"
                             u"{given[branch]} - {given[path]} - "
                             u"{commit[author][name]}: {commit[message]} "
                             u"(+{stats[additions]}/-{stats[deletions]}/"
                             u"\u00B1{stats[total]})",
    "repo-blob-hash-path": u"[GitHub file] {given[owner]}/{given[repo]} - "
                           u"{given[path]} - "
                           u"{commit[author][name]}: {commit[message]} "
                           u"(+{stats[additions]}/-{stats[deletions]}/"
                           u"\u00B1{stats[total]})",

    "repo-no-commits": u"[GitHub repo] {given[owner]}/{given[repo]} - No "
                       u"commits found",
    "repo-commits": u"[GitHub repo] {given[owner]}/{given[repo]} - "
                    u"{commits_count} commits by {contributors_count} "
                    u"contributors",
    "repo-commits-branch": u"[GitHub repo] {given[owner]}/{given[repo]} - "
                           u"{commits_count} commits by {contributors_count} "
                           u"contributors",
    "repo-commits-branch-path": u"[GitHub repo] {given[owner]}/{given[repo]} "
                                u"- {commits_count} commits by "
                                u"{contributors_count} contributors",
    "repo-commit-hash": u"[GitHub commit] {given[owner]}/{given[repo]} - "
                        u"{commit[author][name]}: {commit[message]} "
                        u"(+{stats[additions]}/-{stats[deletions]}/"
                        u"\u00B1{stats[total]})",

    "repo-compare": u"[GitHub commit comparison] Status: {status} - "
                    u"Ahead by {ahead_by} commit(s) / "
                    u"behind by {behind_by} commit(s) - {total_commits} "
                    u"commit(s) in total",

    "repo-issue": u"[GitHub issue] {given[owner]}/{given[repo]} #{number} - "
                  u"{user[login]}: {title} ({state}) - {label_list} -"
                  u" Milestone: {milestone[title]} / Assigned: {assigned_name}",
    "repo-issues": u"[GitHub repo] {given[owner]}/{given[repo]} - "
                   u"{total_count} total issues ({open_count} open / "
                   u"{closed_count} closed)",
    "repo-no-issues": u"[GitHub repo] {given[owner]}/{given[repo]} - No "
                      u"issues found",

    "repo-label": u"[GitHub label] {given[owner]}/{given[repo]} - "
                  u"{given[label] - {total_count} issues: "
                  u"{open_count} open / {closed_count} closed",
    "repo-label-no-issues": u"[GitHub label] {given[owner]}/{given[repo]}  - "
                            u"{given[label] - No issues found",
    "repo-labels": u"[GitHub repo] {given[owner]}/{given[repo]} - "
                   u"{labels_count} labels, including {labels_sample}",
    "repo-no-labels": u"[GitHub repo] {given[owner]}/{given[repo]} - No "
                      u"labels found",

    "repo-milestone": u"[GitHub milestone] {given[owner]}/{given[repo]} - "
                      u"{issues_count} issues - {open_issues} open "
                      u"/ {closed_issues} closed ({percent}% complete)",
    "repo-milestone-no-issues": u"[GitHub milestone] "
                                u"{given[owner]}/{given[repo]} - "
                                u"{title} - {description}- No issues "
                                u"found",
    "repo-milestones": u"[GitHub repo {given[owner]}/{given[repo]}] - "
                       u"{total_milestones} milestones - "
                       u"Latest: {title} - {description} | "
                       u"{open_issues} open issues / "
                       u"{closed_issues} closed issues - {percent}%",
    "repo-no-milestones": u"[GitHub repo] {given[owner]}/{given[repo]} - No "
                          u"milestones found",

    "repo-pull": u"[GitHub pull request] {given[owner]}/{given[repo]} "
                 u"#{number} - {user[login]}: {title} ({state}) -"
                 u" Milestone: {milestone[title]} / Assigned: {assigned_name}",
    "repo-pulls": u"[GitHub repo] {given[owner]}/{given[repo]} - "
                  u"{total_count} total pull requests ({open_count} open / "
                  u"{closed_count} closed)",
    "repo-no-pulls": u"[GitHub repo] {given[owner]}/{given[repo]} - No pull "
                     u"requests found",

    "repo-releases": u"[GitHub repo] {given[owner]}/{given[repo]} - "
                     u"{total_releases} releases",
    "repo-no-releases": u"[GitHub repo] {given[owner]}/{given[repo]} - No "
                        u"releases found",
    "repo-releases-latest": u"[GitHub repo] {given[owner]}/{given[repo]} - "
                            u"Latest release: {tag_name} - {name}",
    "repo-releases-tag": u"[GitHub repo] {given[owner]}/{given[repo]} - "
                         u"Specific release: {tag_name} - {name}",

    "repo-stargazers": u"[GitHub repo] {given[owner]}/{given[repo]} - "
                       u"{total_stargazers} stargazers, including "
                       u"{stargazers_sample}",
    "repo-no-stargazers": u"[GitHub repo] {given[owner]}/{given[repo]} - No "
                          u"stargazers found",

    "repo-tags": u"[GitHub repo] {given[owner]}/{given[repo]} - {total_tags} "
                 u"tags, including {tags_sample}",
    "repo-no-tags": u"[GitHub repo] {given[owner]}/{given[repo]} - No tags "
                    u"found",

    "repo-tree-branch": u"[GitHub repo] {given[owner]}/{given[repo]}/"
                        u"{given[branch]} - "
                        u"{commit[author][name]}: {commit[message]} "
                        u"(+{stats[additions]}/-{stats[deletions]}/"
                        u"\u00B1{stats[total]})",
    "repo-tree-branch-path": u"[GitHub repo] {given[owner]}/{given[repo]}/"
                             u"{given[branch]} - {given[path]} - "
                             u"{commit[author][name]}: {commit[message]} "
                             u"(+{stats[additions]}/-{stats[deletions]}/"
                             u"\u00B1{stats[total]})",
    "repo-tree-branch-path-dir": u"[GitHub repo] {given[owner]}/{given[repo]}/"
                             u"{given[branch]} - {given[path]} - "
                             u"{total_files} files",

    "repo-watchers": u"[GitHub repo] {given[owner]}/{given[repo]} - "
                     u"{total_watchers} watchers, including {watchers_sample}",
    "repo-no-watchers": u"[GitHub repo] {given[owner]}/{given[repo]} - No "
                        u"watchers found"
}

DEFAULT_HEADERS = {
    "Accept": "application/json"
}

RANDOM_SAMPLE_SIZE = 5

COMMIT_HASH_REGEX = re.compile(
    "[a-fA-F0-9]{40}", flags=str_to_regex_flags("ui")
)


def sleep(seconds):
    """
    Non-blocking Deferred-based sleep because GitHub requires it for some calls
    :param seconds:
    :return:
    """
    d = Deferred()
    reactor.callLater(seconds, d.callback, seconds)
    return d


class GithubHandler(URLHandler):
    rate_limit = 60
    limit_remaining = 0
    limit_reset = 0

    criteria = {
        "protocol": re.compile(r"http|https", str_to_regex_flags("iu")),
        "domain": lambda x: x in ["www.github.com", "github.com"]
    }

    session = None

    def __init__(self, plugin):
        super(GithubHandler, self).__init__(plugin)

        self.reload()

    @property
    def zen(self):
        return self.plugin.config.get("github", {}).get("zen", False)

    def raise_if_message(self, request):
        try:
            d = request.json()
        except ValueError:
            return  # Not JSON

        if "message" in d:
            if d["message"] == "Not Found":
                raise NotFoundError(d["message"])
            raise GithubError(d["message"])

    def get_string(self, string):
        formatting = self.plugin.config.get("github", {}).get("formatting", {})

        if string not in formatting:
            return strings[string]
        return formatting[string]

    def parse_link_header(self, headers):
        data = {}

        if "Link" not in headers:
            return data

        header = headers["Link"]

        for element in header.split(","):
            element = element.strip()
            url, rel = element.split("; ")
            rel = rel.split("=")[1][1:-1]  # To remove surrounding quotes

            url = url[1:-1]  # Strip < and >

            matches = extract_urls(url)
            parsed_url = self.urls_plugin.match_to_url(matches[0])

            if parsed_url is None:
                self.plugin.logger.error("Unable to parse URL {}".format(url))
                continue

            data[rel] = parsed_url

        return data

    @inlineCallbacks
    def get(self, *args, **kwargs):
        if self.limit_remaining < 1:
            now = datetime.datetime.now()
            then = datetime.datetime.fromtimestamp(int(self.limit_reset))

            if then > now:
                raise GithubHandler("Rate limit met - Try again in {}".format(
                    then - now
                ))

        params = kwargs.get("params", {})
        kwargs["params"] = self.merge_params(params)

        r = yield self.session.get(*args, **kwargs)

        self.raise_if_message(r)

        if "X-RateLimit-Limit" in r.headers:
            self.rate_limit = int(r.headers["X-RateLimit-Limit"])
        if "X-RateLimit-Remaining" in r.headers:
            self.limit_remaining = int(r.headers["X-RateLimit-Remaining"])
        if "X-RateLimit-Reset" in r.headers:
            self.limit_reset = int(r.headers["X-RateLimit-Reset"])

        returnValue(r)

    def merge_params(self, params):
        config_gh = self.plugin.config.get("github", {})

        if "client_id" in config_gh and "client_secret" in config_gh:
            params.update({
                "client_id": config_gh["client_id"],
                "client_secret": config_gh["client_secret"]
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
            if len(target) < 1:  # It's just the front page, don't bother
                returnValue(True)
            elif target[0] in [  # Stupid special cases
                "stars", "trending", "showcases", "explore", "site",
                "security", "contact", "blog", "about", "pricing",
                "issues", "pulls", "settings", "integrations"
            ]:
                message = yield self.gh_zen()
            elif len(target) == 1:  # User or organisation
                message = yield self.gh_user(target[0])
            elif len(target) == 2:  # It's a bare repo
                message = yield self.gh_repo(target[0], target[1])
            else:  # It's a repo subsection
                if target[2] == "commits":
                    if len(target) == 3:
                        message = yield self.gh_repo_commits(target[0],
                                                             target[1])
                    elif len(target) == 4:
                        message = yield self.gh_repo_commits_branch(
                            target[0], target[1], target[3]
                        )
                    else:
                        message = yield self.gh_repo_commits_branch_path(
                            target[0], target[1], target[3], target[4]
                        )
                elif target[2] == "commit":
                    if len(target) == 4:
                        message = yield self.gh_repo_commit_hash(
                            target[0], target[1], target[3]
                        )
                elif target[2] == "compare":
                    if len(target) == 4:
                        left, right = target[3].split("...", 1)
                        message = yield self.gh_repo_compare(
                            target[0], target[1], left, right
                        )
                    # GitHub 404s without two commits to compare, so do nothing
                elif target[2] == "issues":
                    if len(target) == 3:
                        message = yield self.gh_repo_issues(target[0],
                                                            target[1])
                    else:
                        message = yield self.gh_repo_issues_issue(
                            target[0], target[1], target[3]
                        )
                elif target[2] == "pulls":
                    message = yield self.gh_repo_pulls(target[0], target[1])
                elif target[2] == "pull":
                    if len(target) == 4:
                        message = yield self.gh_repo_pulls_pull(
                            target[0], target[1], target[3]
                        )
                    # GitHub 404s without a PR ID, so do nothing
                elif target[2] == "tags":
                    message = yield self.gh_repo_tags(target[0], target[1])
                elif target[2] == "labels":
                    if len(target) == 3:
                        message = yield self.gh_repo_labels(target[0],
                                                            target[1])
                    else:
                        message = yield self.gh_repo_labels_label(
                            target[0], target[1], target[3]
                        )
                elif target[2] == "milestones":
                    if len(target) == 3:
                        message = yield self.gh_repo_milestones(
                            target[0], target[1]
                        )
                    else:
                        message = yield self.gh_repo_milestones_milestone(
                            target[0], target[1], target[3]
                        )
                elif target[2] == "releases":
                    if len(target) == 3:
                        message = yield self.gh_repo_releases(target[0],
                                                              target[1])
                    elif len(target) == 4:
                        if target[3] == "latest":
                            message = yield self.gh_repo_releases_latest(
                                target[0], target[1]
                            )
                        else:
                            message = yield self.gh_repo_releases_tag(
                                target[0], target[1], target[3]
                            )
                    elif len(target) == 5:
                        if target[3] == "tag":
                            message = yield self.gh_repo_releases_tag(
                                target[0], target[1], target[4]
                            )
                    elif len(target) == 6:
                        if target[3] == "download":
                            message = yield self.gh_repo_releases_download(
                                target[0], target[1], target[4], target[5]
                            )
                elif target[2] == "wiki":
                    message = yield self.gh_repo_wiki(target[0], target[1])
                elif target[2] == "pulse":
                    message = yield self.gh_repo_pulse(target[0], target[1])
                elif target[2] == "graphs":
                    message = yield self.gh_repo_graphs(target[0], target[1])
                elif target[2] == "settings":
                    message = yield self.gh_repo_settings(target[0], target[1])
                elif target[2] == "tree":
                    if len(target) == 4:
                        message = yield self.gh_repo_tree_branch(
                            target[0], target[1], target[3]
                        )
                    elif len(target) > 4:
                        message = yield self.gh_repo_tree_branch_path(
                            target[0], target[1], target[3],
                            "/".join(target[4:])
                        )
                    # GitHub 404s without a branch, so do nothing
                elif target[2] == "blob":
                    if len(target) == 5:
                        # Could be either a branch and path, or hash and path
                        if COMMIT_HASH_REGEX.match(target[3]):
                            message = yield self.gh_repo_blob_hash_path(
                                target[0], target[1], target[3], target[4]
                            )
                        else:
                            message = yield self.gh_repo_blob_branch_path(
                                target[0], target[1], target[3], target[4]
                            )
                    # GitHub 404s without a hash/branch and path, so do nothing
                elif target[2] == "blame":
                    if len(target) == 5:
                        message = yield self.gh_repo_blame_branch_path(
                            target[0], target[1], target[3], target[4]
                        )
                    # GitHub 404s without a branch and path, so do nothing
                elif target[2] == "watchers":
                    message = yield self.gh_repo_watchers(target[0], target[1])
                elif target[2] == "stargazers":
                    message = yield self.gh_repo_stargazers(target[0],
                                                            target[1])
        except NotFoundError:
            returnValue(True)
            return
        except GithubError as e:
            self.plugin.logger.error(e.message)
            returnValue(True)
        except ShutUpException:
            returnValue(False)
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
    def gh_user(self, user):  # User or org
        try:  # Let's see if it's a user
            r = yield self.get(
                URL_USER.format(user), headers=DEFAULT_HEADERS
            )

            data = r.json()

            data["given"] = {
                "user": user
            }

            returnValue(self.get_string("user").format(**data))
        except Exception as e:  # Let's see if it's an organisation, then
            self.plugin.logger.debug(
                "Error getting GitHub user {0}: {1}".format(user), e
            )
            self.plugin.logger.debug(
                "Checking to see if they're an organisation instead."
            )

            r = yield self.get(
                URL_ORG.format(user), headers=DEFAULT_HEADERS
            )

            data = r.json()

            data["given"] = {
                "user": user
            }

            returnValue(self.get_string("org").format(**data))

    @inlineCallbacks
    def gh_repo(self, owner, repo):
        # Preview header for licensing info
        headers = DEFAULT_HEADERS
        headers["Accept"] = "application/vnd.github.drax-preview+json"

        r = yield self.get(
            URL_REPO.format(owner, repo), headers=headers
        )

        self.raise_if_message(r)

        data = r.json()

        data["given"] = {
            "owner": owner,
            "repo": repo
        }

        if data["fork"]:
            returnValue(self.get_string("repo-fork").format(**data))
        else:
            returnValue(self.get_string("repo").format(**data))

    @inlineCallbacks
    def gh_repo_commits(self, owner, repo):
        r = yield self.get(
            URL_COMMITS.format(owner, repo), headers=DEFAULT_HEADERS
        )
        self.raise_if_message(r)

        commits = r.json()

        if len(commits) < 1:
            data = {
                "given": {
                    "owner": owner,
                    "repo": repo
                }
            }

            returnValue(self.get_string("repo-no-commits").format(**data))
            return

        r = yield self.get(
            URL_STATS_CONTRIBUTORS.format(owner, repo), headers=DEFAULT_HEADERS
        )

        tries = 0

        while r.status_code == 202:
            if tries >= 5:
                self.plugin.logger.warning(
                    "Unable to get stats for {}/{}".format(owner, repo)
                )

                returnValue(None)
                return

            # Wait for 1 second for GitHub to cache the result
            # Don't worry, this isn't a blocking sleep
            _ = yield sleep(1)

            r = yield self.get(
                URL_STATS_CONTRIBUTORS.format(owner, repo),
                headers=DEFAULT_HEADERS
            )

            tries += 1

        contributors = r.json()

        r = yield self.get(
            URL_COMMITS.format(owner, repo), headers=DEFAULT_HEADERS,
            params={"per_page": 1}
        )

        link_header = self.parse_link_header(r.headers)

        total_commits = 0

        if "last" in link_header:
            if "page" in link_header["last"].query:
                total_commits = int(link_header["last"].query["page"])

        if total_commits < 1:
            for c in contributors:
                total_commits += c["total"]

        data = {
            "commits": commits,
            "commits_count": total_commits,
            "contributors": contributors,
            "contributors_count": len(contributors),

            "given": {
                "owner": owner,
                "repo": repo
            }
        }

        returnValue(self.get_string("repo-commits").format(**data))

    @inlineCallbacks
    def gh_repo_commits_branch(self, owner, repo, branch):
        r = yield self.get(
            URL_COMMITS.format(owner, repo), headers=DEFAULT_HEADERS,
            params={"sha": branch}
        )
        self.raise_if_message(r)

        commits = r.json()

        if len(commits) < 1:
            data = {
                "given": {
                    "owner": owner,
                    "repo": repo
                }
            }

            returnValue(self.get_string("repo-no-commits").format(**data))
            return

        r = yield self.get(
            URL_STATS_CONTRIBUTORS.format(owner, repo), headers=DEFAULT_HEADERS
        )

        tries = 0

        while r.status_code == 202:
            if tries >= 5:
                self.plugin.logger.warning(
                    "Unable to get stats for {}/{}".format(owner, repo)
                )

                returnValue(None)
                return

            # Wait for 1 second for GitHub to cache the result
            # Don't worry, this isn't a blocking sleep
            _ = yield sleep(1)

            r = yield self.get(
                URL_STATS_CONTRIBUTORS.format(owner, repo),
                headers=DEFAULT_HEADERS
            )

            tries += 1

        contributors = r.json()

        r = yield self.get(
            URL_COMMITS.format(owner, repo), headers=DEFAULT_HEADERS,
            params={"per_page": 1, "sha": branch}
        )

        link_header = self.parse_link_header(r.headers)

        total_commits = 0

        if "last" in link_header:
            if "page" in link_header["last"].query:
                total_commits = int(link_header["last"].query["page"])

        if total_commits < 1:
            for c in contributors:
                total_commits += c["total"]

        data = {
            "commits": commits,
            "commits_count": total_commits,
            "contributors": contributors,
            "contributors_count": len(contributors),

            "given": {
                "owner": owner,
                "repo": repo,
                "branch": branch
            }
        }

        returnValue(self.get_string("repo-commits-branch").format(**data))

    @inlineCallbacks
    def gh_repo_commits_branch_path(self, owner, repo, branch, path):
        r = yield self.get(
            URL_COMMITS.format(owner, repo),
            headers=DEFAULT_HEADERS,
            params={"sha": branch, "path": path}
        )
        self.raise_if_message(r)

        commits = r.json()

        if len(commits) < 1:
            data = {
                "given": {
                    "owner": owner,
                    "repo": repo
                }
            }

            returnValue(self.get_string("repo-no-commits").format(**data))
            return

        r = yield self.get(
            URL_STATS_CONTRIBUTORS.format(owner, repo), headers=DEFAULT_HEADERS
        )

        tries = 0

        while r.status_code == 202:
            if tries >= 5:
                self.plugin.logger.warning(
                    "Unable to get stats for {}/{}".format(owner, repo)
                )

                returnValue(None)
                return

            # Wait for 1 second for GitHub to cache the result
            # Don't worry, this isn't a blocking sleep
            _ = yield sleep(1)

            r = yield self.get(
                URL_STATS_CONTRIBUTORS.format(owner, repo),
                headers=DEFAULT_HEADERS
            )

            tries += 1

        contributors = r.json()

        r = yield self.get(
            URL_COMMITS.format(owner, repo), headers=DEFAULT_HEADERS,
            params={"per_page": 1, "sha": branch, "path": path}
        )

        link_header = self.parse_link_header(r.headers)

        total_commits = 0

        if "last" in link_header:
            if "page" in link_header["last"].query:
                total_commits = int(link_header["last"].query["page"])

        if total_commits < 1:
            for c in contributors:
                total_commits += c["total"]

        data = {
            "commits": commits,
            "commits_count": total_commits,
            "contributors": contributors,
            "contributors_count": len(contributors),

            "given": {
                "owner": owner,
                "repo": repo,
                "branch": branch,
                "path": path
            }
        }

        returnValue(self.get_string("repo-commits-branch-path").format(**data))

    @inlineCallbacks
    def gh_repo_commit_hash(self, owner, repo, hash):
        r = yield self.get(
            URL_COMMIT.format(owner, repo, hash), headers=DEFAULT_HEADERS
        )
        self.raise_if_message(r)

        data = r.json()

        data["given"] = {
            "owner": owner,
            "repo": repo,
            "hash": hash
        }

        returnValue(self.get_string("repo-commit-hash").format(**data))

    @inlineCallbacks
    def gh_repo_compare(self, owner, repo, left, right):
        r = yield self.get(
            URL_COMMIT_RANGE.format(owner, repo, left, right),
            headers=DEFAULT_HEADERS
        )
        self.raise_if_message(r)

        data = r.json()

        data["given"] = {
            "owner": owner,
            "repo": repo,
            "left": left,
            "right": right
        }

        returnValue(self.get_string("repo-compare").format(**data))

    @inlineCallbacks
    def gh_repo_issues(self, owner, repo):
        total = 0
        open = 0

        # First, we get the total count of all issues
        r = yield self.get(
            URL_ISSUES.format(owner, repo), headers=DEFAULT_HEADERS,
            params={"state": "all", "filter": "is:issue", "per_page": 1}
        )
        self.raise_if_message(r)

        if len(r.json()) < 1:
            data = {
                "given": {
                    "owner": owner,
                    "repo": repo
                }
            }

            returnValue(self.get_string("repo-no-issues").format(**data))
            return

        link_header = self.parse_link_header(r.headers)

        if "last" in link_header:
            if "page" in link_header["last"].query:
                total = int(link_header["last"].query["page"])

        # Next, we get the number of open issues
        r = yield self.get(
            URL_ISSUES.format(owner, repo), headers=DEFAULT_HEADERS,
            params={"state": "open", "filter": "all", "per_page": 1}
        )

        link_header = self.parse_link_header(r.headers)

        if "last" in link_header:
            if "page" in link_header["last"].query:
                open = int(link_header["last"].query["page"])

        # And from that, we infer the closed issues, thus saving a request
        closed = total - open

        data = {
            "closed_count": closed,
            "open_count": open,
            "total_count": total,

            "given": {
                "owner": owner,
                "repo": repo
            }
        }

        returnValue(self.get_string("repo-issues").format(**data))

    @inlineCallbacks
    def gh_repo_issues_issue(self, owner, repo, issue):
        r = yield self.get(
            URL_ISSUE.format(owner, repo, issue), headers=DEFAULT_HEADERS,
        )
        self.raise_if_message(r)

        data = r.json()

        data["given"] = {
            "owner": owner,
            "repo": repo,
            "issues": issue
        }

        labels = [l["name"] for l in data["labels"]]

        if len(labels) > 1:
            data["label_list"] = (
                ", ".join(labels[:-1]) + " & " + labels[-1]
            )
        elif len(labels) == 1:
            data["label_list"] = labels[0]
        else:
            data["label_list"] = "No labels"

        if data["assignee"]:
            data["assigned_name"] = data["assignee"]["login"]
        else:
            data["assigned_name"] = None

        returnValue(self.get_string("repo-issue").format(**data))

    @inlineCallbacks
    def gh_repo_pulls(self, owner, repo):
        open = 0
        total = 0

        r = yield self.get(
            URL_PULLS.format(owner, repo), headers=DEFAULT_HEADERS,
            params={"state": "all", "filter": "all", "per_page": 1}
        )
        self.raise_if_message(r)

        if len(r.json()) < 1:
            data = {
                "given": {
                    "owner": owner,
                    "repo": repo
                }
            }

            returnValue(self.get_string("repo-no-pulls").format(**data))
            return

        link_header = self.parse_link_header(r.headers)

        if "last" in link_header:
            if "page" in link_header["last"].query:
                total = int(link_header["last"].query["page"])
        else:
            total = len(r.json())

        r = yield self.get(
            URL_PULLS.format(owner, repo), headers=DEFAULT_HEADERS,
            params={"state": "open", "filter": "all", "per_page": 1}
        )

        link_header = self.parse_link_header(r.headers)

        if "last" in link_header:
            if "page" in link_header["last"].query:
                open = int(link_header["last"].query["page"])
        else:
            open = len(r.json())

        closed = total - open

        data = {
            "closed_count": closed,
            "open_count": open,
            "total_count": total,

            "given": {
                "owner": owner,
                "repo": repo
            }
        }

        returnValue(self.get_string("repo-pulls").format(**data))

    @inlineCallbacks
    def gh_repo_pulls_pull(self, owner, repo, pull):
        r = yield self.get(
            URL_PULL.format(owner, repo, pull), headers=DEFAULT_HEADERS
        )
        self.raise_if_message(r)

        data = r.json()

        data["given"] = {
            "owner": owner,
            "repo": repo,
            "pull": pull
        }

        if "milestone" not in data or not data["milestone"]:
            data["milestone"] = {
                "title": None
            }
        if "assignee" not in data or not data["assignee"]:
            data["assigned_name"] = None
        else:
            data["assigned_name"] = data["assignee"]["login"]

        returnValue(self.get_string("repo-pull").format(**data))

    @inlineCallbacks
    def gh_repo_labels(self, owner, repo):
        r = yield self.get(
            URL_LABELS.format(owner, repo), headers=DEFAULT_HEADERS
        )
        self.raise_if_message(r)

        data = r.json()

        if len(data) < 1:
            data = {
                "given": {
                    "owner": owner,
                    "repo": repo
                }
            }
            returnValue(self.get_string("repo-no-labels").format(**data))
            return

        if len(data) > 5:
            labels = [
                l["name"] for l in random.sample(data, 5)
            ]
        else:
            labels = [
                l["name"] for l in data
            ]

        labels_sample = ", ".join(labels[:-1]) + " & " + labels[-1]

        total = 0

        r = yield self.get(
            URL_LABELS.format(owner, repo), headers=DEFAULT_HEADERS,
            params={"per_page": 1}
        )

        link_header = self.parse_link_header(r.headers)

        if "last" in link_header:
            if "page" in link_header["last"].query:
                total = int(link_header["last"].query["page"])

        data = {
            "labels": data,
            "labels_sample": labels_sample,
            "labels_count": total,

            "given": {
                "owner": owner,
                "repo": repo
            }
        }

        returnValue(self.get_string("repo-labels").format(**data))

    @inlineCallbacks
    def gh_repo_labels_label(self, owner, repo, label):
        total = 0
        open = 0

        # First, we get the total count of all issues
        r = yield self.get(
            URL_ISSUES.format(owner, repo), headers=DEFAULT_HEADERS,
            params={
                "state": "all", "filter": "all", "per_page": 1, "labels": label
            }
        )
        self.raise_if_message(r)

        link_header = self.parse_link_header(r.headers)

        if "last" in link_header:
            if "page" in link_header["last"].query:
                total = int(link_header["last"].query["page"])

        # Next, we get the number of open issues
        r = yield self.get(
            URL_ISSUES.format(owner, repo), headers=DEFAULT_HEADERS,
            params={
                "state": "open", "filter": "all", "per_page": 1,
                "labels": label
            }
        )

        if len(r.json()) < 1:
            data = {
                "given": {
                    "owner": owner,
                    "repo": repo,
                    "label": label
                }
            }
            returnValue(self.get_string("repo-label-no-issues").format(**data))
            return

        link_header = self.parse_link_header(r.headers)

        if "last" in link_header:
            if "page" in link_header["last"].query:
                open = int(link_header["last"].query["page"])

        # And from that, we infer the closed issues, thus saving a request
        closed = total - open

        data = {
            "given": {
                "owner": owner,
                "repo": repo,
                "label": label
            },
            "closed_count": closed,
            "open_count": open,
            "total_count": total
        }

        returnValue(self.get_string("repo-label").format(**data))

    @inlineCallbacks
    def gh_repo_milestones(self, owner, repo):
        r = yield self.get(
            URL_MILESTONES.format(owner, repo),
            headers=DEFAULT_HEADERS,
            params={"state": "all", "per_page": 1}
        )
        self.raise_if_message(r)

        if len(r.json()) < 1:
            data = {
                "given": {
                    "owner": owner,
                    "repo": repo
                }
            }

            returnValue(self.get_string("repo-no-milestones").format(**data))
            return

        total = 0

        link_header = self.parse_link_header(r.headers)

        if "last" in link_header:
            if "page" in link_header["last"].query:
                total = int(link_header["last"].query["page"])

        data = r.json()

        data = data[0]
        data["issues_count"] = data["open_issues"] + data["closed_issues"]

        percent = ((1.0 * data["closed_issues"]) / data["issues_count"]) * 100
        data["percent"] = percent

        data["total_milestones"] = total

        data["given"] = {
            "owner": owner,
            "repo": repo,
        }

        returnValue(self.get_string("repo-milestones").format(**data))

    @inlineCallbacks
    def gh_repo_milestones_milestone(self, owner, repo, milestone):
        r = yield self.get(
            URL_MILESTONE.format(owner, repo, milestone),
            headers=DEFAULT_HEADERS
        )
        self.raise_if_message(r)

        data = r.json()

        if "issues_count" not in data:
            data["given"] = {
                "owner": owner,
                "repo": repo,
                "milestone": milestone
            }
            data["percent"] = 0
            returnValue(
                self.get_string("repo-milestone-no-issues").format(**data)
            )

        data["issues_count"] = data["open_issues"] + data["closed_issues"]

        percent = ((1.0 * data["closed_issues"]) / data["issues_count"]) * 100
        data["percent"] = percent

        data["given"] = {
            "owner": owner,
            "repo": repo,
            "milestone": milestone
        }

        returnValue(self.get_string("repo-milestone").format(**data))

    @inlineCallbacks
    def gh_repo_tree_branch(self, owner, repo, branch):
        r = yield self.get(
            URL_TREE.format(owner, repo, branch),
            headers=DEFAULT_HEADERS
        )
        self.raise_if_message(r)

        data = r.json()
        sha = data["sha"]

        r = yield self.get(
            URL_COMMIT.format(owner, repo, sha),
            headers=DEFAULT_HEADERS
        )

        data = r.json()

        data["given"] = {
            "owner": owner,
            "repo": repo,
            "branch": branch
        }

        returnValue(self.get_string("repo-tree-branch").format(**data))

    @inlineCallbacks
    def gh_repo_tree_branch_path(self, owner, repo, branch, path):
        r = yield self.get(
            URL_GET_CONTENTS.format(owner, repo, path),
            headers=DEFAULT_HEADERS,
            params={"ref": branch}
        )
        self.raise_if_message(r)

        data = r.json()

        if isinstance(data, list):
            data = {
                "total_files": len(data),
                "given": {
                    "owner": owner,
                    "repo": repo,
                    "branch": branch,
                    "path": path
                }
            }

            returnValue(self.get_string("repo-tree-branch-path-dir").format(
                **data
            ))
            return

        sha = data["sha"]

        r = yield self.get(
            URL_COMMIT.format(owner, repo, sha),
            headers=DEFAULT_HEADERS
        )

        data = r.json()

        data["given"] = {
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "path": path
        }

        returnValue(self.get_string("repo-tree-branch-path").format(**data))

    @inlineCallbacks
    def gh_repo_blob_branch_path(self, owner, repo, branch, path):
        r = yield self.get(
            URL_COMMITS.format(owner, repo),
            headers=DEFAULT_HEADERS,
            params={"path": path, "sha": branch, "per_page": 1}
        )
        self.raise_if_message(r)

        data = r.json()

        if len(data) < 1:
            returnValue(None)
            return

        data = data[0]

        r = yield self.get(
            URL_COMMIT.format(owner, repo, data["sha"]),
            headers=DEFAULT_HEADERS,
            params={"path": path}
        )
        self.raise_if_message(r)

        data = r.json()

        data["given"] = {
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "path": path
        }

        returnValue(self.get_string("repo-blob-branch-path").format(**data))

    @inlineCallbacks
    def gh_repo_blob_hash_path(self, owner, repo, hash, path):
        r = yield self.get(
            URL_COMMITS.format(owner, repo),
            headers=DEFAULT_HEADERS,
            params={"path": path, "sha": hash, "per_page": 1}
        )
        self.raise_if_message(r)

        data = r.json()

        if len(data) < 1:
            returnValue(None)
            return

        data = data[0]

        r = yield self.get(
            URL_COMMIT.format(owner, repo, data["sha"]),
            headers=DEFAULT_HEADERS,
            params={"path": path}
        )
        self.raise_if_message(r)

        data = r.json()

        data["given"] = {
            "owner": owner,
            "repo": repo,
            "hash": hash,
            "path": path
        }

        returnValue(self.get_string("repo-blob-hash-path").format(**data))

    @inlineCallbacks
    def gh_repo_blame_branch_path(self, owner, repo, branch, path):
        # No API call, so let's delegate.
        d = yield self.gh_repo(owner, repo)
        returnValue(d)

    @inlineCallbacks
    def gh_repo_watchers(self, owner, repo):
        r = yield self.get(
            URL_WATCHERS.format(owner, repo),
            headers=DEFAULT_HEADERS,
            params={"per_page": 1}
        )
        self.raise_if_message(r)

        if len(r.json()) < 1:
            data = {
                "given": {
                    "owner": owner,
                    "repo": repo
                }
            }

            returnValue(self.get_string("repo-no-watchers").format(**data))
            return

        total = 0

        link_header = self.parse_link_header(r.headers)

        if "last" in link_header:
            if "page" in link_header["last"].query:
                total = int(link_header["last"].query["page"])

        r = yield self.get(
            URL_WATCHERS.format(owner, repo),
            headers=DEFAULT_HEADERS
        )
        data = r.json()

        if total == 0:
            total = len(data)

        if total > 5:
            users = random.sample(data, 5)
        else:
            users = data

        users = [user["login"] for user in users]

        sample = ", ".join(users[:-1]) + " & " + users[-1]

        data = {
            "total_watchers": total,
            "watchers_sample": sample,

            "given": {
                "owner": owner,
                "repo": repo
            }
        }

        returnValue(self.get_string("repo-watchers").format(**data))

    @inlineCallbacks
    def gh_repo_stargazers(self, owner, repo):
        r = yield self.get(
            URL_STARGAZERS.format(owner, repo),
            headers=DEFAULT_HEADERS,
            params={"per_page": 1}
        )
        self.raise_if_message(r)

        if len(r.json()) < 1:
            data = {
                "given": {
                    "owner": owner,
                    "repo": repo
                }
            }

            returnValue(self.get_string("repo-no-stargazers").format(**data))
            return

        total = 0

        link_header = self.parse_link_header(r.headers)

        if "last" in link_header:
            if "page" in link_header["last"].query:
                total = int(link_header["last"].query["page"])

        r = yield self.get(
            URL_STARGAZERS.format(owner, repo),
            headers=DEFAULT_HEADERS
        )
        data = r.json()

        if total == 0:
            total = len(data)

        if total > 5:
            users = random.sample(data, 5)
        else:
            users = data

        users = [user["login"] for user in users]

        sample = ", ".join(users[:-1]) + " & " + users[-1]

        data = {
            "total_stargazers": total,
            "stargazers_sample": sample,

            "given": {
                "owner": owner,
                "repo": repo
            }
        }

        returnValue(self.get_string("repo-stargazers").format(**data))

    @inlineCallbacks
    def gh_repo_wiki(self, owner, repo):
        # No API call, so let's delegate.
        d = yield self.gh_repo(owner, repo)
        returnValue(d)

    @inlineCallbacks
    def gh_repo_pulse(self, owner, repo):
        # No API call, so let's delegate.
        d = yield self.gh_repo(owner, repo)
        returnValue(d)

    @inlineCallbacks
    def gh_repo_graphs(self, owner, repo):
        # No API call, so let's delegate.
        d = yield self.gh_repo(owner, repo)
        returnValue(d)

    @inlineCallbacks
    def gh_repo_settings(self, owner, repo):
        # No API call, so let's delegate.
        d = yield self.gh_repo(owner, repo)
        returnValue(d)

    @inlineCallbacks
    def gh_repo_releases(self, owner, repo):
        r = yield self.get(
            URL_RELEASES.format(owner, repo),
            headers=DEFAULT_HEADERS,
            params={"per_page": 1}
        )
        self.raise_if_message(r)

        if len(r.json()) < 1:
            data = {
                "given": {
                    "owner": owner,
                    "repo": repo
                }
            }

            returnValue(self.get_string("repo-no-releases").format(**data))
            return

        total = 0

        link_header = self.parse_link_header(r.headers)

        if "last" in link_header:
            if "page" in link_header["last"].query:
                total = int(link_header["last"].query["page"])

        if total == 0:
            total = len(r.json())

        data = {
            "total_releases": total,

            "given": {
                "owner": owner,
                "repo": repo
            }
        }

        returnValue(self.get_string("repo-releases").format(**data))

    @inlineCallbacks
    def gh_repo_releases_latest(self, owner, repo):
        r = yield self.get(
            URL_RELEASE.format(owner, repo, "latest"),
            headers=DEFAULT_HEADERS,
            params={"per_page": 1}
        )
        self.raise_if_message(r)

        data = r.json()

        data["given"] = {
            "owner": owner,
            "repo": repo
        }

        returnValue(self.get_string("repo-releases-latest").format(**data))

    @inlineCallbacks
    def gh_repo_releases_tag(self, owner, repo, tag):
        r = yield self.get(
            URL_RELEASE_TAGS.format(owner, repo, tag),
            headers=DEFAULT_HEADERS
        )
        self.raise_if_message(r)

        data = r.json()

        data["given"] = {
            "owner": owner,
            "repo": repo,
            "tag": tag
        }

        returnValue(self.get_string("repo-releases-tag").format(**data))

    @inlineCallbacks
    def gh_repo_releases_download(self, owner, repo, tag, filename):
        # No API call, so let's delegate.
        d = self.gh_repo(owner, repo)
        returnValue(d)

    @inlineCallbacks
    def gh_repo_tags(self, owner, repo):
        r = yield self.get(
            URL_TAGS.format(owner, repo),
            headers=DEFAULT_HEADERS,
            params={"per_page": 1}
        )
        self.raise_if_message(r)

        if len(r.json()) < 1:
            data = {
                "given": {
                    "owner": owner,
                    "repo": repo
                }
            }

            returnValue(self.get_string("repo-no-tags").format(**data))
            return

        total = 0

        link_header = self.parse_link_header(r.headers)

        if "last" in link_header:
            if "page" in link_header["last"].query:
                total = int(link_header["last"].query["page"])

        if total == 0:
            total = len(r.json())

        r = yield self.get(
            URL_TAGS.format(owner, repo),
            headers=DEFAULT_HEADERS
        )

        data = r.json()

        if len(data) > 5:
            tags = random.sample(data, 5)
        else:
            tags = data

        tags = [tag["name"] for tag in tags]

        sample = ", ".join(tags[:-1]) + " & " + tags[-1]

        data = {
            "total_tags": total,
            "tags_sample": sample,

            "given": {
                "owner": owner,
                "repo": repo
            }
        }

        returnValue(self.get_string("repo-tags").format(**data))

    @inlineCallbacks
    def gh_zen(self):
        if self.zen:
            r = yield self.get(
                URL_ZEN,
                headers=DEFAULT_HEADERS
            )

            returnValue(u"[GitHub] {}".format(r.text))
        else:
            raise ShutUpException()

    def reload(self):
        self.teardown()

        self.session = Session()

    def teardown(self):
        if self.session is not None:
            self.session.close()


class GithubError(Exception):
    pass


class NotFoundError(GithubError):
    pass


class ShutUpException(Exception):
    pass
