# coding=utf-8
import json
import zlib

from weakref import ref

import time
from autobahn.twisted import WebSocketClientProtocol
from kitchen.text.converters import to_bytes

from system.logging.logger import getLogger
from system.protocols.discord.voice_websocket import opcodes

__author__ = 'Gareth Coles'


class DiscordVoiceWebsocketProtocol(WebSocketClientProtocol):
    @property
    def protocol(self):
        return self._protocol()

    def __init__(self, protocol, user_id, session_id, token, guild_id,
                 endpoint):
        super(DiscordVoiceWebsocketProtocol, self).__init__()

        self._protocol = ref(protocol)
        self.user_id = user_id
        self.session_id = session_id
        self.token = token
        self.guild_id = guild_id
        self.endpoint = endpoint

        self.log = getLogger("{}: Voice WS".format(self.protocol.name))

    # region: Websocket methods

    def onConnect(self, response):
        self.log.info("Connected: {}".format(response.peer))

    def onOpen(self):
        # Send initial connection message
        self.log.trace("Sending initial connection message...")
        self.send_identify(self.token)

    def onMessage(self, payload, is_binary):
        if is_binary:
            payload = zlib.decompress(payload)

            self.log.trace(
                "Payload (Binary): {}".format(repr(payload))
            )
        else:
            self.log.trace(
                "Payload (Text): {}".format(repr(payload))
            )

        try:
            message = json.loads(payload)
        except Exception:
            self.log.exception("Unable to parse message: {}".format(payload))
            return

        try:
            message_op = message["op"]
            opcode_name = opcodes.get_name(message_op)
            func_name = "discord_{}".format(opcode_name.lower())

            if hasattr(self, func_name):
                getattr(self, func_name)(message)
            else:
                if hasattr(self, "discord_unknown"):
                    self.discord_unknown(message)
                else:
                    self.log.warn(
                        "Unable to handle message type \"{}\"".format(
                            opcode_name
                        )
                    )
        except Exception:
            self.log.exception("Unable to handle message: {}".format(message))

    def onClose(self, was_clean, code, reason):
        self.log.info(
            "Connection closed ({}): {} - {}".format(
                code, reason, "Clean" if was_clean else "Unclean"
            )
        )

    # endregion

    # region: Send methods

    def send_payload(self, opcode, data):
        packed_data = {
            "op": opcode,
            "d": data
        }

        self.send_raw(packed_data, is_binary=False)

    def send_raw(self, data, is_binary=False):
        if not is_binary:
            return self.sendMessage(
                to_bytes(json.dumps(data)), isBinary=False
            )

        return self.sendMessage(to_bytes(data), isBinary=True)

    def send_identify(self):
        data = {
            "server_id": self.guild_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "token": self.token
        }

        self.send_payload(opcodes.IDENTIFY, data)

    def send_select_protocol(self, address, port):
        data = {
            "protocol": "udp",
            "data": {
                "address": address,
                "port": port,
                "mode": "xsalsa20_poly1305"
            }
        }

        self.send_payload(opcodes.SELECT_PROTOCOL, data)

    def send_ready(self, ssrc, port, modes, heartbeat_interval):
        # Never sent, just here for completeness

        data = {
            "ssrc": ssrc,
            "port": port,
            "modes": modes,
            "heartbeat_interval": heartbeat_interval
        }

        self.send_payload(opcodes.READY, data)

    def send_heartbeat(self):
        self.send_payload(opcodes.HEARTBEAT, time.time() * 1000)

    def send_session_description(self, channel_id, self_mute, self_deaf):
        data = {
            "guild_id": self.guild_id,
            "channel_id": channel_id,
            "self_mute": self_mute,
            "self_deaf": self_deaf
        }

        self.send_payload(opcodes.SESSION_DESCRIPTION, data)

    def send_speaking(self, speaking, ssrc, user_id):
        # Never sent, just here for completeness

        data = {
            "speaking": speaking,
            "ssrc": ssrc,
            "user_id": user_id
        }

        self.send_payload(opcodes.SPEAKING, data)

    # endregion

    # region: Discord message handlers

    def discord_identify(self, message):
        pass

    def discord_select_protocol(self, message):
        pass

    def discord_ready(self, message):
        pass

    def discord_heartbeat(self, message):
        pass

    def discord_session_description(self, message):
        pass

    def discord_speaking(self, message):
        pass

    def discord_unknown(self, message):
        self.log.warn("Unknown message opcode: {}".format(message["op"]))

    # endregion

    pass
