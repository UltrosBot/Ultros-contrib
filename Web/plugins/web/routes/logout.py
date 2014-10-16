"""
Logout route - /logout
"""

__author__ = 'Gareth Coles'

from plugins.web.request_handler import RequestHandler


class Route(RequestHandler):

    name = "logout"

    def get(self, *args, **kwargs):
        s = self.get_session_key()

        if s is None:
            self.redirect(
                "/",
                message="You're not logged in.",
                message_colour="yellow"
            )

        self.sessions.delete_session(s)

        self.redirect(
            "/login",
            message="Logged out successfully."
        )
