Google
======

This plugin allows you to do quick Google searches that return up to four results at a time.

## Configuration

* `result_limit` - The max number of results to return for a query. Defaults to `4`.
    * Note that Google will never return more than 4 results.

## Commands and permissions

* `google [:page] <query>` - Do a quick search
    * Permission: `google.google`
    * Arguments:
        * `:page` - Optional argument, specify the page you want (for example, `:2`)
        * `query` - The search query, including spaces
