import json
import urllib
import urllib2

from kitchen.text.converters import to_bytes

from system.plugins.plugin import PluginObject

__author__ = 'Sean'
__all__ = ["UrbanDictionaryPlugin"]


class UrbanDictionaryPlugin(PluginObject):
    # TODO: urllib/2 -> txrequests

    config = None

    def setup(self):
        # Register commands
        self.commands.register_command("urbandictionary",
                                       self.urbandictionary_cmd,
                                       self,
                                       "urbandictionary.definition",
                                       aliases=["ud"], default=True)

    def urbandictionary_cmd(self, protocol, caller, source, command, raw_args,
                            parsed_args):
        args = raw_args.split()  # Quick fix for new command handler signature

        if len(args) == 0:
            caller.respond("Usage: {CHARS}urbandictionary <term>")
            return

        term = " ".join(args)

        try:
            definition, permalink = self.get_definition(term)
            if definition is None:
                source.respond('[UD] "%s" is not defined yet' % term)
            else:
                # TODO: Limit definition length
                source.respond('[UD] "%s" - %s - (%s)' %
                               (term,
                                to_bytes(definition)
                                .replace('\r', '')
                                .replace('\n', ' '),
                                to_bytes(permalink)))
        except Exception:
            self.logger.exception("Cannot get definition for '%s'" % term)
            source.respond("There was an error while fetching the definition -"
                           " please try again later, or alert a bot admin.")

    def get_definition(self, term):
        request = urllib2.Request("http://api.urbandictionary.com/v0/define?" +
                                  urllib.urlencode({'term': term}))

        request.add_header(
            'User-agent', 'Mozilla/5.0 (X11; U; Linux i686; '
                          'en-US; rv:1.9.0.1) Gecko/2008071615 '
                          'Fedora/3.0.1-1.fc9-1.fc9 Firefox/3.0.1'
        )
        try:
            definition = json.load(urllib2.urlopen(request))["list"][0]
            return definition["definition"], definition["permalink"]
        except IndexError:
            return None, None
