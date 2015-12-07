# coding=utf-8

"""
Account - delete an API key
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
            key = self.get_argument("key", default=None)

            if key is None:
                self.redirect(
                    "/account",
                    message="Missing or invalid API key.",
                    message_colour="red"
                )
            else:
                if not self.plugin.api_keys.is_owner(s["username"], key):
                    self.redirect(
                        "/account",
                        message="Missing or invalid API key.",
                        message_colour="red"
                    )
                else:
                    if self.plugin.api_keys.delete_key(key):
                        self.redirect(
                            "/account",
                            message="API key removed successfully."
                        )
                    else:
                        self.redirect(
                            "/account",
                            message="Missing or invalid API key.",
                            message_colour="red"
                        )
