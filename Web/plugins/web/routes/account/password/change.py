# coding=utf-8

"""
Account POST for changing password - /account/password/change

Has XSRF protection. Not an API method.
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
            old = self.get_argument("old_password", default=None)
            new = self.get_argument("new_password", default=None)
            new_confirm = self.get_argument("confirm_password", default=False)

            for x in [old, new, new_confirm]:
                if x is None:
                    self.redirect(
                        "/account",
                        message="Please enter your old password, and your new "
                                "password twice.",
                        message_colour="red"
                    )
                    return

            if new != new_confirm:
                self.redirect(
                    "/account",
                    message="Your new passwords don't match.",
                    message_colour="red"
                )
                return

            user = s["username"]

            for x in self.plugin.commands.auth_handlers:
                if x.check_login(user, old):
                    x.change_password(user, old, new)

                    for u in x.get_logged_in_users(s["username"]):
                        x.logout(u, u.protocol)
                        u.respond("You've been logged out, as your "
                                  "password was changed from the Web "
                                  "interface.")

                    self.sessions.delete_sessions_for_user(s["username"])
                    self.clear_session()

                    self.redirect(
                        "/",
                        message="Your password has been changed successfully."
                    )
                    return

            self.redirect(
                "/account",
                message="Incorrect old password supplied.",
                message_colour="red"
            )
