# coding=utf-8

"""
Admin file page - /admin/file/<file>
"""

__author__ = 'Gareth Coles'

from plugins.web.decorators import check_xsrf
from plugins.web.request_handler import RequestHandler


class Route(RequestHandler):

    name = "admin"

    def initialize(self):
        self.css.append("/static/codemirror.css")
        self.css.append("/static/eclipse.css")

        self.js.append("/static/codemirror-compressed.js")

    def get(self, filetype, filename):
        s = self.get_session_object()

        if s is None:
            self.redirect(
                "/login",
                message="You need to login to access this.",
                message_colour="red",
                redirect="/admin/file/%s/%s" % (filetype, filename)
            )
        elif not self.plugin.check_permission("web.admin", s):
            content = """
<div class="ui red fluid message">
    <p>You do not have permission to access the admin section.</p>
    <p> If you feel this was in error, tell a bot admin to give you the
        <code>web.admin</code> permission.
    </p>
</div>
            """

            self.render(
                "generic.html",
                _title="Admin | No permission",
                content=content
            )
        else:
            files = {
                "config": self.plugin.storage.config_files,
                "data": self.plugin.storage.data_files
            }

            filetype = filetype.lower()

            if filetype not in files:
                return self.redirect(
                    "/admin/files",
                    message="Unknown filetype: %s" % filetype,
                    message_colour="red"
                )

            files = files[filetype]

            if filename not in files:
                return self.redirect(
                    "/admin/files",
                    message="This file cannot be found. Is it loaded?",
                    message_colour="red"
                )

            fh = files[filename].get()

            if fh.representation is None:
                return self.redirect(
                    "/admin/files",
                    message="This file cannot be viewed or edited.",
                    message_colour="red"
                )

            representation = fh.representation

            if representation == "json":
                representation = "javascript"

            return self.render(
                "admin/file.html",
                content=fh.read()[1].rstrip("\n").rstrip("\r"),
                filename=filename,
                mode=representation,
                error=False,
                filetype=filetype,
                success=False
            )

    @check_xsrf
    def post(self, filetype, filename):
        s = self.get_session_object()

        if s is None:
            self.redirect(
                "/login",
                message="You need to login to access this.",
                message_colour="red",
                redirect="/admin/file/%s/%s" % (filetype, filename)
            )
        elif not self.plugin.check_permission("web.admin", s):
            content = """
<div class="ui red fluid message">
    <p>You do not have permission to access the admin section.</p>
    <p> If you feel this was in error, tell a bot admin to give you the
        <code>web.admin</code> permission.
    </p>
</div>
            """

            self.render(
                "generic.html",
                _title="Admin | No permission",
                content=content
            )
        else:
            content = self.get_argument("content", default=None)

            files = {
                "config": self.plugin.storage.config_files,
                "data": self.plugin.storage.data_files
            }

            filetype = filetype.lower()

            if filetype not in files:
                return self.redirect(
                    "/admin/files",
                    message="Unknown filetype: %s" % filetype,
                    message_colour="red"
                )

            files = files[filetype]

            if filename not in files:
                return self.redirect(
                    "/admin/files",
                    message="This file cannot be found. Is it loaded?",
                    message_colour="red"
                )

            fh = files[filename].get()

            if fh.representation is None:
                return self.redirect(
                    "/admin/files",
                    message="This file cannot be viewed or edited.",
                    message_colour="red"
                )

            representation = fh.representation

            if representation == "json":
                representation = "javascript"

            if content is None:
                return self.render(
                    "admin/file.html",
                    content=fh.read()[1].rstrip("\n").rstrip("\r"),
                    filename=filename,
                    mode=representation,
                    error="Missing 'content' parameter.",
                    filetype=filetype,
                    success=False
                )

            result = fh.validate(content)
            error = False

            if result[0] is False:
                error = result[1]
            elif isinstance(result[0], list):
                error = []

                for element in result:
                    error.append("Line %s: %s" % tuple(element))

                error = "<br />\n".join(error)

            if error is False:
                result = fh.write(content)

                if not result:
                    error = "Unable to write file."

            return self.render(
                "admin/file.html",
                content=content.rstrip("\n").rstrip("\r"),
                filename=filename,
                mode=representation,
                error=error,
                filetype=filetype,
                success=(True if not error else False)
            )
