"""
Login reset page - /login/reset
"""

__author__ = 'Gareth Coles'

from plugins.web.request_handler import RequestHandler


class Route(RequestHandler):

    name = "login-reset"

    default_reset_message = """
The bot administrator didn't fill this section out.

Please ask them to add or fill out the "reset_message" option in their
config/plugins/web.yml file.
    """

    def get(self, *args, **kwargs):
        self.render(
            "login-reset.html",
            message=self.plugin.config.get(
                "reset_message",
                self.default_reset_message
            )
        )
