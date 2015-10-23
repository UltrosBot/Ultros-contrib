# coding=utf-8

from txrequests import Session

from plugins.urls import ShortenerDown
from plugins.urls.matching import is_url
from plugins.urls.shorteners import base

__author__ = 'Gareth Coles'


class IsGdShortener(base.Shortener):
    base_url = "http://is.gd/create.php"
    name = "is.gd"

    def do_shorten(self, context):
        session = Session()

        params = {"url": unicode(context["url"]), "format": "simple"}

        d = session.get(self.base_url, params=params)

        d.addCallbacks(
            self.shorten_success, self.shorten_error
        )

        return d

    def shorten_success(self, response):
        """
        :type response: requests.Response
        """

        if response.status_code != 200:
            raise ShortenerDown("HTTP code {}".format(response.status_code))

        url = response.text

        if not is_url(url):
            raise ShortenerDown("Service did not return a URL")

        return url

    def shorten_error(self, error):
        """
        :type error: twisted.python.failure.Failure
        """

        self.urls_plugin.logger.warning(
            "[is.gd] Error fetching URL: {0}".format(error.getErrorMessage())
        )

        return error
