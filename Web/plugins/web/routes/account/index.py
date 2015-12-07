# coding=utf-8

"""
Account page - /account
"""

__author__ = 'Gareth Coles'

from plugins.web.request_handler import RequestHandler


class Route(RequestHandler):

    name = "account"

    def get(self, *args, **kwargs):
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
            api_keys = self.plugin.api_keys.get_keys(s["username"])

            h = self.plugin.commands.auth_handler
            users = h.get_logged_in_users(s["username"])

            self.render(
                "account.html",
                api_keys=api_keys,
                users=users
            )
