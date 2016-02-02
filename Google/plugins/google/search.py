# coding=utf-8

from txrequests import Session
from utils.html import unescape_html_entities

__author__ = "Gareth Coles"

url = "http://ajax.googleapis.com/ajax/services/search/web"

session = Session()


def get_results(query, page=0, limit=None):
    if limit is None:
        limit = 4

    start = int(page * limit)  # In case some fool passes a float

    if start > 0:
        start -= 1

    return session.get(
        url, params={"v": "1.0", "start": start, "q": query}
    )


def parse_results(json, limit=None):
    if limit is None:
        limit = 4

    result = {}
    i = 1

    for r in json["responseData"]["results"]:
        if i > limit:
            break

        result[unescape_html_entities(r["titleNoFormatting"])] = r["url"]

        i += 1
    return result
