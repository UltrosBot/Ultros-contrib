# coding=utf-8
import pprint
import re

from twisted.internet.defer import inlineCallbacks, returnValue
from txrequests import Session

from plugins.urls.handlers.handler import URLHandler
from utils.misc import str_to_regex_flags

__author__ = 'Gareth Coles'

BASE_URL = "https://api.github.com"

URL_USER = BASE_URL + "/users/{0}"
URL_ORG = BASE_URL + "/orgs/{0}"
URL_REPO = BASE_URL + "/repos/{0}/{1}"

URL_RELEASES = URL_REPO + "/releases"
URL_RELEASE = URL_RELEASES + "/{2}"

URL_ISSUES = URL_REPO + "/issues"
URL_ISSUES_OPEN = URL_ISSUES + "?state=open"
URL_ISSUES_CLOSED = URL_ISSUES + "?state=closed"
URL_ISSUE = URL_ISSUES + "/{2}"

URL_COMMITS = URL_REPO + "/commits"
URL_COMMIT = URL_COMMITS + "/{2}"
URL_COMMIT_RANGE = URL_COMMITS + "/{2}...{3}"

URL_PULLS = URL_REPO + "/pulls"
URL_PULLS_OPEN = URL_PULLS + "?state=open"
URL_PULLS_CLOSED = URL_PULLS + "?state=closed"
URL_PULL = URL_PULLS + "/{2}"

strings = {
    "USER": u"[GitHub user] %s (%s followers) - %s repos, %s gists",
    "USER_ADMIN": u"[GitHub admin] %s (%s followers) - %s repos, %s "
                  u"gists",
    "ORG": u"[GitHub org] %s (%s followers) - %s repos, %s gists",

    "REPO": u"[GitHub repo / No forks] %s (%s stars / %s watchers) - "
            u"%s open issues - %s",
    "REPO_FORKS": u"[GitHub repo / %s forks] %s (%s stars / %s "
                  u"watchers) - %s open issues - %s",
    "REPO_FORK": u"[GitHub repo / fork of {parent[full_name]}] {full_name} "
                 u"({stargazers_count} stars / {watchers_count} watchers) - "
                 u"{open_issues_count} open issues - {description}",

    "RELEASES": u"[GitHub repo / %s releases] %s/%s - Latest: %s by "
                u"%s (%s downloads)",
    "RELEASE": u"[GitHub release] %s/%s/%s by %s - %s assets, %s "
               u"downloads",
    "RELEASE_NONE": u"[GitHub repo] %s/%s - No releases found",

    "ISSUES": u"[GitHub repo / %s issues] %s/%s - %s open, %s closed",
    "ISSUE": u"[GitHub issue] %s/%s/%s by %s (%s) - %s (%s)",
    "ISSUE_MILESTONE": u"[GitHub issue] %s/%s/%s %s by %s (%s) - %s (%s)",
    "ISSUE_ASSIGNED": u"[GitHub issue] %s/%s/%s by %s (%s) - %s (%s) "
                      u"- Assigned to %s",
    "ISSUE_ASSIGNED_MILESTONE": u"[GitHub issue] %s/%s/%s %s by %s "
                                u"(%s) - %s (%s) - Assigned to %s",

    "COMMITS": u"[GitHub repo / last %s commits] %s/%s - %s commits by"
               u" %s authors.",
    "COMMITS_COMMIT": u"[GitHub commit] %s/%s +%s/-%s/±%s (%s files) "
                      u"by %s - %s",
    "COMMITS_COMPARE": u"[GitHub commit comparison] %s/%s - Comparing "
                       u"%s by %s and %s by %s with %s intermediary "
                       u"commits",

    "PULLS": u"[GitHub repo / %s pull requests] %s/%s - %s open, %s "
             u"closed",
    "PULLS_PULL": u"[GitHub pull request] %s/%s/%s by %s (%s) - %s",
}

RANDOM_SAMPLE_SIZE = 5

COMMIT_HASH_REGEX = re.compile(
    "[a-fA-F0-9]{40}", flags=str_to_regex_flags("ui")
)


class GithubHandler(URLHandler):
    criteria = {
        "protocol": re.compile(r"http|https", str_to_regex_flags("iu")),
        "domain": lambda x: x in ["www.github.com", "github.com"]
    }

    session = None

    def __init__(self, plugin):
        super(GithubHandler, self).__init__(plugin)

        self.reload()

    @inlineCallbacks
    def call(self, url, context):
        target = url.path.split("/")

        if "" in target:
            target.remove("")
        if " " in target:
            target.remove(" ")

        message = ""

        if len(target) < 1:  # It's just the front page, don't bother
            returnValue(True)
        elif len(target) == 1:  # User or organisation
            message = yield self.gh_user(target[0])

        elif len(target) == 2:  # It's a bare repo
            message = yield self.gh_repo(target[0], target[1])

            # TODO: Message + separation based on fork status
        else:  # It's a repo subsection
            """
            Possible paths:

            [owner, repo]
            [owner, repo, commits]
            [owner, repo, commits, *branch]
            [owner, repo, commits, *branch, *path]
            [owner, repo, commit, *hash]
            [owner, repo, compare, *hashes]
            [owner, repo, issues]
            [owner, repo, issues, *issue]
            [owner, repo, pulls]
            [owner, repo, pull, *pull]
            [owner, repo, labels]
            [owner, repo, labels, *label]
            [owner, repo, milestones]
            [owner, repo, milestones, *milestone]
            [owner, repo, wiki]+  (Treat as bare)
            [owner, repo, pulse]+  (Treat as bare)
            [owner, repo, graphs]+  (Treat as bare)
            [owner, repo, settings]+  (Treat as bare)
            [owner, repo, tree, *branch]
            [owner, repo, tree, *branch, *path]
            [owner, repo, blob, *branch, *path]
            [owner, repo, blob, *hash, *path]
            [owner, repo, blame, *branch, *path]
            [owner, repo, watchers]
            [owner, repo, stargazers]
            """

            if target[2] == "commits":
                if len(target) == 3:
                    pass  # Commit list
                elif len(target) == 4:
                    pass  # Specific branch
                else:
                    pass  # Specific file in a branch
            elif target[2] == "commit":
                if len(target) == 4:
                    pass  # Specific commit
            elif target[2] == "compare":
                if len(target) == 4:
                    left, right = target[3].split("...", 1)
                    pass  # Comparison of two commits
                # GitHub 404s without two commits to compare, so do nothing
            elif target[2] == "issues":
                if len(target) == 3:
                    pass  # Issue list
                else:
                    pass  # Specific issue
            elif target[2] == "pulls":
                pass  # Pull request list
            elif target[2] == "pull":
                if len(target) == 4:
                    pass  # Specific PR
                # GitHub 404s without a PR ID, so do nothing
            elif target[2] == "labels":
                if len(target) == 3:
                    pass  # Label list
                else:
                    pass  # Specific label
            elif target[2] == "milestones":
                if len(target) == 3:
                    pass  # Milestone list
                else:
                    pass  # Specific milestone
            elif target[2] == "wiki":
                pass  # Wiki page
            elif target[2] == "puse":
                pass  # Pulse page
            elif target[2] == "graphs":
                pass  # Graphs page
            elif target[2] == "settings":
                pass  # Settings page
            elif target[2] == "tree":
                if len(target) == 4:
                    pass  # File tree of specific branch
                elif len(target) == 5:
                    pass  # Specific path of specific branch
                # GitHub 404s without a branch, so do nothing
            elif target[2] == "blob":
                if len(target) == 5:
                    # Could be either a branch and path, or hash and path
                    if COMMIT_HASH_REGEX.match(target[4]):
                        pass  # It's a file under a specific commit hash
                    else:
                        pass  # It's a file under a specific branch
                # GitHub 404s without a hash/branch and path, so do nothing
            elif target[2] == "blame":
                if len(target) == 5:
                    pass  # Blame page
                # GitHub 404s without a branch and path, so do nothing
            elif target[2] == "watchers":
                pass  # Watchers page
            elif target[2] == "stargazers":
                pass  # Stargazers page

        # At this point, if `message` isn't set then we don't understand the
        # url, and so we'll just allow it to pass down to the other handlers

        if message:
            context["event"].target.respond(message)
            returnValue(False)
        else:
            returnValue(True)

    @inlineCallbacks
    def gh_user(self, user):  # User or org
        try:  # Let's see if it's a user
            r = yield self.session.get(URL_USER.format(user))
            data = r.json()

            pprint.pprint(data)
            returnValue("It's a user!")

            # TODO: Return message
        except Exception as e:  # Let's see if it's an organisation, then
            self.plugin.logger.debug(
                "Error getting GitHub user {0}: {1}".format(user), e
            )
            self.plugin.logger.debug(
                "Checking to see if they're an organisation instead."
            )

            r = yield self.session.get(URL_ORG.format(user))
            data = r.json()

            pprint.pprint(data)
            returnValue("It's an org!")

            # TODO: Return message

    @inlineCallbacks
    def gh_repo(self, owner, repo):
        pass

    @inlineCallbacks
    def gh_repo_commits(self, owner, repo):
        pass

    @inlineCallbacks
    def gh_repo_commits_branch(self, owner, repo, branch):
        pass

    @inlineCallbacks
    def gh_repo_commits_branch_path(self, owner, repo, branch, path):
        pass

    @inlineCallbacks
    def gh_repo_commit_hash(self, owner, repo, hash):
        pass

    @inlineCallbacks
    def gh_repo_compare(self, owner, repo, left, right):
        pass

    @inlineCallbacks
    def gh_repo_issues(self, owner, repo):
        pass

    @inlineCallbacks
    def gh_repo_issues_issue(self, owner, repo, issue):
        pass

    @inlineCallbacks
    def gh_repo_pulls(self, owner, repo):
        pass

    @inlineCallbacks
    def gh_repo_pulls_pull(self, owner, repo, pull):
        pass

    @inlineCallbacks
    def gh_repo_labels(self, owner, repo):
        pass

    @inlineCallbacks
    def gh_repo_labels_label(self, owner, repo, label):
        pass

    @inlineCallbacks
    def gh_repo_milestones(self, owner, repo):
        pass

    @inlineCallbacks
    def gh_repo_milestones_milestone(self, owner, repo, milestone):
        pass

    @inlineCallbacks
    def gh_repo_tree_branch(self, owner, repo, branch):
        pass

    @inlineCallbacks
    def gh_repo_tree_branch_path(self, owner, repo, branch, path):
        pass

    @inlineCallbacks
    def gh_repo_blob_branch_path(self, owner, repo, branch, path):
        pass

    @inlineCallbacks
    def gh_repo_blob_hash_path(self, owner, repo, hash, path):
        pass

    @inlineCallbacks
    def gh_repo_blame_branch_path(self, owner, repo, branch, path):
        pass

    @inlineCallbacks
    def gh_repo_watchers(self, owner, repo):
        # Use random.sample() for examples
        pass

    @inlineCallbacks
    def gh_repo_stargazers(self, owner, repo):
        # Use random.sample() for examples
        pass

    def reload(self):
        self.teardown()

        self.session = Session()

    def teardown(self):
        if self.session is not None:
            self.session.close()
