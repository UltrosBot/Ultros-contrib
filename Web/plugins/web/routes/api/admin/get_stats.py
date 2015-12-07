# coding=utf-8

"""
API route for the memory graph at the admin index - /api/admin/get_mem
"""

__author__ = 'Gareth Coles'

from plugins.web.request_handler import RequestHandler


class Route(RequestHandler):

    name = ""

    def get(self, *args, **kwargs):
        s = self.get_session_object()

        if s is None:
            self.finish_json(
                {"error": "You must login to use this."}
            )
        elif not self.plugin.check_permission("web.admin", s):
            self.finish_json(
                {"error": "You don't have permission to use this."}
            )
        else:
            cpu = self.plugin.stats.get_cpu_latest()
            ram = self.plugin.stats.get_ram_latest()

            data = {
                "cpu": {"x": cpu[1], "y": float("%0.2f" % cpu[0])},
                "ram": {"x": ram[1], "y": float("%0.2f" % ram[0])}
            }

            self.finish_json(
                data
            )
