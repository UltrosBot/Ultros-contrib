__author__ = 'Gareth Coles'

from bottle import error, request


class Errors(object):

    def __init__(self, plugin):
        """
        :type plugin: BottlePlugin
        """
        self.plugin = plugin
        self.error_404()
        self.error_500()

    def error_404(self):

        @error(404)
        def inner_error(error):
            self.plugin.logger.warn("Page not found!")
            content = """
                <div class="ui warning message">
                    <div class="header">Page not found</div>

                    Path: <strong>%s</strong>
                </div>
            """

            return self.plugin.wrap_template(
                content % request.path,
                "Page not found",
                ""
            )

        return inner_error

    def error_500(self):

        @error(500)
        def inner_error(error):
            self.plugin.logger.warn("Error!")
            content = """
                <div class="ui error message">
                    <div class="header">Internal server error</div>

                    Path: <strong>%s</strong>
                </div>

                <pre class="ui segment">%s</pre>
            """

            return self.plugin.wrap_template(
                content % (request.path, error.traceback),
                "Internal server error",
                ""
            )

        return inner_error
