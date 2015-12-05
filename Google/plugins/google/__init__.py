import treq

from kitchen.text.converters import to_unicode

from plugins.google.search import get_results, parse_results

from system.decorators.threads import run_async_threadpool
from system.plugins.plugin import PluginObject
from system.storage.formats import YAML

__author__ = 'Gareth Coles'
__all__ = ["GooglePlugin"]


class GooglePlugin(PluginObject):
    # TODO: Port to txrequests, update for new URLs plugin
    _config = None

    @property
    def urls(self):
        """
        :rtype: plugins.urls.URLsPlugin
        """

        return self.plugins.get_plugin("urls")

    @property
    def num_results(self):
        """
        :rtype: int
        """

        return self._config["result_limit"] if self._config else None

    def setup(self):
        try:
            self._config = self.storage.get_file(
                self, "config", YAML, "plugins/google.yml"
            )
        except Exception:
            self.logger.exception("Error loading configuration!")
            self.logger.error("Disabling...")
            self._disable_self()
            return
        if not self._config.exists:
            self.logger.warn("Unable to find config/plugins/google.yml")
            self.logger.warn("Defaulting to 4 results per page.")

        self._config.add_callback(self.reload)
        self.reload()

        self.commands.register_command(
            "google", self.google_command, self, "google.google",
            ["g", "search"], True
        )

    def reload(self):
        try:
            self._config.reload()
        except Exception:
            self.logger.exception("Error reloading configuration!")
            return False
        return True

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

        d = get_results(query, page, self.num_results)
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
        results = parse_results(result, self.num_results)

        for title, url in results.iteritems():
            source.respond(u"[{}] {}".format(self.urls.tinyurl(url),
                                             to_unicode(title)))

    def google_json_callback_failed(self, result, protocol, caller, source):
        caller.respond("Failed to parse results: {}".format(result))
