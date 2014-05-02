# coding=utf-8
__author__ = 'Gareth Coles'

from twilio import TwilioRestException
from twilio.rest import TwilioRestClient

from .contact import Contact
# from .events import SMSReceivedEvent

import system.plugin as plugin

from system.command_manager import CommandManager
from system.event_manager import EventManager
from system.plugin_manager import YamlPluginManagerSingleton
from system.storage.manager import StorageManager
from system.storage.formats import YAML, JSON

from utils.switch import Switch


class TwilioPlugin(plugin.PluginObject):

    config = None
    data = None

    commands = None
    events = None
    plugins = None
    storage = None

    twilio = None
    web = None

    def setup(self):
        self.logger.debug("Entered setup method.")

        self.commands = CommandManager()
        self.events = EventManager()
        self.plugins = YamlPluginManagerSingleton()
        self.storage = StorageManager()

        #: :type: BottlePlugin
        self.web = self.plugins.getPluginByName("Web").plugin_object

        try:
            self.config = self.storage.get_file(self, "config", YAML,
                                                "plugins/twilio.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            return self._disable_self()
        else:
            if not self.config.exists:
                self.logger.error("Unable to find config/plugins/twilio.yml")
                return self._disable_self()

        try:
            self.data = self.storage.get_file(self, "data", JSON,
                                              "plugins/twilio/contacts.json")
        except Exception:
            self.logger.exception("Error loading data!")
            self.logger.error("This data file is required. Shutting down...")
            return self._disable_self()

        self.twilio = TwilioRestClient(
            self.config["identification"]["sid"],
            self.config["identification"]["token"]
        )

        account = self.twilio.accounts.get(
            self.config["identification"]["sid"]
        )

        self.logger.info("Logged in as [%s] %s." % (account.type,
                                                    account.friendly_name))

        self.events.add_callback("Web/ServerStartedEvent", self,
                                 self.add_routes,
                                 0)

        self.commands.register_command("sms", self.sms_command, self,
                                       "twilio.sms")
        self.commands.register_command("mms", self.mms_command, self,
                                       "twilio.mms")
        self.commands.register_command("tw", self.tw_command, self,
                                       "twilio.tw")

    def add_routes(self, event):
        self.web.add_route("/twilio/%s" % self.config["security"]["api_key"],
                           ["POST"], self.route)
        self.logger.info("Registered route: /twilio/%s"
                         % self.config["security"]["api_key"], )

    def tw_command(self, protocol, caller, source, command, raw_args,
                   parsed_args):

        args = raw_args.split(" ")
        if len(args) < 3:
            caller.respond("Usage: {CHARS}tw contact <set/del/get> "
                           "<[name] [number]>")
            return

        action = args[0].lower()
        operation = args[1].lower()
        target = args[2]

        if action != "contact":
            caller.respond("Unknown action: %s" % action)
            return

        for case in Switch(operation):  # I was bored, okay?
            if case("set"):
                if len(args) < 4:
                    caller.respond("Usage: {CHARS}tw contact set <name>"
                                   " <number>")
                    break
                try:
                    self.save_contact(name=target, number=args[3])
                except Exception as e:
                    source.respond("Error saving contact: %s" % e)
                else:
                    source.respond("Contact '%s' saved." % target)

                break
            if case("del"):
                try:
                    if target.startswith("+"):
                        c = self.load_contact(number=target)
                    else:
                        c = self.load_contact(name=target)

                    if not c:
                        source.respond("No contact found for '%s'" % target)
                        return

                    r = self.del_contact(contac_=c)

                    if not r:
                        source.respond("No contact found for '%s'" % target)
                    else:
                        source.respond("Contact for '%s' deleted." % target)
                except Exception as e:
                    source.respond("Error deleting contact: %s" % e)

                break
            if case("get"):
                try:
                    if target.startswith("+"):
                        c = self.load_contact(number=target)
                    else:
                        c = self.load_contact(name=target)

                    if not c:
                        source.respond("No contact found for '%s'" % target)
                    else:
                        source.respond("CONTACT | %s -> %s" % (c.name,
                                                               c.number))
                except Exception as e:
                    source.respond("Error loading contact: %s" % e)

                break
            if case():
                caller.respond("Unknown operation: %s" % operation)

    def sms_command(self, protocol, caller, source, command, raw_args,
                    parsed_args):
        args = raw_args.split(" ")
        if len(args) < 2:
            caller.respond("Usage: {CHARS}sms <name/number> <message>")
            return

        sent = self.config["formatting"].get("sms-sent",
                                             "SMS | {TO} | Message sent.")
        error = self.config["formatting"].get("sms-error",
                                              "SMS | ERROR | {ERROR}")

        target = args[0]
        message = "<%s> %s" % (caller.nickname, " ".join(args[1:]))

        if target.startswith("+"):
            c = self.load_contact(number=target)
        else:
            c = self.load_contact(name=target)

        if c is None:
            name = target
            if not target.startswith("+"):
                source.respond(
                    error.replace(
                        "{ERROR}",
                        "Numbers must start with a '+'"
                    )
                )
                return

            sent = sent.replace("{TO}", name)

            try:
                self.send_sms(name, message)
            except TwilioRestException as e:
                source.respond(
                    error.replace(
                        "{ERROR}",
                        str(e.msg)
                    )
                )
            except Exception as e:
                source.respond(
                    error.replace(
                        "{ERROR}",
                        str(e)
                    )
                )
            else:
                source.respond(sent)
        else:
            name = c.name
            sent = sent.replace("{TO}", name)

            try:
                self.send_sms(c, message)
            except TwilioRestException as e:
                source.respond(
                    error.replace(
                        "{ERROR}",
                        str(e.msg)
                    )
                )
            except Exception as e:
                source.respond(
                    error.replace(
                        "{ERROR}",
                        str(e)
                    )
                )
            else:
                source.respond(sent)

    def mms_command(self, protocol, caller, source, command, raw_args,
                    parsed_args):
        args = raw_args.split(" ")
        if len(args) < 3:
            caller.respond("Usage: {CHARS}mms <name/number> <url> <message>")
            return

        sent = self.config["formatting"].get("mms-sent",
                                             "MMS | {TO} | Message sent.")
        error = self.config["formatting"].get("mms-error",
                                              "MMS | ERROR | {ERROR}")

        target = args[0]
        url = args[1]
        message = "<%s> %s" % (caller.nickname, " ".join(args[2:]))

        if target.startswith("+"):
            c = self.load_contact(number=target)
        else:
            c = self.load_contact(name=target)

        if c is None:
            name = target
            if not target.startswith("+"):
                source.respond(
                    error.replace(
                        "{ERROR}",
                        "Numbers must start with a '+'"
                    )
                )
                return

            sent = sent.replace("{TO}", name)

            try:
                self.send_sms(name, message, media_url=url)
            except TwilioRestException as e:
                source.respond(
                    error.replace(
                        "{ERROR}",
                        str(e.msg)
                    )
                )
            except Exception as e:
                source.respond(
                    error.replace(
                        "{ERROR}",
                        str(e)
                    )
                )
            else:
                source.respond(sent)
        else:
            name = c.name
            sent = sent.replace("{TO}", name)

            try:
                self.send_sms(c, message, media_url=url)
            except TwilioRestException as e:
                source.respond(
                    error.replace(
                        "{ERROR}",
                        str(e.msg)
                    )
                )
            except Exception as e:
                source.respond(
                    error.replace(
                        "{ERROR}",
                        str(e)
                    )
                )
            else:
                source.respond(sent)

    def do_targets(self, sender, message):
        c = self.load_contact(number=sender)
        name = "default"

        if c is not None:
            name = c.name

        if name not in self.config["targetting"]:
            name = "default"

            if name not in self.config["targetting"]:
                self.logger.debug("No default target found.")
                return

        targets = self.config["targetting"][name]

        f_str = self.config["formatting"].get(
            "sms",
            "SMS | {FROM} | {MESSAGE}"
        )

        from_ = name
        if from_ == "default":
            from_ = sender

        message = message.replace("\r", "")
        message = message.replace("\n", " ")

        f_str = f_str.replace("{FROM}", from_)
        f_str = f_str.replace("{MESSAGE}", message)

        self.logger.info(f_str)

        for target in targets:
            try:
                p_str = target["protocol"]
                p = self.factory_manager.get_protocol(p_str)

                if p is None:
                    self.logger.warn("No such protocol: %s" % p_str)
                    continue

                p.send_msg(target["target"], f_str,
                           target_type=target["target-type"])
            except Exception:
                self.logger.exception("Error relaying SMS message")
                continue

    def send_sms(self, target, message, media_url=None):
        if isinstance(target, Contact):
            target = target.number

        msg = self.twilio.messages.create(
            body=message, to=target,
            from_=self.config["identification"]["number"],
            media_url=media_url)

        return msg

    def load_contact(self, contac_=None, name=None, number=None):
        if contac_ is not None:
            return contac_

        if name is not None:
            number = self.data.get(name, None)
            if number is not None:
                return Contact(number, name, self)

        if number is not None:
            for k in self.data.keys():
                if number == self.data[k]:
                    return Contact(number, k, self)

        return None

    def save_contact(self, contac_=None, name=None, number=None):
        if contac_ is not None:
            with self.data:
                self.data[contac_.name] = contac_.number
            return contac_
        elif name is not None and number is not None:
            contac_ = Contact(number, name, self)
            with self.data:
                self.data[contac_.name] = contac_.number
            return contac_

        raise ValueError("You need to give either a contact, or a name and "
                         "number to save.")

    def del_contact(self, contac_=None, name=None, number=None):
        if contac_ is not None:
            with self.data:
                if contac_.name in self.data:
                    del self.data[contac_.name]
                    return True
                return False

        elif name is not None:
            with self.data:
                if name in self.data:
                    del self.data[name]
                    return True
                return False

        elif number is not None:
            for k in self.data.keys():
                if number == self.data[k]:
                    del self.data[k]
                    return True
            return False

        raise ValueError("You need to give either a contact, name or "
                         "number to delete.")

    def route(self):
        r = self.web.get_objects()
        request = r.request
        response = r.response

        from_ = request.forms.From
        message = request.forms.Body

        if not (len(from_) and len(message)):
            return r.abort(400, "No data!")

        response.content_type = "text/xml"

        try:
            self.do_targets(from_, message)
        except Exception:
            self.logger.exception("Error in SMS message handler!")
        finally:
            return "<Response></Response>"

    pass  # So the regions work in PyCharm
