"""
Index page - /
"""

__author__ = 'Gareth Coles'

from plugins.web.request_handler import RequestHandler


class Route(RequestHandler):

    name = "home"

    def get(self, *args, **kwargs):
        s = self.get_session_object()

        packages = None
        plugins = None
        factories = None

        if self.plugin.check_permission("web.index.plugins", s):
            packages = self.plugin.packages.get_installed_packages()
            plugins = [
                p.info for p in self.plugin.plugins.plugin_objects.values()
            ]

        if self.plugin.check_permission("web.index.protocols", s):
            factories = self.plugin.factory_manager.factories

        self.render(
            "index.html",
            packages=packages,
            plugins=plugins,
            factories=factories
        )
