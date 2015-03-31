__author__ = 'Gareth Coles'

import treq
import system.plugin as plugin

from system.decorators.threads import run_async_threadpool

from kitchen.text.converters import to_unicode
from search import get_results, parse_results


class GooglePlugin(plugin.PluginObject):
    @property
    def urls(self):
        """
        :rtype: plugins.urls.URLsPlugin
        """

        return self.plugins.get_plugin("urls")

    def setup(self):
        self.commands.register_command(
            "google", self.google_command, self, "google.google",
            ["g", "search"], True
        )

    def google_command(self, protocol, caller, source, command, raw_args,
                       parsed_args):
        if len(parsed_args) < 1:
            caller.respond("Usage: {CHARS}%s [:page] <query>" % command)

        page = 0
        query = raw_args

        if len(parsed_args) > 1:
            if parsed_args[0].startswith(":"):
                try:
                    page = int(parsed_args[0][1:]) - 1
                except Exception:
                    pass
                else:
                    query = " ".join(raw_args.split(" ")[1:])

        d = get_results(query, page)
        d.addCallback(self.google_response_callback, protocol, caller, source)
        d.addErrback(self.google_response_callback_failed, protocol, caller,
                     source)

    def google_response_callback(self, result, protocol, caller, source):
        d = treq.json_content(result)
        d.addCallback(self.google_json_callback, protocol, caller, source)
        d.addErrback(self.google_json_callback_failed, protocol, caller,
                     source)

    def google_response_callback_failed(self, result, protocol, caller,
                                        source):
        caller.respond("Failed to get results: {}".format(result))

    @run_async_threadpool
    def google_json_callback(self, result, protocol, caller, source):
        results = parse_results(result)

        for title, url in results.iteritems():
            source.respond(u"[{}] {}".format(self.urls.tinyurl(url),
                                             to_unicode(title)))

    def google_json_callback_failed(self, result, protocol, caller, source):
        caller.respond("Failed to parse results: {}".format(result))
