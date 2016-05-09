# coding=utf-8
from system.protocols.discord.permissions import get_permissions

__author__ = 'Gareth Coles'


class Attachment(object):
    def __init__(self, _id, filename, size, url, proxy_url,
                 height=None, width=None):
        self.id = _id
        self.filename = filename
        self.size = size
        self.url = url
        self.proxy_url = proxy_url
        self.height = height
        self.width = width


class Embed(object):
    def __init__(self, title, _type, description, url, thumbnail, provider):
        self.title = title
        self.type = _type
        self.description = description
        self.url = url
        self.thumbnail = thumbnail
        self.provider = provider


class EmbedThumbnail(object):
    def __init__(self, url, proxy_url, height, width):
        self.url = url
        self.proxy_url = proxy_url
        self.height = height
        self.width = width


class EmbedProvider(object):
    def __init__(self, name, url):
        self.name = name
        self.url = url


class Role(object):
    def __init__(self, _id, name, color, hoist, position, permissions,
                 managed):
        self.id = int(_id)
        self.name = name
        self.color = color
        self.hoist = hoist
        self.position = position
        self.permissions = get_permissions(permissions)
        self.managed = managed

    @property
    def colour(self):
        return self.color


class PermissionOverwrite(object):
    def __init__(self, _id, _type, allow, deny):
        self.id = int(_id)
        self.type = _type
        self.allow = allow
        self.deny = deny
