# coding=utf-8
from autobahn.twisted import WebSocketClientFactory

from twisted.internet import reactor
from twisted.internet import ssl
from twisted.internet.defer import inlineCallbacks

from txrequests import Session

from system.constants import __version__
from system.protocols.discord.exceptions import InvalidLoginDetailsException
from system.protocols.generic.factory import BaseFactory

__author__ = 'Gareth Coles'

LOGIN_URL = "https://discordapp.com/api/auth/login"
GATEWAY_URL = "https://discordapp.com/api/gateway"


class Factory(BaseFactory, WebSocketClientFactory):
    __version__ = "0.0.1"
    TYPE = "discord"

    gateway = None
    gateway_address = None
    useragent = None
    token = None

    def __init__(self, protocol_name, config, factory_manager):
        BaseFactory.__init__(self, protocol_name, config, factory_manager)

    @inlineCallbacks
    def connect(self):
        self.token = self.config["identity"]["bot_token"]

        try:
            _ = yield self.get_gateway()
        except InvalidLoginDetailsException as e:
            self.logger.error(e.message)
            self.factory_manager.remove_protocol(self.name)
            return
        except Exception:
            self.logger.exception("Error retrieving login token")
            self.factory_manager.remove_protocol(self.name)
            return

        self.logger.trace("Connecting to gateway: {}".format(self.gateway))
        self.useragent = "DiscordBot (https://ultros.io {}); Ultros".format(
            __version__
        )

        WebSocketClientFactory.__init__(
            self, url=self.gateway, useragent=self.useragent
        )

        reactor.connectSSL(
            self.gateway_address,
            443,
            self,
            ssl.ClientContextFactory()
        )

    @inlineCallbacks
    def get_gateway(self):
        s = Session()

        r = yield s.get(GATEWAY_URL, headers={
            "Authorization": "Bot {}".format(self.token)
        })

        data = r.json()
        self.gateway = data["url"] + "/encoding=json?v=4"
        self.gateway_address = self.gateway.split("://", 1)[1].split("/", 1)[0]
