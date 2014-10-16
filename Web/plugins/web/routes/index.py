"""
Index page - /
"""

__author__ = 'Gareth Coles'

from plugins.web.request_handler import RequestHandler


class Route(RequestHandler):

    name = "home"

    def get(self, *args, **kwargs):
        self.render(
            "index.html",
            packages=self.plugin.packages.get_installed_packages(),
            plugins=[
                p.info for p in self.plugin.plugins.plugin_objects.values()
            ],
            factories=self.plugin.factory_manager.factories
        )
