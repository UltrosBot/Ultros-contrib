"""
API route for the getting the username for your API key
- /api/plugins/web/get_username
"""

__author__ = 'Gareth Coles'

from plugins.web.api_errors import permissions_error, invalid_key_error
from plugins.web.decorators import check_api
from plugins.web.request_handler import RequestHandler


class Route(RequestHandler):

    name = ""

    @check_api
    def get(self, username, *args, **kwargs):
        if username is None:
            # Invalid API key
            return self.finish_json(
                invalid_key_error()
            )
        if self.plugin.check_permission(
            "web.api.get_username", username
        ):
            # Valid API key and user has permission
            return self.finish_json({
                "username": username
            })

        # Valid API key, but user doesn't have permission
        self.finish_json(
            permissions_error("web.api.get_username")
        )
