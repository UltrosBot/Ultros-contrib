# coding=utf-8

__author__ = "Adam Guy"

import random

from system.protocols.generic.channel import Channel
from system.command_manager import CommandManager

import system.plugin as plugin


class RoulettePlugin(plugin.PluginObject):

    commands = None

    channels = {}
    users = {}

    def setup(self):
        self.commands = CommandManager()
        self.commands.register_command("rroulette", self.play, self,
                                       "russianroulette.rroulette",
                                       aliases=["roulette"], default=True)

    def addChannel(self, channel):
        if channel not in self.channels.keys():
            players = []
            curplayers = []
            shots = 0
            deaths = 0
            chambers = 6

            data = {"players": players, "shots": shots, "deaths": deaths,
                    "chambers": chambers, "curplayers": curplayers}

            self.channels[channel] = data

    def play(self, protocol, caller, source, command, raw_args,
             parsed_args):
        args = raw_args.split()  # Quick fix for new command handler signature
        self.logger.trace("Caller: %s" % repr(caller))
        self.logger.trace("Source: %s" % repr(source))
        self.logger.trace("Result: %s" % isinstance(source, Channel))
        if not isinstance(source, Channel):
            caller.respond("This command may only be used in a channel.")
            return

        self.addChannel(source.name)

        chambers_left = self.channels[source.name]["chambers"]

        random.seed()

        if random.randint(1, chambers_left) == 1:
            # Boom!
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
        self.channels[source.name]["chambers"] = chambers_left
