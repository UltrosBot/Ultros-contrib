# coding=utf-8

"""
Account - create an API key
"""

__author__ = 'Gareth Coles'

from plugins.web.decorators import check_xsrf
from plugins.web.request_handler import RequestHandler


class Route(RequestHandler):

    @check_xsrf
    def post(self, *args, **kwargs):
        s = self.get_session_object()

        if s is None:
            # Not logged in
            self.redirect(
                "/login",
                message="You need to login to access this.",
                message_colour="red",
                redirect="/account"
            )
        else:
            try:
                key = self.plugin.api_keys.create_key(s["username"])
            except Exception as e:
                self.redirect(
                    "/account",
                    message="Error creating API key: %s" % e.message,
                    message_colour="red"
                )
            else:
                self.redirect(
                    "/account",
                    message="API key created: %s" % key
                )
