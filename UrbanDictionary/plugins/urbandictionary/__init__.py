import json
import urllib
import urllib2

from system.command_manager import CommandManager
from system.plugin import PluginObject
from utils.config import Config
from utils.data import Data


__author__ = 'Sean'


class Plugin(PluginObject):

    commands = None
    config = None

    def setup(self):
        ### Grab important shit
        self.commands = CommandManager.instance()

        ### Register commands
        self.commands.register_command("urbandictionary",
                                       self.urbandictionary_cmd,
                                       self,
                                       "urbandictionary.definition")
        # TODO: Replace ud command with urbandictionary alias when implemented
        self.commands.register_command("ud",
                                       self.urbandictionary_cmd,
                                       self,
                                       "urbandictionary.definition")

    def urbandictionary_cmd(self, caller, source, args, protocol):
        ### Get LastFM username to use
        username = None
        if len(args) == 0:
            caller.respond("Usage: {CHARS}urbandictionary <term>")
            return

        term = " ".join(args)

        try:
            definition, permalink = self.get_definition(term)
            if definition is None:
                source.respond('[UD] "%s" is not defined yet')
            else:
                # TODO: Limit definition length
                source.respond('[UD] "%s" - %s - (%s)' %
                               (term,
                                str(definition)
                                .replace('\r', ' ')
                                .replace('\n', ' '),
                                str(permalink)))
        except:
            self.logger.exception("Cannot get definition for '%s'" % term)
            source.respond("There was an error while fetching the definition -"
                           " please try again later, or alert a bot admin.")

    def get_definition(self, term):
        request = urllib2.Request("http://api.urbandictionary.com/v0/define?" +
                                  urllib.urlencode({'term':term}))
        # Fuck you PEP8. Fuck you with the largest, spikiest dragon dildo, in
        # every orifice you have, and more.
        request.add_header('User-agent', 'Mozilla/5.0 '
                                         '(X11; U; Linux i686; '
                                         'en-US; rv:1.9.0.1) '
                                         'Gecko/2008071615 '
                                         'Fedora/3.0.1-1.fc9-1.fc9 '
                                         'Firefox/3.0.1')
        try:
            definition = json.load(urllib2.urlopen(request))["list"][0]
            return definition["definition"], definition["permalink"]
        except IndexError:
            return None, None
