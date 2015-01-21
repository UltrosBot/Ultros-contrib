# coding=utf-8
__author__ = "Gareth Coles"

import json

from twisted.internet import reactor
from twisted.protocols.basic import LineOnlyReceiver

from system.command_manager import CommandManager
from system.enums import CommandState

from system.event_manager import EventManager

from system.events import general as general_events
from system.events import inter as inter_events

from system.protocols.generic.protocol import NoChannelsProtocol
from system.protocols.inter.user import User
from system.protocols.inter.channel import Channel
from system.translations import Translations

from system.logging.logger import getLogger
from utils.switch import Switch
_ = Translations().get()


class Protocol(LineOnlyReceiver, NoChannelsProtocol):
    __version__ = "0.0.1"
    __inter_version__ = 3

    TYPE = "inter"
    CHANNELS = False

    factory = None
    config = None
    log = None
    event_manager = None
    command_manager = None

    nickname = ""
    ourselves = None
    channel = None
    can_flood = False

    control_chars = "."

    handshake_done = False

    inter_servers = {}

    _users = []

    def __init__(self, name, factory, config):
        NoChannelsProtocol.__init__(self, name, factory, config)

        self.log = getLogger(self.name)
        self.event_manager = EventManager()
        self.command_manager = CommandManager()

        reactor.connectTCP(
            self.config["connection"]["host"],
            self.config["connection"]["port"],
            self.factory,
            120
        )

    def connectionMade(self):
        self.handshake_done = False
        self.inter_servers = {}
        self.nickname = ""

        self.control_chars = self.config["control_char"]

        self.ourselves = User(self.config["nickname"], self, True)
        self.channel = Channel(protocol=self)

    def lineReceived(self, line):
        try:
            self.log.trace("<- %s" % repr(line))
            message = json.loads(line)
        except Exception:
            self.log.exception("Failed to parse line")
        else:
            if "version" in message:
                v = message["version"]

                if v != self.__inter_version__:
                    self.log.error("Protocol version mismatch!")
                    self.log.error("Ours: %s | Theirs: %s"
                                   % (self.__inter_version__, v))

                    self.factory.manager.remove_protocol(self.name)
                    return

                self.log.info("Connected to Inter, version %s" % v)

                message = {
                    "api_key": self.config["connection"]["api_key"]
                }

                self.send(message)

            if "from" in message:
                origin = message["from"]

                for case, default in Switch(origin):
                    if case("chat"):
                        source = message["source"]
                        msg = message["message"]

                        user = self.get_user(
                            message["user"], server=source, create=True
                        )
                        if not user.server:
                            user.server = source

                        if user == self.ourselves:
                            break  # Since, well, this is us.

                        if source == self.nickname:
                            break  # Since this is also us.

                        event = general_events.PreMessageReceived(
                            self, user, user, msg, "message"  # No channels
                        )
                        self.event_manager.run_callback("PreMessageReceived",
                                                        event)
                        if event.printable:
                            for line in event.message.split("\n"):
                                self.log.info("<%s> %s" % (user, line))

                        if not event.cancelled:
                            result = self.command_manager.process_input(
                                event.message, user, user, self,
                                self.control_chars, self.nickname
                            )

                            for c, d in Switch(result[0]):
                                if c(CommandState.RateLimited):
                                    self.log.debug("Command rate-limited")
                                    user.respond("That command has been "
                                                 "rate-limited, please try "
                                                 "again later.")
                                    return  # It was a command
                                if c(CommandState.NotACommand):
                                    self.log.debug("Not a command")
                                    break
                                if c(CommandState.UnknownOverridden):
                                    self.log.debug("Unknown command "
                                                   "overridden")
                                    return  # It was a command
                                if c(CommandState.Unknown):
                                    self.log.debug("Unknown command")
                                    break
                                if c(CommandState.Success):
                                    self.log.debug("Command ran successfully")
                                    return  # It was a command
                                if c(CommandState.NoPermission):
                                    self.log.debug("No permission to run "
                                                   "command")
                                    return  # It was a command
                                if c(CommandState.Error):
                                    user.respond("Error running command: "
                                                 "%s" % result[1])
                                    return  # It was a command
                                if d:
                                    self.log.debug("Unknown command state: "
                                                   "%s" % result[0])
                                    break
                            second_event = general_events.MessageReceived(
                                self, user, user, msg, "message"
                            )

                            self.event_manager.run_callback(
                                "MessageReceived", second_event
                            )
                        break
                    if case("players"):
                        _type = message["type"]
                        target = message["target"]

                        if _type == "list":
                            if target == "all":
                                # All servers, we can just overwrite the list.
                                self.inter_servers = {}
                                players = message["players"]

                                for key in players:
                                    self.inter_servers[key] = []

                                    for user in players[key]:
                                        obj = User(user, self, True)
                                        obj.server = key

                                        self.inter_servers[key].append(obj)

                                        if obj not in self._users:
                                            self._users.append(obj)

                                self.log.info("Got player list.")

                                for key in self.inter_servers.keys():
                                    self.log.info(
                                        "%s: %s players" % (
                                            key,
                                            len(self.inter_servers[key])
                                        )
                                    )

                                event = inter_events.InterServerListReceived(
                                    self, self.inter_servers
                                )

                                self.event_manager.run_callback(
                                    "Inter/ServerListReceived", event
                                )
                            else:
                                # Unexpected!
                                self.log.warn("Unknown list target: %s"
                                              % target)
                        elif _type == "offline":
                            player = self.get_user(
                                message["player"], target, True
                            )

                            player.server = target

                            if target not in self.inter_servers:
                                self.inter_servers[target] = []

                            if player in self.inter_servers[target]:
                                self.inter_servers[target].remove(player)

                            if player in self._users:
                                self._users.remove(player)

                            self.log.info("%s disconnected from %s."
                                          % (player, target))

                            event = general_events.UserDisconnected(
                                self, player
                            )

                            self.event_manager.run_callback(
                                "UserDisconnected", event
                            )

                            second_event = inter_events.InterPlayerDisonnected(
                                self, player
                            )

                            self.event_manager.run_callback(
                                "Inter/PlayerDisconnected", second_event
                            )

                        elif _type == "online":
                            player = self.get_user(
                                message["player"], target, True
                            )

                            player.server = target

                            if target not in self.inter_servers:
                                self.inter_servers[target] = []

                            if player not in self.inter_servers[target]:
                                self.inter_servers[target].append(player)

                            if player not in self._users:
                                self._users.append(player)

                            self.log.info("%s connected to %s."
                                          % (player, target))

                            event = inter_events.InterPlayerConnected(
                                self, player
                            )

                            self.event_manager.run_callback(
                                "Inter/PlayerConnected", event
                            )
                        break
                    if case("auth"):
                        action = message["action"]

                        if action == "authenticated":
                            if not self.handshake_done and "status" in message:
                                status = message["status"]

                                if status == "success":
                                    self.nickname = message["name"]
                                    self.log.info("Authenticated as %s"
                                                  % self.nickname)
                                    self.handshake_done = True

                                    # Get players
                                    self.send_get_players()

                                    self.send_connect(self.ourselves.nickname)

                                    event = inter_events.InterAuthenticated(
                                        self
                                    )

                                    self.event_manager.run_callback(
                                        "Inter/Authenticated", event
                                    )
                                else:
                                    error = message["error"]
                                    self.log.error("Error authenticating: %s"
                                                   % error)

                                    event = (
                                        inter_events.InterAuthenticationError(
                                            self, error
                                        )
                                    )

                                    self.event_manager.run_callback(
                                        "Inter/AuthenticationError", event
                                    )

                                    self.transport.close()
                                    self.factory.manager.remove_protocol(
                                        self.name
                                    )
                            else:
                                name = message["name"]
                                self.log.info("Server connected to Inter: %s"
                                              % name)

                                event = inter_events.InterServerConnected(
                                    self, name
                                )

                                self.event_manager.run_callback(
                                    "Inter/ServerConnected", event
                                )
                        else:
                            name = message["name"]
                            self.log.info("Server disconnected from Inter: %s"
                                          % name)

                            event = inter_events.InterServerDisonnected(
                                self, name
                            )

                            self.event_manager.run_callback(
                                "Inter/ServerDisconnected", event
                            )

                            if name in self.inter_servers:
                                del self.inter_servers[name]
                        break
                    if case("core"):
                        event = inter_events.InterCoreMessage(
                            self, message
                        )

                        self.event_manager.run_callback(
                            "Inter/CoreMessage", event
                        )
                        break
                    if case("ping"):
                        timestamp = message["timestamp"]

                        event = inter_events.InterPing(
                            self, timestamp
                        )

                        self.event_manager.run_callback(
                            "Inter/Ping", event
                        )

                        self.send_pong(timestamp)
                        break
                    if default:
                        self.log.warn("Unknown message origin: %s" % origin)

                        event = inter_events.InterUnknownMessage(
                            self, message
                        )

                        self.event_manager.run_callback(
                            "Inter/UnknownMessage", event
                        )

                        break

    def send(self, _json):
        self.sendLine(
            json.dumps(_json)
        )

    def sendLine(self, line):
        self.log.trace("-> %s" % repr(line))
        LineOnlyReceiver.sendLine(self, line)

    def shutdown(self):
        """
        Called when a protocol needs to disconnect. Cleanup should be done
        here.
        """
        self.transport.loseConnection()

    def get_user(self, username, server=None, create=False):
        """
        Used to retrieve a user. Return None if we can't find it.
        :param user: string representing the user we need.
        """
        if server is None:
            for key in self.inter_servers:
                for user in self.inter_servers[key]:
                    if user.name.lower() == username.lower():
                        return user
        else:
            if server in self.inter_servers:
                for user in self.inter_servers[server]:
                    if user.name.lower() == username.lower():
                        return user

        if create:
            return User(username, self)

        return None

    def send_msg(self, target, message, target_type=None, use_event=True):
        """
        Send a message.
        :param target: Ignored.
        :param message: The message to send.
        :param target_type: Ignored.
        :param use_event: Whether to fire the MessageSent event or not.
        :return: Boolean describing whether the target was found and messaged.
        """
        # Target and target type are ignored here.
        self.send(
            {
                "action": "chat",
                "message": message,
                "user": str(self.ourselves)
            }
        )

        return True

    def send_msg_other(self, user, message):
        self.send(
            {
                "action": "chat",
                "message": message,
                "user": str(user)
            }
        )

        return True

    def send_action(self, target, message, target_type=None, use_event=True):
        # Target and target type are ignored here.
        return self.send_msg(target, "*%s*" % message, target_type, use_event)

    def send_action_other(self, user, message):
        self.send(
            {
                "action": "chat",
                "message": "*%s*" % message,
                "user": str(user)
            }
        )

    def send_connect(self, username):
        message = {
            "action": "players",
            "type": "online",
            "player": username
        }

        self.send(message)

    def send_disconnect(self, username):
        message = {
            "action": "players",
            "type": "offline",
            "player": username
        }

        self.send(message)

    def send_get_players(self):
        message = {
            "action": "players",
            "type": "list"
        }

        self.send(message)

    def send_pong(self, timestamp):
        message = {
            "pong": timestamp,
        }

        self.send(message)
