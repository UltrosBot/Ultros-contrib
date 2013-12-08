Teamspeak
=========

### Important note

As the Teamspeak protocol is proprietary and undocumented, it was
impossible to create a protocol that would masquerade as a user on
Teamspeak, which is what bots usually do. This means that we are forced
to use ServerQuery, a telnet text protocol designed for administration
tools.

As a result, the bot *will not be visible* to normal users, or even to
admin users that don't enable ServerQuery client visibility. However,
the bot will still function as expected - users simply won't see it in the
user-list.

Another problem resulting from the use of ServerQuery is that this protocol
is quite hacky and somewhat slow. While we believe that this is a somewhat
decent solution for people requiring bots on Teamspeak servers, we're not
exactly proud of the code for this protocol.

We may consider releasing another protocol that makes use of the Teamspeak
client API in the future.