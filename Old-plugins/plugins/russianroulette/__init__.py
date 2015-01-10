# coding=utf-8

__author__ = "Adam Guy"

import random
import system.plugin as plugin

from system.command_manager import CommandManager
from system.protocols.generic.channel import Channel
from system.protocols.generic.protocol import ChannelsProtocol


class RoulettePlugin(plugin.PluginObject):

    commands = None

    channels = {}
    users = {}

    def setup(self):
        self.commands = CommandManager()
        self.commands.register_command("rroulette", self.play, self,
                                       "russianroulette.rroulette",
                                       aliases=["roulette"], default=True)

    def getChannel(self, channel):
        if channel not in self.channels.keys():
            self.channels[channel] = {"players": [], "shots": 0, "deaths": 0,
                                      "chambers": 6, "curplayers": []}
        return self.channels[channel]

    def setChambers(self, channel, chambers):
        self.channels[channel]["chambers"] = chambers

    def play(self, protocol, caller, source, command, raw_args,
             parsed_args):
        self.logger.trace("Caller: %s" % repr(caller))
        self.logger.trace("Source: %s" % repr(source))
        self.logger.trace("Result: %s" % isinstance(source, Channel))

        if not isinstance(source, Channel):
            caller.respond("This command may only be used in a channel.")
            return

        chan = self.getChannel("{}/{}".format(protocol.name, source.name))

        chambers_left = chan["chambers"]

        random.seed()

        if random.randint(1, chambers_left) == 1:
            # Boom!
            if isinstance(protocol, ChannelsProtocol):
                attempt = protocol.channel_kick(caller, source, "BANG")

                if not attempt:
                    source.respond("BANG")
            else:
                attempt = protocol.global_kick(caller, "BANG")

                if not attempt:
                    source.respond("BANG")

            protocol.send_action(source, "*reloads the gun*")
            chambers_left = 6
            source.respond(
                'There are %s new chambers. You have a %s%% chance of dying.'
                % (chambers_left, int(100.0 / chambers_left)))

        else:
            # Click..
            chambers_left -= 1
            source.respond(
                '*click* You\'re safe for now. There are %s chambers left. '
                'You have a %s%% chance of dying.'
                % (chambers_left, int(100.0 / chambers_left)))

        self.setChambers(
            "{}/{}".format(protocol.name, source.name), chambers_left
        )
