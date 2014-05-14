__author__ = 'Gareth Coles'

from collections import OrderedDict

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
        self.plugin.add_route("/admin", ["GET"], self.admin)
        self.plugin.add_route("/admin/files", ["GET"], self.get_files)
        self.plugin.add_route("/admin/file/<filetype>/<filename:path>",
                              ["GET"], self.get_file)

        self.plugin.add_route("/admin/file/<filetype>/<filename:path>",
                              ["POST"], self.post_file)

        self.plugin.add_navbar_entry("Admin", "/admin")

    def has_admin(self, r=None):
        return self.plugin.check_permission("web.admin", r=r)

    def error(self, message, r=None):
        message = "" \
                  "<div class=\"alert alert-danger\">" \
                  "    %s" \
                  "</div>" % message
        return self.plugin.wrap_template(message, "Admin | Error", "Admin", r)

    def post_file(self, filetype, filename):
        r = self.plugin.get_objects()
        x = self.plugin.require_login(r)

        if not x[0]:
            return x[1]

        if not self.has_admin(r):
            return self.error(
                "You do not have permission to use the admin section.",
                r
            )

        files = {
            "config": self.plugin.storage.config_files,
            "data": self.plugin.storage.data_files
        }

        filetype = filetype.lower()

        if filetype not in files:
            return self.error("Unknown filetype: %s" % filetype)

        files = files[filetype]

        if filename not in files:
            return self.error("File '%s' does not exist or isn't loaded."
                              % filename)

        fh = files[filename].get()

        if fh.representation is None:
            return self.error("File '%s' cannot be viewed as it has no "
                              "conventional representation." % filename)

        error = False

        data = r.request.forms.get("input", None)

        if data is None:
            return self.error("Invalid request: Missing input data")

        result = fh.validate(data)

        if result[0] is False:
            error = result[1]
        elif isinstance(result[0], list):
            error = []

            for element in result:
                error.append("Line %s: %s" % (element[0], element[1]))

            error = "<br />\n".join(error)

        if error is False:
            # Continue processing
            result = fh.write(data)

            if not result:
                error = "Unable to write file."

        representation = fh.representation

        if representation == "json":
            representation = "javascript"

        return self.plugin.wrap_template(
            data.strip().rstrip("\n").rstrip("\r"), filename, "Admin", r,
            "web/templates/admin/file.html", filename=filename,
            mode=representation, error=error, filetype=filetype,
            success=(True if not error else False)
        )

    def get_file(self, filetype, filename):
        r = self.plugin.get_objects()
        x = self.plugin.require_login(r)

        if not x[0]:
            return x[1]

        if not self.has_admin(r):
            return self.error(
                "You do not have permission to use the admin section.",
                r
            )

        files = {
            "config": self.plugin.storage.config_files,
            "data": self.plugin.storage.data_files
        }

        filetype = filetype.lower()

        if filetype not in files:
            return self.error("Unknown filetype: %s" % filetype)

        files = files[filetype]

        if filename not in files:
            return self.error("File '%s' does not exist or isn't loaded."
                              % filename)

        fh = files[filename].get()

        if fh.representation is None:
            return self.error("File '%s' cannot be viewed as it has no "
                              "conventional representation." % filename)

        representation = fh.representation

        if representation == "json":
            representation = "javascript"

        return self.plugin.wrap_template(
            fh.read()[1].rstrip("\n").rstrip("\r"), filename, "Admin", r,
            "web/templates/admin/file.html", filename=filename,
            mode=representation, error=False, filetype=filetype,
            success=False
        )

    def get_files(self):
        r = self.plugin.get_objects()
        x = self.plugin.require_login(r)

        if not x[0]:
            return x[1]

        if not self.has_admin(r):
            return self.error(
                "You do not have permission to use the admin section.",
                r
            )

        files = {
            "config": OrderedDict(
                sorted(
                    self.plugin.storage.config_files.items()
                )
            ),
            "data": OrderedDict(
                sorted(
                    self.plugin.storage.data_files.items()
                )
            )
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
              "            <td><a href=\"/admin/file/%s/%s\">%s</a></td>\n" \
              "            <td>%s</td>\n" \
              "        </tr>\n"

        for k in files.keys():
            self.logger.debug("Files: %s" % files[k])
            rows = ""

            for d in files[k].keys():
                f = files[k][d]
                rows += row % (k, d, d, f.get().format)
            content += table % (k.title(), rows)

        crumbs = [
            ["Home", "/"],
            ["Admin", "/admin"]
        ]

        return self.plugin.wrap_template(content, "Files", "Admin", r,
                                         breadcrumbs=crumbs,
                                         current_breadcrumb="Files",
                                         use_breadcrumbs=True)

    def admin(self):
        r = self.plugin.get_objects()
        x = self.plugin.require_login(r)

        if not x[0]:
            return x[1]

        if not self.has_admin(r):
            return self.error(
                "You do not have permission to use the admin section.",
                r
            )

        content = """
            <h2>Admin interface</h2>

            <p>
                Welcome to the admin interface. Please note that it is in VERY
                EARLY BETA, and therefore will have bugs and limited
                functionality.
            <p>

            <p>
                So far, the only thing you can do is look at the config and
                data files. If you want to do that,
                <a href="/admin/files">
                    click here
                </a>.
            </p>
        """

        crumbs = [
            ["Home", "/"]
        ]

        return self.plugin.wrap_template(content, "Admin interface", "Admin",
                                         r, breadcrumbs=crumbs,
                                         current_breadcrumb="Admin",
                                         use_breadcrumbs=True)
