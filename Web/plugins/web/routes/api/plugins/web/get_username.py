"""
API route for the getting the username for your API key
- /api/plugins/web/get_username
"""

__author__ = 'Gareth Coles'

from plugins.web.decorators import check_api
from plugins.web.request_handler import RequestHandler


class Route(RequestHandler):

    name = ""

    @check_api
    def get(self, username, *args, **kwargs):
        self.finish_json({
            "username": username
        })
