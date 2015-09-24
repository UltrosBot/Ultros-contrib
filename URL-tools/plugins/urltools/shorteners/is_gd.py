from txrequests import Session
from plugins.urls.shorteners import base

reload(base)

__author__ = 'Gareth Coles'


class IsGdShortener(base.Shortener):
    base_url = "http://is.gd/create.php"
    name = "is.gd"

    def do_shorten(self, context):
        session = Session()

        params = {"url": context["url"].text, "format": "simple"}

        d = session.get(self.base_url, params=params)

        d.addCallbacks(
            self.shorten_success, self.shorten_error
        )

        return d

    def shorten_success(self, response):
        """
        :type response: requests.Response
        """

        return response.text

    def shorten_error(self, error):
        """
        :type error: twisted.python.failure.Failure
        """

        self.urls_plugin.logger.warning(
            "[is.gd] Error fetching URL: {0}".format(error.getErrorMessage())
        )

        return error

shortener = IsGdShortener
