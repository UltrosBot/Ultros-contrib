__author__ = "Gareth Coles"

import requests

import system.plugin as plugin
from system.plugins.manager import PluginManager

HASTEBIN_URL = "http://hastebin.com/documents"


class AntiMibbitPlugin(plugin.PluginObject):

    plugs = None

    @property
    def urls(self):
        """
        :rtype: URLsPlugin
        """
        return self.plugs.get_plugin("URLs")

    def setup(self):
        self.plugs = PluginManager()

        self.urls.add_handler("miburl.com", self.miburl_handler)
        self.urls.add_handler("mibpaste.com", self.mibpaste_handler)

    def hastebin(self, data):
        key = requests.post(HASTEBIN_URL, data).json()["key"]
        return "http://hastebin.com/%s" % key

    def miburl_handler(self, url):
        response = requests.get(url)
        return "Re-shortened: %s - Don't use Mibbit for URL shortening!" \
               % self.urls.tinyurl(response.url)

    def mibpaste_handler(self, url):
        response = requests.get(url)
        #: :type: str
        content = response.text

        body_start = content.find("<body>") + 9  # Tabs? Really?
        last_hr = content.rfind("<hr>") - 1

        to_paste = content[body_start:last_hr]
        to_paste = to_paste.replace("<br/>", "")
        to_paste = to_paste.replace("<br />", "")
        to_paste = to_paste.strip("\n").strip(" ")

        hb_url = self.hastebin(to_paste)

        return "Re-pasted: %s - Don't use Mibbit as a pastebin!" \
               % hb_url
