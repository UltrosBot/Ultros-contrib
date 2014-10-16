"""
Login page - /login
"""

__author__ = 'Gareth Coles'

from plugins.web.decorators import check_xsrf
from plugins.web.request_handler import RequestHandler


class Route(RequestHandler):

    name = "login"

    def get(self, *args, **kwargs):
        s = self.get_session_object()
        r = self.get_argument("redirect", default=None)

        if s is None:
            self.render(
                "login.html",
                redirect=r
            )
        else:
            self.redirect(
                "/",
                message="You are already logged in.",
                message_colour="yellow"
            )

    @check_xsrf
    def post(self, *args, **kwargs):
        s = self.get_session_object()
        redirect = self.get_argument("redirect", default="/")

        if s is None:
            username = self.get_argument("username", default=None)
            password = self.get_argument("password", default=None)
            remember = self.get_argument("remember", default=False)

            for x in [username, password]:
                if x is None:
                    return self.render(
                        "login.html",
                        missing=True
                    )

            r = self.plugin.sessions.check_login(username, password)

            if r:
                key = self.plugin.sessions.create_session(username, remember)
                self.set_session(key, remember)

                self.redirect(
                    redirect,
                    message="Logged in successfully."
                )
            else:
                self.render(
                    "login.html",
                    failed=True
                )
        else:
            self.redirect(
                redirect,
                message="You are already logged in.",
                message_colour="yellow"
            )
