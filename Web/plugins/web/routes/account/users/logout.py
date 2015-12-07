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
            user = self.get_argument("user", default=None)

            h = self.plugin.commands.auth_handler

            for u in h.get_logged_in_users(s["username"]):
                if str(id(u)) == user:
                    h.logout(u, u.protocol)
                    u.respond(
                        "You have been logged out via the web interface."
                    )

                    self.redirect(
                        "/account",
                        message="Session logged out successfully."
                    )
                    break

            self.redirect(
                "/account",
                message="Invalid user specified.",
                message_colour="red"
            )
