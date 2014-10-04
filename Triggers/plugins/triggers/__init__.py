import random
import re
import itertools

from system.command_manager import CommandManager
from system.event_manager import EventManager
from system.events.general import MessageReceived

import system.plugin as plugin
from system.protocols.generic.channel import Channel

from system.storage.formats import YAML
from system.storage.manager import StorageManager


__author__ = 'Sean'


class TriggersPlugin(plugin.PluginObject):

    commands = None
    events = None
    storage = None

    _config = None

    def setup(self):
        ### Grab important shit
        self.commands = CommandManager()
        self.events = EventManager()
        self.storage = StorageManager()

        ### Initial config load
        try:
            self._config = self.storage.get_file(self,
                                                 "config",
                                                 YAML,
                                                 "plugins/triggers.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            self.logger.error("Disabling...")
            self._disable_self()
            return
        if not self._config.exists:
            self.logger.error("Unable to find config/plugins/triggers.yml")
            self.logger.error("Disabling...")
            self._disable_self()
            return

        ### Register event handlers
        def _message_event_filter(event=MessageReceived):
            target = event.target
            type_ = event.type

            return isinstance(target, Channel)

        self.events.add_callback("MessageReceived",
                                 self,
                                 self.message_handler,
                                 1,
                                 _message_event_filter)

    def reload(self):
        try:
            self._config.reload()
        except Exception:
            self.logger.exception("Error reloading configuration!")
            return False
        return True

    @property
    def _triggers(self):
        return self._config.get("triggers", {})

    def message_handler(self, event=MessageReceived):
        """
        Event handler for general messages
        """

        protocol = event.caller
        source = event.source
        target = event.target
        message = event.message

        allowed = self.commands.perm_handler.check("triggers.trigger",
                                                   source,
                                                   target,
                                                   protocol)
        if not allowed:
            return

        # TODO: Rewrite this when Matcher is finished

        # TODO: We check the types of half of these - do the rest

        global_triggers = self._triggers.get("global", [])
        proto_trigger_block = self._triggers.get("protocols", {})

        proto_triggers = proto_trigger_block.get(protocol.name, {})
        if not isinstance(proto_triggers, dict):
            self.logger.error(
                "Invalid triggers for protocol '%s'" % protocol.name
            )
            return

        proto_triggers_global = proto_triggers.get("global", [])
        channel_triggers_block = proto_triggers.get("channels", {})

        channel_triggers = []
        _channel = None

        for _channel, _triggers in channel_triggers_block.iteritems():
            if protocol.get_channel(_channel) == target:
                channel_triggers = _triggers
                break

        if not isinstance(channel_triggers, list):
            self.logger.error(
                "Invalid triggers for channel '%s' in protocol  '%s'" %
                (
                    _channel,
                    protocol.name
                )
            )
            return

        for trigger in itertools.chain(channel_triggers,
                                       proto_triggers_global,
                                       global_triggers):
            try:
                trigger_regex = trigger["trigger"]
                responses = trigger["response"]
                chance = trigger.get("chance", 100)
                flags = trigger.get("flags", "")

                response = random.choice(responses)

                if random.random() * 100 >= chance:
                    continue

                flags_parsed = 0

                for flag in flags.lower():
                    if flag == "i":
                        flags_parsed += re.I
                    elif flag == "u":
                        flags_parsed += re.U
                    elif flag == "l":
                        flags_parsed += re.L
                    elif flag == "m":
                        flags_parsed += re.M
                    elif flag == "x":
                        flags_parsed += re.X
                    elif flag == "s":
                        flags_parsed += re.S
                    elif flag == "d":
                        flags_parsed += re.DEBUG
                    else:
                        self.log.warning("Unknown regex flag '%s'" % flag)

                # TODO: Rate limiting
                # re caches compiled patterns internally, so we don't have to
                match = re.search(trigger_regex, message, flags_parsed)
                if match:
                    # Hack to get around the fact that regex groups start at
                    # one, but formatting args start at 0
                    format_args = [""]
                    format_args.extend(match.groups())
                    format_kwargs = {}
                    for k, v in match.groupdict().iteritems():
                        format_kwargs[k] = v
                    format_kwargs["channel"] = _channel
                    format_kwargs["source"] = source
                    format_kwargs["target"] = target
                    format_kwargs["message"] = message
                    format_kwargs["protocol"] = protocol.name
                    response_formatted = response.format(
                        *format_args,
                        **format_kwargs
                    )
                    target.respond(response_formatted)
            except Exception:
                self.logger.exception(
                    "Invalid trigger for channel '%s' in protocol  '%s'" %
                    (
                        _channel,
                        protocol.name
                    )
                )
