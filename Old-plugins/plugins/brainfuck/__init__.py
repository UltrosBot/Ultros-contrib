__author__ = 'Gareth Coles'

from datetime import datetime

from system.command_manager import CommandManager
from system.plugin import PluginObject
from system.protocols.generic.channel import Channel
from utils.config import Config


class Plugin(PluginObject):

    commands = None
    config = None
    timeout = 100

    def setup(self):
        self.commands = CommandManager.instance()

        try:
            self.config = Config("plugins/brainfuck.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            self.logger.error("Disabling..")
            self._disable_self()
            return
        if not self.config.exists:
            self.logger.error("Unable to find config/plugins/brainfuck.yml")
            self.logger.error("Disabling..")
            self._disable_self()
            return

        self.timeout = self.config["timeout"]
        self.commands.register_command("bf", self.bf_command, self,
                                       "brainfuck.exec")

    def reload(self):
        try:
            self.config.reload()
        except Exception:
            self.logger.exception("Error reloading configuration!")
            return False
        self.timeout = self.config["timeout"]
        return True

    def bf_command(self, caller, source, args, protocol):
        if len(args) < 1:
            caller.respond("Usage: {CHARS}bf <brainfuck program>")
            return

        start_time = datetime.now()
        ended_early = False
        code = args[0]

        i, j = 0, 0
        l = -1
        loops = [0] * 16
        buf = [0] * 30000
        out = ''
        buf_max = 0
        while j < len(code):
            if (datetime.now() - start_time).microseconds / 1000 \
                    >= self.timeout:
                ended_early = True
                break
            if code[j] == '+':
                buf[i] += 1
            elif code[j] == '-':
                buf[i] -= 1
            elif code[j] == '>':
                i += 1
                buf_max = max(buf_max, i)
            elif code[j] == '<':
                i = abs(i - 1)
            elif code[j] == '[':
                l += 1
                loops[l] = j
            elif code[j] == ']':
                if buf[i] == 0:
                    j += 1
                    loops[l] = 0
                    l -= 1
                    continue
                else:
                    j = loops[l]
            elif code[j] == '.':
                out += chr(buf[i])
            j += 1

        if ended_early:
            if isinstance(source, Channel):
                source.respond("KILLED | %s %s" % (buf[:buf_max], out))
            else:
                caller.respond("KILLED | %s %s" % (buf[:buf_max], out))
        else:
            if isinstance(source, Channel):
                source.respond("RESULT | %s %s" % (buf[:buf_max], out))
            else:
                caller.respond("RESULT | %s %s" % (buf[:buf_max], out))
