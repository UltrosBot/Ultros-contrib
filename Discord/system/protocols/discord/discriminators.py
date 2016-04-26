# coding=utf-8

"""
Discriminators are used to refer to channels and guilds with unique IDs that
try to be somewhat user-friendly.

This requires a mappings file, which is always available for the user to read
on-disk or via the web interface.
"""

from weakref import ref

from system.storage.formats import YAML
from system.storage.manager import StorageManager

__author__ = 'Gareth Coles'


class DiscriminatorManager(object):
    storage = None
    data = None

    def __init__(self, protocol):
        #: :type protocol: system.protocols.discord.protocol.Protocol
        self._protocol = ref(protocol)

    @property
    def protocol(self):
        return self._protocol()

    def setup(self):
        self.storage = StorageManager()

        self.data = self.storage.get_file(
            self.protocol, "data", YAML,
            "protocols/{}/mappings.yml".format(self.protocol.name)
        )

        with self.data:
            if "guilds" not in self.data:
                self.data["guilds"] = {}
            if "channels" not in self.data:
                self.data["channels"] = {}
            if "highest" not in self.data:
                self.data["highest"] = {
                    "guild": 0,
                    "channel": 0
                }

    def get_guild_discriminator(self, _id):
        _id = int(_id)

        if _id not in self.data["guilds"]:
            discriminator = self.create_guild_discriminator()

            with self.data:
                self.data["guilds"][_id] = discriminator
        else:
            discriminator = self.data["guilds"][_id]

        return discriminator

    def get_channel_discriminator(self, _id):
        _id = int(_id)

        if _id not in self.data["channels"]:
            discriminator = self.create_channel_discriminator()

            with self.data:
                self.data["channels"][_id] = discriminator
        else:
            discriminator = self.data["channels"][_id]

        return discriminator

    def create_guild_discriminator(self):
        discriminator = self.data["highest"]["guild"] + 1

        with self.data:
            self.data["highest"]["guild"] = discriminator

        return discriminator

    def create_channel_discriminator(self):
        discriminator = self.data["highest"]["channel"] + 1

        with self.data:
            self.data["highest"]["channel"] = discriminator

        return discriminator
