# coding=utf-8

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

    @staticmethod
    def from_message(message):
        return Attachment(
            message["id"], message["filename"], message["size"],
            message["url"], message["proxy_url"],
            message.get("height"), message.get("width")
        )


class Embed(object):
    def __init__(self, title, _type, description, url, thumbnail, provider):
        self.title = title
        self.type = _type
        self.description = description
        self.url = url
        self.thumbnail = thumbnail
        self.provider = provider

    @staticmethod
    def from_message(message):
        return Embed(
            message["title"], message["type"], message["description"],
            message["url"],
            EmbedThumbnail.from_message(message["thumbnail"]),
            EmbedProvider.from_message(message["provider"])
        )


class EmbedThumbnail(object):
    def __init__(self, url, proxy_url, height, width):
        self.url = url
        self.proxy_url = proxy_url
        self.height = height
        self.width = width

    @staticmethod
    def from_message(message):
        return EmbedThumbnail(
            message["url"], message["proxy_url"], message["height"],
            message["width"]
        )


class EmbedProvider(object):
    def __init__(self, name, url):
        self.name = name
        self.url = url

    @staticmethod
    def from_message(message):
        return EmbedProvider(
            message["name"], message["url"]
        )


class Role(object):
    def __init__(self, _id, name, color, hoist, position, permissions,
                 managed):
        self.id = int(_id)
        self.name = name
        self.color = color
        self.hoist = hoist
        self.position = position
        self.permissions = permissions
        self.managed = managed

    @property
    def colour(self):
        return self.color
