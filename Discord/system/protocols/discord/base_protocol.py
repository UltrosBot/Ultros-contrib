# coding=utf-8
import json
import platform
import zlib

from autobahn.twisted import WebSocketClientProtocol
from kitchen.text.converters import to_bytes
from twisted.internet.defer import inlineCallbacks, returnValue
from txrequests import Session

from system.constants import __version__
from system.protocols.discord import opcodes
from system.protocols.generic.protocol import ChannelsProtocol

__author__ = 'Gareth Coles'

API_URL = "https://discordapp.com/api/{}"


class DiscordProtocol(ChannelsProtocol, WebSocketClientProtocol):
    whitelist_warning_logged = False

    def __init__(self, name, factory, config):
        WebSocketClientProtocol.__init__(self)
        ChannelsProtocol.__init__(self, name, factory, config)

    @property
    def token(self):
        return self.factory.token

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

    # region: Send functions

    def send_heartbeat(self, seq):
        self.send_payload(opcodes.HEARTBEAT, seq)

    def send_identify(self, token):
        payload = {
            "token": token,
            "properties": {
                "$os": platform.system(),
                "$browser": "Ultros",
                "$device": "Ultros",
                "$referrer": "",
                "$referring_domain": ""
            },
            "compress": True,
            "large_threshold": 250
        }

        self.send_payload(opcodes.IDENTIFY, payload)

    def send_status_update(self, idle_since=None, game=None):
        payload = {
            "idle_since": idle_since,
            "game": {
                "name": game
            }
        }

        self.send_payload(opcodes.STATUS_UPDATE, payload)

    def send_voice_state_update(self, guild_id, self_mute, self_deaf,
                                channel_id=None):
        payload = {
            "guild_id": guild_id,
            "channel_id": channel_id,
            "self_mute": self_mute,
            "self_deaf": self_deaf
        }

        self.send_payload(opcodes.VOICE_STATE_UPDATE, payload)

    def send_voice_server_ping(self):
        raise NotImplementedError(
            "This method is not documented in the Discord documentation"
        )

    def send_resume(self, token, session_id, seq):
        payload = {
            "token": token,
            "session_id": session_id,
            "seq": seq
        }

        self.send_payload(opcodes.RESUME, payload)

    def send_request_guild_members(self, guild_id, query="", limit=0):
        payload = {
            "guild_id": guild_id,
            "query": query,
            "limit": limit
        }

        self.send_payload(opcodes.REQUEST_GUILD_MEMBERS, payload)

    def send_payload(self, opcode, data):
        packed_data = {
            "op": opcode,
            "d": data
        }

        self.send_raw(packed_data, is_binary=False)

    def send_raw(self, data, is_binary=False):
        if not is_binary:
            return self.sendMessage(to_bytes(json.dumps(data)), isBinary=False)
        return self.sendMessage(to_bytes(data), isBinary=True)

    # endregion

    # region: Web API: Utils

    @inlineCallbacks
    def make_request(self, path, method="GET", **kwargs):
        s = Session()
        url = API_URL.format(path)

        headers = {
            "Content-Type": "application/json",
            "Authorization": self.token,
            "User-Agent": "DiscordBot (https://ultros.io {}); Ultros".format(
                __version__
            )
        }

        func = getattr(s, method.lower())

        result = yield func(
            url, headers=headers, **kwargs
        )

        if result.status_code != 200:
            result.raise_for_status()

        returnValue(result)
        return

    # endregion

    # region: Web API: Channels

    @inlineCallbacks
    def web_get_channel(self, channel_id):
        result = yield self.make_request("channels/{}".format(channel_id))

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_modify_channel(self, channel_id, data):
        result = yield self.make_request(
            "channels/{}".format(channel_id), "PUT", json=data
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_delete_channel(self, channel_id):
        result = yield self.make_request(
            "channels/{}".format(channel_id), "DELETE"
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_get_channel_messages(self, channel_id, before=None, after=None,
                                 limit=50):
        data = {
            "limit": limit
        }

        if before is not None:
            data["before"] = before
        elif after is not None:
            data["after"] = after

        result = yield self.make_request(
            "channels/{}/messages".format(channel_id),
            params=data
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_create_message(self, channel_id, message, nonce=None, tts=False):
        data = {
            "content": message,
            "tts": tts
        }

        if nonce is not None:
            data["nonce"] = nonce

        result = yield self.make_request(
            "channels/{}/messages".format(channel_id), "POST", json=data
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_edit_message(self, channel_id, message_id, content):
        data = {
            "content": content
        }

        result = yield self.make_request(
            "channels/{}/messages/{}".format(channel_id, message_id),
            "PATCH",
            json=data
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_delete_message(self, channel_id, message_id):
        result = yield self.make_request(
            "channels/{}/messages/{}".format(channel_id, message_id),
            "DELETE"
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_ack_message(self, channel_id, message_id):
        result = yield self.make_request(
            "channels/{}/messages/{}/ack".format(channel_id, message_id),
            "POST"
        )

        returnValue(result)
        return

    @inlineCallbacks
    def web_edit_channel_permissions(self, channel_id, overwrite_id, allow,
                                     deny):
        data = {
            "allow": allow,
            "deny": deny
        }

        result = yield self.make_request(
            "channels/{}/permissions/{}".format(channel_id, overwrite_id),
            "PUT", json=data
        )

        returnValue(result)
        return

    @inlineCallbacks
    def web_get_channel_invites(self, channel_id):
        result = yield self.make_request(
            "channels/{}/invites".format(channel_id),
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_create_channel_invite(self, channel_id, max_age=86400, max_uses=0,
                                  temporary=False, xkcdpass=False):
        data = {
            "max_age": max_age,
            "max_uses": max_uses,
            "temporary": temporary,
            "xkcdpass": xkcdpass
        }

        result = yield self.make_request(
            "channels/{}/invites".format(channel_id),
            "POST", json=data
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_delete_channel_permission(self, channel_id, overwrite_id):
        result = yield self.make_request(
            "channels/{}/permissions/{}".format(channel_id, overwrite_id),
            "DELETE"
        )

        returnValue(result)
        return

    @inlineCallbacks
    def web_trigger_typing_indicator(self, channel_id):
        result = yield self.make_request(
            "channels/{}/typing".format(channel_id),
            "POST"
        )

        returnValue(result)
        return

    # endregion

    # region: Web API: Guilds

    @inlineCallbacks
    def web_create_guild(self, name, region, icon=None):
        if not self.whitelist_warning_logged:
            self.log.debug(
                "Note: Only white-listed bots may create guilds. If you think "
                "you have a good reason to do this and haven't already, "
                "contact support@discordapp.com and explain why your bot "
                "should be allowed to do this, and what it's for."
            )

            self.whitelist_warning_logged = True

        data = {
            "name": name,
            "region": region
        }

        if icon is not None:
            data["icon"] = icon

        result = yield self.make_request(
            "guilds", "POST", json=data
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_get_guild(self, guild_id):
        result = yield self.make_request(
            "guilds/{}".format(guild_id),
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_modify_guild(self, guild_id, **kwargs):
        keys = [
            "name", "region", "verification_level", "afk_channel_id",
            "afk_timeout", "icon", "owner_id", "splash"
        ]

        for k in kwargs.keys():
            if k not in keys:
                raise KeyError(
                    "Unknown key for guild modification: {}".format(k)
                )

        result = yield self.make_request(
            "guilds/{}".format(guild_id),
            "PATCH", json=kwargs
        )

        returnValue(result)
        return

    @inlineCallbacks
    def web_delete_guild(self, guild_id):
        result = yield self.make_request(
            "guilds/{}".format(guild_id),
            "DELETE"
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_get_guild_channels(self, guild_id):
        result = yield self.make_request(
            "guilds/{}/channels".format(guild_id),
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_create_guild_channel(self, guild_id, name, _type, bitrate):
        _type = _type.lower()

        if _type == "text":
            data = {
                "name": name,
                "type": _type
            }
        elif _type == "voice":
            data = {
                "name": name,
                "type": _type,
                "bitrate": bitrate
            }
        else:
            raise NameError("Unknown channel type: {}".format(_type))

        result = yield self.make_request(
            "guilds/{}/channels".format(guild_id),
            "POST", json=data
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_modify_guild_channel(self, guild_id, channel_id, position):
        data = {
            "id": channel_id,
            "position": position
        }

        result = yield self.make_request(
            "guilds/{}/channels".format(guild_id),
            "PATCH", json=data
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_get_guild_member(self, guild_id, user_id):
        result = yield self.make_request(
            "guilds/{}/members/{}".format(guild_id, user_id),
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_list_guild_members(self, guild_id, limit=1, offset=0):
        data = {
            "limit": limit,
            "offset": offset
        }

        result = yield self.make_request(
            "guilds/{}/members".format(guild_id),
            params=data
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_modify_guild_member(self, guild_id, user_id, roles=None,
                                mute=None, deaf=None, channel_id=None):

        data = {}

        if roles is not None:
            data["roles"] = roles
        if mute is not None:
            data["mute"] = mute
        if deaf is not None:
            data["deaf"] = deaf
        if channel_id is not None:
            data["channel_id"] = channel_id

        result = yield self.make_request(
            "guilds/{}/members/{}".format(guild_id, user_id),
            "PATCH", json=data
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_remove_guild_member(self, guild_id, user_id):
        result = yield self.make_request(
            "guilds/{}/members/{}".format(guild_id, user_id),
            "DELETE"
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_get_guild_bans(self, guild_id):
        result = yield self.make_request(
            "guilds/{}/bans".format(guild_id),
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_create_guild_ban(self, guild_id, user_id, delete_message_days=0):
        data = {
            "delete-message-days": delete_message_days
        }

        result = yield self.make_request(
            "guilds/{}/bans/{}".format(guild_id, user_id),
            "PUT", json=data
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_remove_guild_ban(self, guild_id, user_id):
        result = yield self.make_request(
            "guilds/{}/bans/{}".format(guild_id, user_id),
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_get_guild_roles(self, guild_id):
        result = yield self.make_request(
            "guilds/{}/roles".format(guild_id),
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_create_guild_role(self, guild_id):
        result = yield self.make_request(
            "guilds/{}/roles".format(guild_id),
            "POST"
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_modify_guild_role(self, guild_id, role_id, **kwargs):
        keys = {
            "name", "permissions", "position", "color", "hoist"
        }

        for k in kwargs.keys():
            if k not in keys:
                raise KeyError(
                    "Unknown key for guild role modification: {}".format(k)
                )

        result = yield self.make_request(
            "guilds/{}/roles/{}".format(guild_id, role_id),
            "PATCH", json=kwargs
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_delete_guild_role(self, guild_id, role_id):
        result = yield self.make_request(
            "guilds/{}/roles/{}".format(guild_id, role_id),
            "DELETE"
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_get_guild_prune_count(self, guild_id, days=1):
        data = {
            "days": days
        }

        result = yield self.make_request(
            "guilds/{}/prune".format(guild_id),
            "GET", params=data
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_begin_guild_prune(self, guild_id, days=1):
        data = {
            "days": days
        }

        result = yield self.make_request(
            "guilds/{}/prune".format(guild_id),
            "POST", json=data
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_get_guild_voice_regions(self, guild_id):
        result = yield self.make_request(
            "guilds/{}/regions".format(guild_id),
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_get_guild_invites(self, guild_id):
        result = yield self.make_request(
            "guilds/{}/invites".format(guild_id),
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_get_guild_integrations(self, guild_id):
        result = yield self.make_request(
            "guilds/{}/integrations".format(guild_id),
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_create_guild_integration(self, guild_id, _type, integration_id):
        data = {
            "type": _type,
            "id": integration_id
        }

        result = yield self.make_request(
            "guilds/{}/integrations".format(guild_id),
            "POST", json=data
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_modify_guild_integration(self, guild_id, integration_id, **kwargs):
        keys = [
            "expire_behavior", "expire_grace_period", "enable_emoticons"
        ]

        for k in kwargs.keys():
            if k not in keys:
                raise KeyError(
                    "Unknown key for guild integration modification: "
                    "{}".format(k)
                )

        result = yield self.make_request(
            "guilds/{}/integrations/{}".format(guild_id, integration_id),
            "PATCH", json=kwargs
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_delete_guild_integration(self, guild_id, integration_id):
        result = yield self.make_request(
            "guilds/{}integrations/{}".format(guild_id, integration_id),
            "DELETE"
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_sync_guild_integration(self, guild_id, integration_id):
        result = yield self.make_request(
            "guilds/{}/integrations/{}/sync".format(guild_id, integration_id),
            "POST"
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_get_guild_embed(self, guild_id):
        result = yield self.make_request(
            "guilds/{}/embed".format(guild_id),
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_modify_guild_embed(self, guild_id, **kwargs):
        keys = [
            "enabled", "channel_id"
        ]

        for k in kwargs.keys():
            if k not in keys:
                raise KeyError(
                    "Unknown key for guild embed modification: {}".format(k)
                )

        result = yield self.make_request(
            "guilds/{}/embed".format(guild_id),
            "PATCH", json=kwargs
        )

        returnValue(result.json())
        return

    # endregion

    # region: Web API: Users

    @inlineCallbacks
    def web_query_users(self, username, limit=25):
        data = {
            "q": username,
            "limit": limit
        }

        result = yield self.make_request(
            "users".format(),
            params=data
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_get_current_user(self):
        result = yield self.make_request("users/@me")  # TODO: Test

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_get_user(self, user_id):
        result = yield self.make_request(
            "users/{}".format(user_id),
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_modify_current_user(self, **kwargs):
        keys = [
            "username", "email", "password", "new_password", "avatar"
        ]

        for k in kwargs.keys():
            if k not in keys:
                raise KeyError(
                    "Unknown key for user modification: {}".format(k)
                )

        if "new_password" in kwargs and "password" not in kwargs:
            raise KeyError("Must provide the old password when changing it")

        result = yield self.make_request(
            "users/@me", "PATCH", json=kwargs
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_get_current_user_guilds(self):
        result = yield self.make_request("users/@me/guilds")

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_leave_guild(self, guild_id):
        result = yield self.make_request(
            "users/@me/guilds/{}".format(guild_id),
            "DELETE"
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_get_user_dms(self):
        result = yield self.make_request("users/@me/channels")

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_create_dm(self, user_id):
        data = {
            "recipient_id": str(user_id)
        }

        result = yield self.make_request(
            "users/@me/channels", "POST", json=data
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_get_connections(self):
        result = yield self.make_request("users/@me/connections")

        returnValue(result.json())
        return

    # endregion

    # region: Web API: Invites

    @inlineCallbacks
    def web_get_invite(self, invite_id):
        result = yield self.make_request(
            "invites/{}".format(invite_id)
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_delete_invite(self, invite_id):
        result = yield self.make_request(
            "invites/{}".format(invite_id),
            "DELETE"
        )

        returnValue(result.json())
        return

    @inlineCallbacks
    def web_accept_invite_not_for_bots(self, invite_id):
        # Note: Bots may not use this. It's just here for completeness.
        result = yield self.make_request(
            "invites/{}".format(invite_id),
            "POST"
        )

        returnValue(result.json())
        return

    # endregion

    # region: Web API: Voice

    @inlineCallbacks
    def web_list_voice_regions(self):
        result = yield self.make_request("voice/regions")

        returnValue(result.json())
        return

    # endregion

    # region: Web API: Applications

    def web_get_oauth2_application(self):
        result = yield self.make_request("oauth2/applications/@me")

        returnValue(result.json())
        return

    # endregion

    pass
