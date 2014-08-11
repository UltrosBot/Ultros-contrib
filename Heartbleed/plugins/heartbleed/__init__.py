__author__ = 'Gareth Coles'

from . import hb

from system.command_manager import CommandManager
from system.decorators.threads import run_async_threadpool

import system.plugin as plugin


class HeartbleedPlugin(plugin.PluginObject):
    commands = None

    def setup(self):
        self.commands = CommandManager()

        self.commands.register_command("hb",
                                       self.hb_command,
                                       self,
                                       "hb.hb", default=True)

    @run_async_threadpool
    def hb_command(self, protocol, caller, source, command, raw_args,
                   parsed_args):
        args = raw_args.split()  # Quick fix for new command handler signature
        if len(args) < 1:
            caller.respond("Usage: {CHARS}hb <address> [port]")
            return
        else:
            host = args[0]
            port = 443

            if len(args) > 1:
                port = args[1]
                try:
                    port = int(port)
                except:
                    source.respond("Port '%s' is invalid, trying on port "
                                   "443." % port)
            try:
                source.respond("Checking %s:%s" % (host, port))
                result = hb.try_host(host, port)
                if result:
                    source.respond("Host %s is vulnerable!" % host)
                elif result is None:
                    source.respond("Host %s returned an error. It's probably "
                                   "not vulnerable." % host)
                else:
                    source.respond("Host %s is not vulnerable." % host)
            except:
                self.logger.exception("Error querying host %s" % host)
                source.respond("Unable to determine whether host %s is "
                               "vulnerable." % host)
