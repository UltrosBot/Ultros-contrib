# coding=utf-8

from plugins.web.request_handler import RequestHandler

__author__ = 'Gareth Coles'


class Route(RequestHandler):
    def post(self, *args, **kwargs):
        payload = self.request.body

        fh = open("logs/gh-{}.json".format(
            self.request.headers.get("X-Github-Event")
        ), "w")
        fh.write(payload)
        fh.flush()
        fh.close()
