from plugins.web.decorators import check_api
from plugins.web.request_handler import RequestHandler

"""
API route for the getting the username for your API key
- /api/plugins/web/get_username
"""

__author__ = 'Gareth Coles'


class Route(RequestHandler):

    name = ""

    @check_api(permission="web.api.get_username", required_key=True)
    def get(self, username, *args, **kwargs):
        return self.finish_json({  # Decorator does all the heavy lifting
            "username": username
        })
