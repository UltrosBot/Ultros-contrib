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

```
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

```
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

You may notice that the tokens contained within the curly braces - `{` and `}` - also appear in our data from GitHub.
These tokens will be replaced with their respective values in the data - So `{name}` becomes `Gareth Coles`, and `{login}` becomes `gdude2002`.

This is the basis for all formatting strings. If you'd like to understand a bit more about them, check out [this site](https://pyformat.info/),
looking at the new-style `.format()` calls for examples.

Handler formatting
==================

TODO: The rest of this document
