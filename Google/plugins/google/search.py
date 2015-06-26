__author__ = "Gareth Coles"

import treq
from utils.html import unescape_html_entities

url = "http://ajax.googleapis.com/ajax/services/search/web"


def get_results(query, page=0, limit=None):
    if limit is None:
        limit = 4

    start = int(page * limit)  # In case some fool passes a float

    if start > 0:
        start -= 1

    return treq.get(
        url, params={"v": "1.0", "start": start, "q": query}
    )


def parse_results(json, limit=None):
    if limit is None:
        limit = 4

    result = {}
    i = 0

    for r in json["responseData"]["results"]:
        if i > limit:
            break

        result[unescape_html_entities(r["titleNoFormatting"])] = r["url"]

        i += 1
    return result
