__author__ = 'Gareth Coles'

import psutil
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

        self.plugin.add_route("/admin/get_mem", ["GET"], self.get_mem)

        self.plugin.add_navbar_entry("Admin", "/admin", "settings")

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

        table = "<h2 class=\"ui header\">%s</h2>" \
                "\n" \
                "<table class=\"ui table segment\">\n" \
                "    <thead>\n" \
                "        <tr>\n" \
                "            <th style=\"width: 60%%\">Descriptor</th>\n" \
                "            <th style=\"width: 15%%\">Editable</th>\n" \
                "            <th style=\"width: 25%%\">Format</th>\n" \
                "        </tr>\n" \
                "    </thead>\n" \
                "    <tbody>\n" \
                "%s" \
                "    </tbody>\n" \
                " </table>\n" \
                "\n"

        row = "        <tr>\n" \
              "          <td style=\"width: 60%%\">" \
              "                <a href=\"/admin/file/%s/%s\">%s</a>" \
              "            </td>\n" \
              "          <td style=\"width: 15%%;\" class=\"positive\">" \
              "                Yes" \
              "            </td>" \
              "          <td style=\"width: 25%%\">%s</td>\n" \
              "        </tr>\n"

        row_error = "        <tr>\n" \
                    "          <td style=\"width: 60%%\">" \
                    "                %s" \
                    "            </td>\n" \
                    "         <td style=\"width: 15%%;\" class=\"negative\">" \
                    "                No" \
                    "            </td>" \
                    "          <td style=\"width: 25%%\">" \
                    "               %s" \
                    "            </td>\n" \
                    "        </tr>\n"

        for k in files.keys():
            self.logger.trace("Files: %s" % files[k])
            rows = ""

            for d in files[k].keys():
                f = files[k][d]

                if f.get().representation is None:
                    rows += row_error % (d, f.get().format)
                else:
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

    def get_mem(self):
        p = psutil.Process()  # This process

        # Memory used by this process
        proc_used_mb = (float(p.memory_info().rss) / 1024) / 1024

        return '{"y": %0.2f}' % proc_used_mb

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

        mem = psutil.virtual_memory()
        mem_mb = (float(mem.total) / 1024) / 1024  # Total memory

        content = """            <div class="ui labeled icon menu">
                <a class="green active item">
                    <i class="home icon"></i>
                    Home
                </a>
                <a class="item" href="/admin/files">
                    <i class="file outline icon"></i>
                    Files
                </a>
            </div>

            <div class="ui attached fluid segment">
                    Memory usage (out of <strong>%0.2fMB</strong>)
            </div>
            <div id="mem_chart" class="ui attached fluid segment"
                 style="height:400px;">
            </div>

            <script>
                var mem_chart;

                function request_mem_data() {
                    $.ajax({
                        url: '/admin/get_mem',
                        success: function(json) {

                            var series = mem_chart.series[0],
                                point = JSON.parse(json),
                                shift = series.data.length > 20;
                                // shift if the series is longer than 20

                            console.log(json);
                            console.log(point);

            var d = new Date();
                x = d.getTime(),
                y = point.y;

                            point = [x, y];

                            console.log(point);

                            // add the point
                            mem_chart.series[0].addPoint(point, true, shift);

                            // call it again after one second
                            setTimeout(request_mem_data, 5000);
                        },
                        cache: false
                    });
                }

                $(document).ready(function() {
                    mem_chart = new Highcharts.Chart({
                        chart: {
                            renderTo: "mem_chart",
                            type: 'spline'
                        },
                        title: "",
                        tooltip: {
                            formatter: function () {
                    return this.series.name + "<br /><b>" + this.y + "MB</b>";
                            }
                        },
                        animation: true,
                        xAxis: {
                            labels: {
                                formatter: function() {
                                    // Because PEP8
                                    return Highcharts.dateFormat(
                                        "%%H:%%M:%%S", this.value, false
                                    );
                                }
                            },
                            gridLineWidth: 1 //,
                            //type: "datetime"
                        },
                        yAxis: {
                            title: {
                                text: 'Memory usage'
                            }, labels: {
                                formatter: function() {
                                    return this.value + "MB";
                                }
                            },
                            gridLineWidth: 1,
                            min: 0
                        },
                        series:
                        [{
                            name: 'Used by Ultros',
                            data: []
                        }]
                    });

                    request_mem_data();
                });
            </script>"""

        # I did not know this was possible.
        content %= mem_mb

        crumbs = [
            ["Home", "/"]
        ]

        return self.plugin.wrap_template(content, "Admin interface", "Admin",
                                         r, breadcrumbs=crumbs,
                                         current_breadcrumb="Admin",
                                         use_breadcrumbs=True)
