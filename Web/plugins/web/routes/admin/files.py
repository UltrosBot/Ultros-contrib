"""
Admin files list page - /admin/files
"""

__author__ = 'Gareth Coles'

from collections import OrderedDict

from plugins.web.request_handler import RequestHandler


class Route(RequestHandler):

    name = "admin"

    def get(self, *args, **kwargs):
        s = self.get_session_object()

        if s is None:
            self.redirect(
                "/login",
                message="You need to login to access this.",
                message_colour="red",
                redirect="/admin/files"
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
            storage = self.plugin.storage

            file_objs = OrderedDict()

            file_objs["config"] = OrderedDict(
                sorted(
                    storage.config_files.items()
                )
            )

            file_objs["data"] = OrderedDict(
                sorted(
                    storage.data_files.items()
                )
            )

            self.render(
                "admin/files.html",
                file_objs=file_objs
            )
