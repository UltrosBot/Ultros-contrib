Handler Formatting
==================

**Please note**: This is an advanced topic. Prior experience with Python or another
programming language will help considerably, but a little elbow grease should still
get most people through.

Know what you're doing? [Skip to the formatting strings](#handler-formatting-1).

---

Some of the provided handlers are highly configurable, allowing you to change
almost every aspect of their output. This is done through the use of formatting
strings, which are formatted internally using python's own `str.format()` function.

In the interests of creating a powerful system, we've raised the difficulty bar
slightly. Formatting strings are quite reliant on the data each site provides
via their respective APIs, and this means that some knowledge of each is
required. That said, if you have a little time and patience to spare, it won't
take you long to understand.

Python's strings are formatted using tokens contained with `{` and `}` - the
curly braces. Inside these is an identifier - the name of what you're trying
to refer to - and the data available is usually passed in as a dictionary.

An example
----------

As an example, let's look at the default message given for a GitHub user.

The formatting string might be declared as follows: 

```yaml
github:
 formatting:
  user: !!python/unicode "[GitHub user] {name} ({login}) - {public_repos} repos / {public_gists} gists - {followers} followers / {following} following - {blog}"
```

The `!!python/unicode` prefix is optional, but we highly recommend that you use it to minimize possible
encoding errors. The need for this will go away once we eventually move to Python 3.

Now, let's look at the data GitHub makes available to us for the user named `gdude2002`:

```json
{
 "login": "gdude2002",
 "id": 204153,
 "avatar_url": "https://avatars.githubusercontent.com/u/204153?v=3",
 "gravatar_id": "",
 "url": "https://api.github.com/users/gdude2002",
 "html_url": "https://github.com/gdude2002",
 "followers_url": "https://api.github.com/users/gdude2002/followers",
 "following_url": "https://api.github.com/users/gdude2002/following{/other_user}",
 "gists_url": "https://api.github.com/users/gdude2002/gists{/gist_id}",
 "starred_url": "https://api.github.com/users/gdude2002/starred{/owner}{/repo}",
 "subscriptions_url": "https://api.github.com/users/gdude2002/subscriptions",
 "organizations_url": "https://api.github.com/users/gdude2002/orgs",
 "repos_url": "https://api.github.com/users/gdude2002/repos",
 "events_url": "https://api.github.com/users/gdude2002/events{/privacy}",
 "received_events_url": "https://api.github.com/users/gdude2002/received_events",
 "type": "User",
 "site_admin": false,
 "name": "Gareth Coles",
 "company": null,
 "blog": "http://archivesmc.com",
 "location": "Ireland",
 "email": null,
 "hireable": null,
 "bio": null,
 "public_repos": 26,
 "public_gists": 17,
 "followers": 16,
 "following": 14,
 "created_at": "2010-02-15T19:46:20Z",
 "updated_at": "2015-10-04T20:24:45Z"
}
```

Oh my, that's quite a lot of info, isn't it? Let's strip it down to the things that we can actually use:

```json
{
 "login": "gdude2002",
 "type": "User",
 "name": "Gareth Coles",
 "blog": "http://archivesmc.com",
 "location": "Ireland",
 "public_repos": 26,
 "public_gists": 17,
 "followers": 16,
 "following": 14
}
```

There, that's much easier to read. Now, if we look at our formatting string again..

```
"[GitHub user] {name} ({login}) - {public_repos} repos / {public_gists} gists - {followers} followers / {following} following - {blog}"
```

You may notice that the tokens contained within the curly braces - `{` and `}` - 
also appear in our data from GitHub. These tokens will be replaced with their 
respective values in the data - So `{name}` becomes `Gareth Coles`, and `{login}` 
becomes `gdude2002`.

This is the basis for all formatting strings. If you'd like to understand a 
bit more about them, check out [this site](https://pyformat.info/), looking at 
the new-style `.format()` calls for examples.

Handler formatting
==================

Currently, the handlers that this plugin supports for customization are:

* [GitHub](#github)
* [osu!](#)

More of these will be added over time.

To change a formatting string, open your `urltools.yml`, find the section for
the handler you want to customize, and add the corresponding key and value to
the `formatting` section.

Most handler sections below will contain a sample URL to be matched, as well as
links to the API documentation that point to up-to-date data samples.

GitHub
------

Each formatting string below has a key named `given` available to it, which refers
to a dictionary that itself contains some keys. You can access this using `[` 
square brackets `]`, like so: `{given[key]}`

### Key: user

* **Example URL**: `https://github.com/gdude2002`
* **API documentation**: https://developer.github.com/v3/users/#get-a-single-user
* `given`: `user`

**Default string**:

```
!!python/unicode "[GitHub user] {name} ({login}) - {public_repos} repos / {public_gists} gists - {followers} followers / {following} following - {blog}"
```

### Key: org

* **Example URL**: https://github.com/UltrosBot
* **API documentation**: https://developer.github.com/v3/orgs/#get-an-organization
* `given`: `user`

**Default string**:

```
!!python/unicode "[GitHub org] {name}: {description} - {public_repos} repos / {public_gists} gists - {followers} followers - {blog}"
```

### Key: repo

* **Example URL**: https://github.com/UltrosBot/Ultros
* **API documentation**: https://developer.github.com/v3/repos/#get
* `given`: `owner`, `repo`

**Default string**:

```
!!python/unicode "[GitHub repo] {full_name}: {description} - {forks_count} forks / {watchers_count} watchers, {subscribers_count} stars"
```

### Key: repo-fork

* **Example URL**: https://github.com/voxadam/Ultros (Fork of UltrosBot/Ultros)
* **API documentation**: https://developer.github.com/v3/repos/#get
* `given`: `owner`, `repo`

**Default string**:

```
!!python/unicode "[GitHub fork] {full_name} (Fork of {parent[full_name]}): {description} - {forks_count} forks / {watchers_count} watchers, {subscribers_count} stars"
```

### Key: repo-blob-branch-path

* **Example URL**: https://github.com/voxadam/Ultros/blob/master/LICENSE
* **API documentation**: https://developer.github.com/v3/repos/commits/#get-a-single-commit
* `given`: `owner`, `repo`, `branch`, `path`

**Default string**:

```
!!python/unicode "[GitHub file] {given[owner]}/{given[repo]}/{given[branch]} - {given[path]} - {commit[author][name]}: {commit[message]} (+{stats[additions]}/-{stats[deletions]}/±{stats[total]})"
```

### Key: repo-blob-hash-path

* **Example URL**: https://github.com/UltrosBot/Ultros/blob/740db9cd4f15e208530833b45bf9d91ada9d56a6/system/logging/logger.py
* **API documentation**: https://developer.github.com/v3/repos/commits/#get-a-single-commit
* `given`: `owner`, `repo`, `hash`, `path`

**Default string**:

```
!!python/unicode "[GitHub file] {given[owner]}/{given[repo]} - {given[path]} - {commit[author][name]}: {commit[message]} (+{stats[additions]}/-{stats[deletions]}/±{stats[total]})"
```

### Key: repo-no-commits

* **Example URL**: https://github.com/UltrosBot/test/commits
* **API documentation**: N/A
* **Notes**: The only data available here is in `given`
* `given`: `owner`, `repo`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]} - No commits found"
```

### Key: repo-commits

* **Example URL**: https://github.com/UltrosBot/Ultros/commits
* **API documentation**: N/A
* **Notes**: The following data is available:
    * `commits`: A large list of commits
    * `commits_count`: The total number of commits
    * `contributors`: A potentially large list of contributors
    * `contributors_count`: The total number of contributors
* `given`: `owner`, `repo`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]} - {commits_count} commits by {contributors_count} contributors"
```

### Key: repo-commits-branch

* **Example URL**: https://github.com/UltrosBot/Ultros/commits/master
* **API documentation**: N/A
* **Notes**: The following data is available:
    * `commits`: A large list of commits
    * `commits_count`: The total number of commits
    * `contributors`: A potentially large list of contributors
    * `contributors_count`: The total number of contributors
* `given`: `owner`, `repo`, `branch`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]} - {commits_count} commits by {contributors_count} contributors"
```

### Key: repo-commits-branch-path

* **Example URL**: https://github.com/UltrosBot/Ultros/commits/master/system/logging/logger.py
* **API documentation**: N/A
* **Notes**: The following data is available:
    * `commits`: A large list of commits
    * `commits_count`: The total number of commits
    * `contributors`: A potentially large list of contributors
    * `contributors_count`: The total number of contributors
* `given`: `owner`, `repo`, `branch`, `path`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]} - {commits_count} commits by {contributors_count} contributors"
```

### Key: repo-commit-hash

* **Example URL**: https://github.com/UltrosBot/Ultros/commit/126790345e68072def2b91ba5b0d5033d005e0da
* **API documentation**: 
* `given`: `owner`, `repo`, `hash`

**Default string**:

```
!!python/unicode "[GitHub commit] {given[owner]}/{given[repo]} - {commit[author][name]}: {commit[message]} (+{stats[additions]}/-{stats[deletions]}/±{stats[total]})"
```

### Key: repo-compare

* **Example URL**: https://github.com/UltrosBot/Ultros-contrib/compare/54d62947f8ad...9dd4a625659e
* **API documentation**: 
* `given`: `owner`, `repo`, `left`, `right`

**Default string**:

```
!!python/unicode "[GitHub commit comparison] Status: {status} - Ahead by {ahead_by} commit(s) / behind by {behind_by} commit(s) - {total_commits} commit(s) in total"
```

### Key: repo-issue

* **Example URL**: https://github.com/UltrosBot/Ultros/issues/82
* **API documentation**: 
* `given`: `owner`, `repo`, `issue`

**Default string**:

```
!!python/unicode "[GitHub issue] {given[owner]}/{given[repo]} #{number} - {user[login]}: {title} ({state}) - {label_list} - Milestone: {milestone[title]} / Assigned: {assigned_name}"
```

### Key: repo-issues

* **Example URL**: https://github.com/UltrosBot/Ultros/issues
* **API documentation**: 
* `given`: `owner`, `repo`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]} - {total_count} total issues ({open_count} open / {closed_count} closed)"
```

### Key: repo-no-issues

* **Example URL**: https://github.com/<some owner>/<some repo with no issues>/issues
* **API documentation**: 
* **Notes**: The only data available here is in `given`
* `given`: `owner`, `repo`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]} - No issues found"
```

### Key: repo-label

* **Example URL**: https://github.com/UltrosBot/Ultros/labels/Bug
* **API documentation**: 
* **Notes**: The following data is available:
    * `closed_count`: Number of closed issues under this label
    * `open_count`: Number of open issues under this label
    * `total_count`: Total number of issues under this label
* `given`: `owner`, `repo`, `label`

**Default string**:

```
!!python/unicode "[GitHub label] {given[owner]}/{given[repo]} - {given[label] - {total_count} issues: {open_count} open / {closed_count} closed"
```

### Key: repo-label-no-issues

* **Example URL**: https://github.com/UltrosBot/Ultros/labels/Invalid
* **API documentation**: 
* **Notes**: The only data available here is in `given`
* `given`: `owner`, `repo`, `label`

**Default string**:

```
!!python/unicode "[GitHub label] {given[owner]}/{given[repo]} - {given[label] - No issues found"
```

### Key: repo-labels

* **Example URL**: https://github.com/UltrosBot/Ultros/labels
* **API documentation**: 
* **Notes**: The following data is available:
    * `labels`: Large list of all labels; unformatted
    * `labels_sample`: Number of open issues under this label
    * `labels_count`: Total number of issues under this label
* `given`: `owner`, `repo`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]} - {labels_count} labels, including {labels_sample}"
```

### Key: repo-no-labels

* **Example URL**: https://github.com/UltrosBot/test/labels
* **API documentation**: 
* **Notes**: The only data available here is in `given`
* `given`: `owner`, `repo`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]} - No labels found"
```

### Key: repo-milestone

**Important**: The GitHub API does not provide a way to access milestone information using the URL slug.
As a result, the API expects the ID of a milestone instead - starting at `1` for the earliest.

We're aware that this makes this call not all that useful, but we'd rather have *some* functionality here
than none.

* **Example URL**: https://github.com/UltrosBot/Ultros/milestones/2 (Note the ID here instead of the milestone name)
* **API documentation**: 
* **Notes**: The following extra data is available:
    * `issues_count`: Total number of issues under this milestone
    * `percent`: Estimated completion percentage of this milestone
* `given`: `owner`, `repo`, `milestone`

**Default string**:

```
!!python/unicode "[GitHub milestone] {given[owner]}/{given[repo]} - {issues_count} issues - {open_issues} open / {closed_issues} closed ({percent}% complete)"
```

### Key: repo-milestone-no-issues

**Important**: The GitHub API does not provide a way to access milestone information using the URL slug.
As a result, the API expects the ID of a milestone instead - starting at `1` for the earliest.

We're aware that this makes this call not all that useful, but we'd rather have *some* functionality here
than none.

* **Example URL**: https://github.com/UltrosBot/test/milestones/1 (Note the ID here instead of the milestone name)
* **API documentation**: 
* **Notes**: The following data is available:
    * `percent`: This is just `0` right now
* `given`: `owner`, `repo`, `milestone`

**Default string**:

```
!!python/unicode "[GitHub milestone] {given[owner]}/{given[repo]} - {title} - {description} - No issues found"
```

### Key: repo-milestones

**Important**: This call is distinct from the other listing calls in that it provides the
latest milestone, rather than the list of milestones - although, that's arguably more useful
than a list.

* **Example URL**: https://github.com/UltrosBot/Ultros/milestones
* **API documentation**: 
* **Notes**: The following extra data is available:
    * `issues_count`: Total number of issues under this milestone
    * `percent`: Estimated completion percentage of this milestone
    * `total_milestones`: Total number of milestones in this repo
* `given`: `owner`, `repo`

**Default string**:

```
!!python/unicode "[GitHub repo {given[owner]}/{given[repo]}] - {total_milestones} milestones - Latest: {title} - {description} | {open_issues} open issues / {closed_issues} closed issues - {percent}%"
```

### Key: repo-no-milestones

* **Example URL**: https://github.com/UltrosBot/Ultros-tools/milestones
* **API documentation**: 
* **Notes**: The only data available here is in `given`
* `given`: `owner`, `repo`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]} - No milestones found"
```

### Key: repo-pull

**Important**: GitHub understandably doesn't return specific data, when it's missing, so we substitute
it in that case. For this call, `assigned_name` should be used instead of `assignee`, and only the `title`
key of the `milestone` are safe to use, but we decided to include everything in case they were useful to someone.

* **Example URL**: https://github.com/UltrosBot/Ultros/pull/75
* **API documentation**: 
* **Notes**: The following extra data is available:
    * `assigned_name`: The username of the assignee, or None if there isn't one
* `given`: `owner`, `repo`, `pull`

**Default string**:

```
!!python/unicode "[GitHub pull request] {given[owner]}/{given[repo]} #{number} - {user[login]}: {title} ({state}) - Milestone: {milestone[title]} / Assigned: {assigned_name}"
```

### Key: repo-pulls

* **Example URL**: https://github.com/UltrosBot/Ultros/pulls
* **API documentation**: 
* **Notes**: The following data is available:
    * `closed_count`: Total number of closed PRs under this repo
    * `open_count`: Total number of open PRs under this repo
    * `total_count`: Total number of PRs under this repo
* `given`: `owner`, `repo`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]} - {total_count} total pull requests ({open_count} open / {closed_count} closed)"
```

### Key: repo-no-pulls

* **Example URL**: https://github.com/UltrosBot/test/pulls
* **API documentation**: 
* **Notes**: The only data available here is in `given`
* `given`: `owner`, `repo`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]} - No pull requests found"
```

### Key: repo-releases

* **Example URL**: https://github.com/UltrosBot/Ultros/releases
* **API documentation**: 
* **Notes**: The following data is available:
    * `total_releases`: Total number of releases under this repo
* `given`: `owner`, `repo`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]} - {total_releases} releases"
```

### Key: repo-no-releases

* **Example URL**: https://github.com/UltrosBot/test/releases
* **API documentation**: 
* **Notes**: The only data available here is in `given`
* `given`: `owner`, `repo`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]} - No releases found"
```

### Key: repo-releases-latest

* **Example URL**: https://github.com/UltrosBot/Ultros/releases/latest
* **API documentation**: 
* `given`: `owner`, `repo`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]} - Latest release: {tag_name} - {name}"
```

### Key: repo-releases-tag

* **Example URL**: https://github.com/UltrosBot/Ultros/releases/tag/v1.1.0
* **API documentation**: 
* `given`: `owner`, `repo`, `tag`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]} - Specific release: {tag_name} - {name}"
```

### Key: repo-stargazers

* **Example URL**: https://github.com/UltrosBot/Ultros/stargazers
* **API documentation**: 
* **Notes**: The following data is available:
    * `total_stargazers`: The total number of stargazers for this repo
    * `stargazers_sample`: A random selection of up to 5 stargazers
* `given`: `owner`, `repo`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]} - {total_stargazers} stargazers, including {stargazers_sample}"
```

### Key: repo-no-stargazers

* **Example URL**: https://github.com/<some owner>/<some repo with no stars>/issues
* **API documentation**: 
* **Notes**: The only data available here is in `given`
* `given`: `owner`, `repo`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]} - No stargazers found"
```

### Key: repo-tags

* **Example URL**: https://github.com/UltrosBot/Ultros/tags
* **API documentation**: 
* **Notes**: The following data is available:
    * `total_tags`: The total number of tags for this repo
    * `tags_sample`: A random selection of up to 5 tags
* `given`: `owner`, `repo`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]} - {total_tags} tags, including {tags_sample}"
```

### Key: repo-no-tags

* **Example URL**: https://github.com/UltrosBot/test/tags
* **API documentation**: 
* **Notes**: The only data available here is in `given`
* `given`: `owner`, `repo`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]} - No tags found"
```

### Key: repo-tree-branch

* **Example URL**: https://github.com/UltrosBot/Ultros/tree/master
* **API documentation**: 
* `given`: `owner`, `repo`, `branch`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]}/{given[branch]} - {commit[author][name]}: {commit[message]} (+{stats[additions]}/-{stats[deletions]}/±{stats[total]})"
```

### Key: repo-tree-branch-path

* **Example URL**: https://github.com/UltrosBot/Ultros/tree/master/README.md
* **API documentation**: 
* `given`: `owner`, `repo`, `branch`, `path`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]}/{given[branch]} - {given[path]} - {commit[author][name]}: {commit[message]} (+{stats[additions]}/-{stats[deletions]}/±{stats[total]})"
```

### Key: repo-tree-branch-path-dir

* **Example URL**: https://github.com/UltrosBot/Ultros/tree/master/system
* **API documentation**: 
* **Notes**: The following data is available:
    * `total_files`: The total number of files in this directory
* `given`: `owner`, `repo`, `branch`, `path`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]}/{given[branch]} - {given[path]} - {total_files} files"
```

### Key: repo-watchers

* **Example URL**: https://github.com/UltrosBot/Ultros/watchers
* **API documentation**: 
* **Notes**: The following data is available:
    * `total_watchers`: The total number of watchers for this repo
    * `watchers_sample`: A random selection of up to 5 watchers
* `given`: `owner`, `repo`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]} - {total_watchers} watchers, including {watchers_sample}"
```

### Key: repo-no-watchers

* **Example URL**: https://github.com/<some owner>/<some repo with no watchers>/issues
* **API documentation**: 
* **Notes**: The only data available here is in `given`
* `given`: `owner`, `repo`

**Default string**:

```
!!python/unicode "[GitHub repo] {given[owner]}/{given[repo]} - No watchers found"
```
