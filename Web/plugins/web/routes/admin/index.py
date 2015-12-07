# coding=utf-8

"""
Admin index page - /admin
"""

__author__ = 'Gareth Coles'

import json

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
                redirect="/admin"
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
            cpu = json.dumps([
                {
                    "x": v[1],
                    "y": float("%0.2f" % v[0])
                } for v in self.plugin.stats.get_cpu()
            ])

            ram = json.dumps([
                {
                    "x": v[1],
                    "y": float("%0.2f" % v[0])
                } for v in self.plugin.stats.get_ram()
            ])

            self.render(
                "admin/index.html",
                ram=ram,
                cpu=cpu,
                total_mem=self.plugin.stats.get_ram_total()
            )
