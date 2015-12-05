import random
import re
import itertools

from system.events.general import MessageReceived, ActionReceived
from system.plugins.plugin import PluginObject
from system.protocols.generic.channel import Channel
from system.storage.formats import YAML


__author__ = 'Sean'
__all__ = ["TriggersPlugin"]


class TriggersPlugin(PluginObject):
    _config = None

    def setup(self):

        # Initial config load
        try:
            self._config = self.storage.get_file(
                    self, "config", YAML, "plugins/triggers.yml"
            )
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

        # Register event handlers
        def _message_event_filter(event=MessageReceived):
            return isinstance(event.target, Channel)

        self.events.add_callback("MessageReceived",
                                 self,
                                 self.message_handler,
                                 1,
                                 _message_event_filter)

        self.events.add_callback("ActionReceived",
                                 self,
                                 self.action_handler,
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
        self.event_handler(
            event.caller,
            event.source,
            event.target,
            event.message,
            event.type
        )

    def action_handler(self, event=ActionReceived):
        self.event_handler(
            event.caller,
            event.source,
            event.target,
            event.message,
            "action"
        )

    def event_handler(self, protocol, source, target, message, e_type):
        """
        Event handler for general messages
        """

        allowed = self.commands.perm_handler.check(
                "triggers.trigger", source, target, protocol
        )
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
                trigger_types = trigger.get("trigger_types", {"message": True})
                response_type = trigger.get("response_type", "message")
                permission = trigger.get("permission", None)

                if not trigger_types.get(e_type, False):
                    continue

                if random.random() * 100 >= chance:
                    continue

                if permission is not None:
                    _full_perm = "triggers.trigger." + permission
                    self.logger.debug("Checking for permission: {0}",
                                      _full_perm)
                    if not self.commands.perm_handler.check(_full_perm, source,
                                                            target, protocol):
                        continue

                response = random.choice(responses)
                if isinstance(response, dict):
                    response_type = response.get("type", response_type)
                    response = response["response"]
                response_type = response_type.lower()

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
                        self.logger.warning("Unknown regex flag '%s'" % flag)

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
                    if response_type == "message":
                        protocol.send_msg(target, response_formatted)
                    elif response_type == "action":
                        protocol.send_action(target, response_formatted)
                    elif response_type == "notice":
                        if hasattr(protocol, "send_notice"):
                            protocol.send_notice(target, response_formatted)
                        else:
                            self.logger.error(
                                "Cannot respond with notice on protocol: '%s'"
                                % protocol.name
                            )
                    elif response_type == "channel_kick":
                        attempted = protocol.channel_kick(
                            source,
                            channel=_channel,
                            reason=response_formatted
                        )
                        if not attempted:
                            self.logger.warning(
                                "Couldn't kick %s from %s" % (
                                    source,
                                    _channel
                                )
                            )
                    elif response_type == "channel_ban":
                        attempted = protocol.channel_ban(
                            source,
                            channel=_channel,
                            reason=response_formatted
                        )
                        if not attempted:
                            self.logger.warning(
                                "Couldn't ban %s from %s" % (
                                    source,
                                    _channel
                                )
                            )
                    elif response_type == "global_kick":
                        attempted = protocol.global_kick(
                            source,
                            reason=response_formatted
                        )
                        if not attempted:
                            self.logger.warning(
                                "Couldn't global kick %s" % source
                            )
                    elif response_type == "global_ban":
                        attempted = protocol.global_ban(
                            source,
                            reason=response_formatted
                        )
                        if not attempted:
                            self.logger.warning(
                                "Couldn't global ban %s" % source
                            )
                    else:
                        self.logger.error(
                            "Invalid response_type '%s'" % response_type
                        )
            except Exception:
                self.logger.exception(
                    "Invalid trigger for channel '%s' in protocol  '%s'" %
                    (
                        _channel,
                        protocol.name
                    )
                )
