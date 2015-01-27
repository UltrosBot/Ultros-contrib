/******************************************************************************\
 * @author Gareth Coles                                                       *
 *                                                                            *
 * This file is the JavaScript that's injected into the plug.dj room pages.   *
 *                                                                            *
 * We need this to be done so that we can poll for events. Yes, that means    *
 * that events are stored in the browser until they've been pulled out of the *
 * queue, but that's really the only working method we could come up with.    *
 *                                                                            *
 * If someone figures out a better way of doing this, please raise a ticket!  *
\******************************************************************************/

document.ultros = { // It's the only place I could think of storing this
    // Just an array, but we're using it as a FILO queue.
    queue: [],

    // Remove and return the last element of the queue.
    get_items: function() {
        x = document.ultros.queue;
        document.ultros.queue = [];
        return x;
    },

    // region Event listeners

    advance_listener: function(event) {
        // Fired when the DJ booth advances to the next song
        var item = {
            event: "advance",
            dj: event.dj,  // DJ object, current DJ
            media: event.media,  // Media object, current song
            score: event.score,  // {positive, negative, grabs}
            last_play: event.lastPlay,  // Advance event from the last play, sans last_play

            raw_object: event  // Mostly for debugging purposes
        };

        document.ultros.queue.push(item);
    },

    chat_listener: function (event) {
        // Fired on a message sent from a user, or the moderation/chat system itself
        var item = {
            event: "chat",
            type: event.type,  // message, emote, moderation, system, skip
            username: event.un,  // Whoever sent the message
            user_id: event.uid,  // User's ID
            message: event.message,  // Actual chat message
            message_id: event.cid,  // Chat message ID (for, eg, deletion)

            raw_object: event  // Mostly for debugging purposes
        };

        document.ultros.queue.push(item);
    },

    command_listener: function(value) {
        var item = {
            event: "command",
            command: value,

            raw_object: {command: value}  // Mostly for debugging purposes
        };

        document.ultros.queue.push(item);
    },

    grab_listener: function(event) {
        var item = {
            event: "grab",
            user: event.user,

            raw_object: event  // Mostly for debugging purposes
        };

        document.ultros.queue.push(item);
    },

//    history_listener: function(event) {
//        var item = {
//            event: "history",
//            user: event.user,
//            media: event.media,
//            score: event.score,
//
//            raw_object: event  // Mostly for debugging purposes
//        };
//
//        document.ultros.queue.push(item);
//    },

    mod_skip_listener: function(username) {
        var item = {
            event: "mod_skip",
            username: username,

            raw_object: {username: username}  // Mostly for debugging purposes
        };

        document.ultros.queue.push(item);
    },

    score_listener: function(event) {
        var item = {
            event: "score",
            positive: event.positive,
            negative: event.negative,
            grabs: event.grabs,

            raw_object: event  // Mostly for debugging purposes
        };

        document.ultros.queue.push(item);
    },

    user_join_listener: function(user) {
        var item = {
            event: "user_join",
            user: user,

            raw_object: {user: user}  // Mostly for debugging purposes
        };

        document.ultros.queue.push(item);
    },

    user_leave_listener: function(user) {
        var item = {
            event: "user_leave",
            user: user,

            raw_object: {user: user}  // Mostly for debugging purposes
        };

        document.ultros.queue.push(item);
    },

    user_skip_listener: function(username) {
        var item = {
            event: "user_skip",
            username: username,

            raw_object: {username: username}  // Mostly for debugging purposes
        };

        document.ultros.queue.push(item);
    },

    vote_listener: function(event) {
        var item = {
            event: "vote",
            user: event.user,
            vote: event.vote,

            raw_object: event  // Mostly for debugging purposes
        };

        document.ultros.queue.push(item);
    },

    wait_list_listener: function(users) {
        var item = {
            event: "wait_list",
            users: users,

            raw_object: {users: users}  // Mostly for debugging purposes
        };

        document.ultros.queue.push(item);
    }

    // endregion
};

// region Event handler registry

// Now register the event handlers

API.on(API.ADVANCE, document.ultros.advance_listener);
API.on(API.CHAT, document.ultros.chat_listener);
API.on(API.CHAT_COMMAND, document.ultros.command_listener);
API.on(API.GRAB_UPDATE, document.ultros.grab_listener);
// Disabled, unnecessary and really frickin' spammy
// API.on(API.HISTORY_UPDATE, document.ultros.history_listener);
API.on(API.MOD_SKIP, document.ultros.mod_skip_listener);
API.on(API.SCORE_UPDATE, document.ultros.score_listener);
API.on(API.USER_JOIN, document.ultros.user_join_listener);
API.on(API.USER_LEAVE, document.ultros.user_leave_listener);
API.on(API.USER_SKIP, document.ultros.user_skip_listener);
API.on(API.VOTE_UPDATE, document.ultros.vote_listener);
API.on(API.WAIT_LIST_UPDATE, document.ultros.wait_list_listener);

// endregion

// region Stuff to do on page load

if ( $(".icon-emoji-on").length > 0 ) {
    // Turn off emoji if enabled
    $("#chat-emoji-button").click();
    console.log("Emoji disabled.")
}

if ( $(".icon-timestamps-12").length > 0 ) {
    // Turn on 24-hour timestamps if they're set to 12-hour mode
    $("#chat-timestamp-button").click();
    console.log("Timestamps set to 24-hour format.")
}

// Now, disable audio/video if enabled

$(".info").click();

setTimeout(function() {
    $(".item.settings").click();
    setTimeout(function() {
        if ( $(".s-av.selected").length > 0 ) {
            $(".s-av.selected").click();
            console.log("Disabled audio/video.")
        }
        $(".back").click();
    }, 1500);
}, 1500);

// endregion

console.log("Ultros JavaScript injected.");

API.sendChat("Finished loading. The bot is now active!");
