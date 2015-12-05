from twisted.internet import reactor

from system.events.general import MessageReceived
from system.events.inter import InterPlayerConnected, InterPlayerDisonnected, \
    InterServerConnected, InterServerDisonnected

from system.plugins.plugin import PluginObject
from system.protocols.generic.protocol import Protocol

from system.storage.formats import YAML

from system.translations import Translations

__author__ = 'Gareth Coles'
__all__ = ["InterPlugin"]

_ = Translations().get()
__ = Translations().get_m()


class InterPlugin(PluginObject):
    config = None

    proto = None
    channel = None
    formatting = None

    def setup(self):
        self.logger.trace("Entered setup method.")

        self.protocol_events = {
            "general": [
                # This is basically just *args.
                ["MessageReceived", self, self.message_received, 0]
            ],
            "inter": [
                ["Inter/PlayerConnected", self,
                    self.inter_player_connected, 0],
                ["Inter/PlayerDisconnected", self,
                    self.inter_player_disconnected, 0],
                ["Inter/ServerConnected", self,
                    self.inter_server_connected, 0],
                ["Inter/ServerDisconnected", self,
                    self.inter_server_disconnected, 0]
            ]
        }

        try:
            self.config = self.storage.get_file(self, "config", YAML,
                                                "plugins/inter.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            self.logger.error(_("Disabling.."))
            self._disable_self()
            return

        if not self.config.exists:
            self.logger.error("Unable to find config/plugins/inter.yml")
            self.logger.error(_("Disabling.."))
            self._disable_self()
            return

        self.config.add_callback(self.reload)

        self.commands.register_command(
            "players", self.players_command, self, "inter.players",
            default=True
        )

        if not reactor.running:
            self.events.add_callback(
                "ReactorStarted", self, self.first_load, 0
            )
        else:
            self.first_load()

    def first_load(self, _=None):
        if not self.reload():
            self.logger.error(_("Disabling.."))
            self._disable_self()

    def reload(self):
        self.events.remove_callbacks_for_plugin(self.info.name)
        proto = self.factory_manager.get_protocol(self.config["protocol"])

        if proto is None:
            self.logger.error(_("Unknown protocol: %s")
                              % self.config["protocol"])
            return False

        if proto.TYPE == "inter":
            self.logger.error(_("You cannot relay between two Inter "
                                "protocols!"))
            return False

        self.proto = proto
        self.channel = self.config["channel"]
        self.formatting = self.config["formatting"]

        for event in self.protocol_events["general"]:
            self.events.add_callback(*event)

        for event in self.protocol_events["inter"]:
            self.events.add_callback(*event)

        if proto.TYPE in self.protocol_events:
            for event in self.protocol_events[proto.TYPE]:
                self.events.add_callback(*event)

        return True

    def get_inters(self):
        inters = {}

        for key in self.factory_manager.factories.keys():
            if self.factory_manager.get_protocol(key).TYPE == "inter":
                inters[key] = self.factory_manager.get_protocol(key)

        return inters

    def players_command(self, protocol, caller, source, command, raw_args,
                        args):
        if protocol.TYPE == "inter":
            caller.respond("This command cannot be used via Inter.")
            return

        inters = self.get_inters()

        if len(inters) < 1:
            caller.respond("No Inter protocols were found.")
        elif len(inters) == 1:
            servers = inters[inters.keys()[0]].inter_servers

            for key in servers.keys():
                formatting = self.formatting["player"]["list"]

                done = formatting["message"]
                _done = []

                for x in servers[key]:
                    _done.append(str(x))

                if len(_done):
                    players = formatting["join"].join(_done)
                else:
                    players = "No players online."

                done = done.replace("{SERVER}", key)
                done = done.replace("{PLAYERS}", players)
                source.respond(done)
        else:
            if len(args) < 1:
                caller.respond("Usage: {CHARS}%s <inter server>")
                caller.respond("Servers: %s" % ", ".join(inters.keys()))
                return

            srv = args[1]
            if srv not in inters:
                caller.respond("Unknown inter server: %s" % srv)
                caller.respond("Servers: %s" % ", ".join(inters.keys()))
                return

            servers = inters[srv].inter_servers

            for key in servers.keys():
                formatting = self.formatting["player"]["list"]

                done = formatting["message"]
                _done = []

                for x in servers[key]:
                    _done.append(str(x))

                if len(_done):
                    players = formatting["join"].join(_done)
                else:
                    players = "No players online."

                done = done.replace("{SERVER}", key)
                done = done.replace("{PLAYERS}", players)
                source.respond(done)

    def message_received(self, event=MessageReceived):
        caller = event.caller
        user = event.source
        message = event.message
        target = event.target

        if target is None:
            return
        if caller is None:
            return

        if isinstance(caller, Protocol):
            if caller.TYPE == "inter":
                f_str = self.formatting["player"]["message"]

                f_str = f_str.replace("{SERVER}", user.server)
                f_str = f_str.replace("{USER}", str(user))
                f_str = f_str.replace("{MESSAGE}", message)

                self.proto.send_msg(self.channel, f_str)
            else:
                if caller.name == self.proto.name:
                    if target.name.lower() == self.channel.lower():
                        inters = self.get_inters()

                        for proto in inters.values():
                            proto.send_msg_other(user, message)

    def inter_server_connected(self, event=InterServerConnected):
        f_str = self.formatting["server"]["connected"]
        f_str = f_str.replace("{SERVER}", event.name)

        self.proto.send_msg(self.channel, f_str)

    def inter_server_disconnected(self, event=InterServerDisonnected):
        f_str = self.formatting["server"]["disconnected"]
        f_str = f_str.replace("{SERVER}", event.name)

        self.proto.send_msg(self.channel, f_str)

    def inter_player_connected(self, event=InterPlayerConnected):
        f_str = self.formatting["player"]["connected"]
        f_str = f_str.replace("{SERVER}", event.user.server)
        f_str = f_str.replace("{USER}", str(event.user))

        self.proto.send_msg(self.channel, f_str)

    def inter_player_disconnected(self, event=InterPlayerDisonnected):
        f_str = self.formatting["player"]["disconnected"]
        f_str = f_str.replace("{SERVER}", event.user.server)
        f_str = f_str.replace("{USER}", str(event.user))

        self.proto.send_msg(self.channel, f_str)
