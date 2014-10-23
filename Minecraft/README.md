Minecraft
========================

The Minecraft plugin provides a command for querying Minecraft servers
that have their UDP query enabled, as well as a Mojang service status
watcher.

## Configuration

The `minecraft.yml` file contains the following configuration..
* `relay_status` - Whether to enable the service status watcher. This will relay Mojang status updates to the configured targets.
  * Set this to either `yes` or `no`.
  * Checks are done every 600 seconds (ten minutes). The first check is done after 60 seconds, to be sure that all protocols are connected and set up.
* `targets` - A list of targets to relay status updates to
  * `protocol` - Name of the protocol to relay to
  * `target` - Name of the target to relay to
  * `target-type` - Type of the target to relay to. This will usually be `user` or `channel`.
  * `initial-relay` - Whether to relay there on startup with all of Mojang's statuses.

## Usage

This package supplies the following command..
* `mcquery <address[:port]>` - Query a Minecraft server
  * `<address>` The IP or address of the server
  * `[port]` The query port of the server. Defaults to 25565 or the value of the SRV record.
  * Queries a Minecraft server and returns some information about it.
    * This plugin will output a full player list if `can-flood` is enabled for the current protocol.
* The command will be output to the current channel - or in a private message, if used in one.