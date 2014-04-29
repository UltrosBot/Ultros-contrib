__author__ = 'Gareth Coles'

from utils.log import getLogger


class Admin(object):

    api_descriptors = []

    logger = None
    plugin = None

    def __init__(self, plugin):
        """
        :type plugin: BottlePlugin
        """
        self.logger = getLogger("Web/Admin")
        self.plugin = plugin

        # TODO: Add routes
        self.plugin.add_route("/admin/files", ["GET"], self.get_files)

    def has_admin(self, r=None):
        return self.plugin.check_permission("web.admin", r=r)

    def get_files(self):
        r = self.plugin.get_objects()
        x = self.plugin.require_login(r)

        if not x[0]:
            return x[1]

        if not self.has_admin(r):
            return self.plugin.wrap_template(
                "You do not have permission to use the admin section.",
                "Unauthorized", "Admin", r
            )

        files = {
            "config": self.plugin.storage.config_files,
            "data": self.plugin.storage.data_files
        }

        content = ""

        table = "\n" \
                "<h2>%s</h2>\n" \
                "\n" \
                "<table class=\"table table-striped table-bordered\">\n" \
                "    <thead>\n" \
                "        <tr>\n" \
                "            <th>Descriptor</th>\n" \
                "            <th>Format</th>\n" \
                "        </tr>\n" \
                "    </thead>\n" \
                "    <tbody>\n" \
                "%s" \
                "    </tbody>\n" \
                " </table>\n" \
                "\n"

        row = "        <tr>\n" \
              "            <td>%s</td>\n" \
              "            <td>%s</td>\n" \
              "        </tr>\n"

        for k in files.keys():
            rows = ""

            for d in files[k].values():
                rows += row % (d.path, d.format)
            content += table % (k.title(), rows)

        return self.plugin.wrap_template(content, "Files", "", r)