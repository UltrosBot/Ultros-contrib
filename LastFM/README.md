Last.FM
===========

This plugin allows integration with the Last.FM API. Additional features may be added in future.

## Configuration

* `apikey` - Your Last.FM API key, which can be obtained on your [Last.FM API accounts page](http://www.last.fm/api/accounts).
* `recent_play_limit` - How long ago (in seconds) to allow "recent" played tracks to be shown.

## Commands and permissions

* `nowplaying [lastfm username]`
    * Description: Fetch the currently playing song for the given username, or yourself if no username given.
    * Aliases: `np`
    * Permissions: `lastfm.nowplaying`
* `lastfmnick [username]`
    * Description: Store your last.fm username in the bot, or displays your currently stored name if none given.
    * Permissions: `lastfm.lastfmnick`

## Usernames

Any place your username is needed, but has not been set, your current IRC nickname will be used instead. You can set your nickname with `lastfmnick`.

## Attribution

* Sean Gordon
