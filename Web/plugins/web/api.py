__author__ = 'Gareth Coles'

from utils.log import getLogger


class API(object):

    api_descriptors = []

    logger = None
    plugin = None

    def __init__(self, plugin):
        """
        :type plugin: BottlePlugin
        """
        self.logger = getLogger("Web/API")
        self.plugin = plugin

        # TODO: Add routes
        self.add_callback("/api", "/api", self.list_methods)
        self.plugin.add_route("/api", ["GET"], self.list_methods)

    def add_callback(self, path, descriptor, function):
        if descriptor in self.api_descriptors:
            return False

        r = self.plugin.add_route(path, ["POST"], function)

        if r:
            self.api_descriptors.append(descriptor)

        return r

    def list_methods(self):
        return {"methods": self.api_descriptors}
