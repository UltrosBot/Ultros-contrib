# coding=utf-8
import random
import urlparse
from datetime import datetime, timedelta

import re
from twisted.internet.defer import inlineCallbacks, returnValue
from txrequests import Session

from plugins.urls.constants import CASCADE, STOP_HANDLING
from plugins.urls.handlers.handler import URLHandler
from plugins.urltools_nsfw.handlers.flist.misc import flatten_kinks, \
    flatten_character
from utils.misc import str_to_regex_flags
from plugins.urltools_nsfw.exceptions import ApiKeyMissing

__author__ = 'Gareth Coles'

URL_BASE = "http://www.f-list.net/json/api"
URL_TICKET = "http://www.f-list.net/json/getApiTicket.php"  # For some reason..

URL_CHAR_INFO = URL_BASE + "/character-info.php"
URL_CHAR_KINKS = URL_BASE + "/character-kinks.php"

strings = {
    # Name, gender, species, orientation, relationship, kinks
    "character": u"[F-List character] {given[name]} "
                 u"({general_details[gender]} {general_details[species]}) "
                 u"{general_details[orientation]} / "
                 u"{general_details[relationship]} / "
                 u"Fave: {sample_kinks[fave]} / "
                 u"Yes: {sample_kinks[yes]} / "
                 u"Maybe: {sample_kinks[maybe]} / "
                 u"No: {sample_kinks[no]}"
}


class FListHandler(URLHandler):
    criteria = {
        "protocol": re.compile(r"http|https", str_to_regex_flags("iu")),
        "domain": re.compile(
            r"(www\.f-list\.net)|(f-list\.net)",
            str_to_regex_flags("iu")
        ),
        "path": re.compile(r"/c/.*", str_to_regex_flags("iu")),
        "permission": "urls.trigger.nsfw"
    }

    ticket = ""  # API auth ticket; needs manual renewing
    last_renewal = None  # So we know when we renewed last
    session = None

    name = "f-list"

    @property
    def username(self):
        return self.plugin.config.get("f-list", {}).get("username", "")

    @property
    def password(self):
        return self.plugin.config.get("f-list", {}).get("password", "")

    @property
    def kinks_limit(self):
        return self.plugin.config.get("f-list", {}).get("kink-sample", 2)

    def __init__(self, plugin):
        super(FListHandler, self).__init__(plugin)

        if not (self.username and self.password):
            raise ApiKeyMissing()

        self.reload()
        self.get_ticket()

    def reload(self):
        self.teardown()

        self.session = Session()

    def teardown(self):
        if self.session is not None:
            self.session.close()

    def get_string(self, string):
        formatting = self.plugin.config.get("osu", {}).get("formatting", {})

        if string not in formatting:
            return strings[string]
        return formatting[string]

    @inlineCallbacks
    def get(self, *args, **kwargs):
        r = yield self.session.get(*args, **kwargs)
        data = r.json()

        if "error" in data and data["error"]:
            raise FListError(data["error"])

        returnValue(data)

    @inlineCallbacks
    def post(self, *args, **kwargs):
        r = yield self.session.post(*args, **kwargs)
        data = r.json()

        if "error" in data and data["error"]:
            raise FListError(data["error"])

        returnValue(data)

    @inlineCallbacks
    def get_ticket(self):
        now = datetime.now()
        then = now - timedelta(minutes=4)

        if not self.last_renewal or then > self.last_renewal:
            data = yield self.post(
                URL_TICKET, params={
                    "account": self.username,
                    "password": self.password
                }
            )

            self.ticket = data["ticket"]
            self.last_renewal = datetime.now()

        returnValue(self.ticket)

    def get_sample(self, items, count):
        if not items:
            return ["Nothing"]
        if len(items) <= count:
            return items
        return [i for i in random.sample(items, count)]

    @inlineCallbacks
    def call(self, url, context):
        target = url.path

        while target.endswith("/"):
            target = target[:-1]

        target = target.split("/")

        if "" in target:
            target.remove("")
        if " " in target:
            target.remove(" ")

        message = ""

        try:
            if len(target) < 2:  # It's the front page or invalid, don't bother
                returnValue(CASCADE)
            elif target[0].lower() == "c":  # Character page
                message = yield self.character(target[1])

        except Exception:
            self.plugin.logger.exception("Error handling URL: {}".format(url))
            returnValue(CASCADE)

        # At this point, if `message` isn't set then we don't understand the
        # url, and so we'll just allow it to pass down to the other handlers

        if message:
            context["event"].target.respond(message)
            returnValue(STOP_HANDLING)
        else:
            returnValue(CASCADE)

    @inlineCallbacks
    def character(self, char_name):
        char_name = urlparse.unquote(char_name)
        ticket = yield self.get_ticket()
        params = {
            "ticket": ticket,
            "name": char_name,
            "account": self.username
        }

        char_info = yield self.post(URL_CHAR_INFO, params=params)
        char_kinks = yield self.post(URL_CHAR_KINKS, params=params)

        char_info = flatten_character(char_info)
        char_kinks = flatten_kinks(char_kinks)

        data = char_info["info"]

        data["sample_kinks"] = {
            "fave": ", ".join(self.get_sample(
                char_kinks["preferences"]["fave"], self.kinks_limit
            )),
            "yes": ", ".join(self.get_sample(
                char_kinks["preferences"]["yes"], self.kinks_limit
            )),
            "maybe": ", ".join(self.get_sample(
                char_kinks["preferences"]["maybe"], self.kinks_limit
            )),
            "no": ", ".join(self.get_sample(
                char_kinks["preferences"]["no"], self.kinks_limit
            )),
        }

        data["given"] = {
            "name": char_name
        }

        returnValue(
            self.get_string("character").format(**data).replace(u"&amp;", u"&")
        )


class FListError(Exception):
    pass
