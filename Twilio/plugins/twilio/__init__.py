# coding=utf-8
__author__ = 'Gareth Coles'

from twilio import TwilioRestException
from twilio.rest import TwilioRestClient

from plugins.twilio.contact import Contact

from system.plugins.plugin import PluginObject
from system.storage.formats import YAML, JSON

from utils.switch import Switch as switch


class TwilioPlugin(PluginObject):
    # TODO: Rewrite and test
    # I'm not convinced this actually works anymore, and it
    # probably needs a rewrite to properly support Web

    config = None
    data = None
    twilio = None

    @property
    def web(self):
        """
        :rtype: WebPlugin
        """
        return self.plugins.get_plugin("Web")

    def setup(self):
        self.logger.trace("Entered setup method.")

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

        self._load()
        self.config.add_callback(self._load)

        self.events.add_callback("Web/ServerStartedEvent", self,
                                 self.add_routes,
                                 0)

        self.commands.register_command("sms", self.sms_command, self,
                                       "twilio.sms")
        self.commands.register_command("mms", self.mms_command, self,
                                       "twilio.mms")
        self.commands.register_command("tw", self.tw_command, self,
                                       "twilio.tw")

    def _load(self):
        self.twilio = TwilioRestClient(
            self.config["identification"]["sid"],
            self.config["identification"]["token"]
        )

        account = self.twilio.accounts.get(
            self.config["identification"]["sid"]
        )

        self.logger.info("Logged in as [%s] %s." % (account.type,
                                                    account.friendly_name))

    def add_routes(self, event):
        self.web.add_handler(
            r"/twilio/%s" % self.config["security"]["api_key"],
            "plugins.twilio.route.Route"
        )
        self.logger.info("Registered route: /twilio/<apikey>")

    def tw_command(self, protocol, caller, source, command, raw_args,
                   parsed_args):

        args = raw_args.split(" ")
        if len(args) < 1:
            caller.respond("Usage: {CHARS}tw <contact/reload> [<set/del/get> "
                           "<[name] [number]>]")
            return

        action = args[0].lower()

        if action == "reload":
            self.config.reload()
            self.data.reload()

            source.respond("Files reloaded.")
            return

        if action != "contact":
            caller.respond("Unknown action: %s" % action)
            return

        if len(args) < 3:
            caller.respond("Usage: {CHARS}tw contact <set/del/get> "
                           "<[name] [number]>")
            return

        operation = args[1].lower()
        target = args[2]

        for case, default in switch(operation):  # I was bored, okay?
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
            if default:
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
                if "has not been enabled for MMS" in e.msg:
                    e.msg = "Twilio number has not been enabled for MMS."
                elif "Please use only valid http and https urls" in e.msg:
                    e.msg = "Media URL is invalid - please use a link to a " \
                            "media file."
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
                        str(e).replace(
                            "\r", ""
                        ).replace(
                            "\n", " "
                        ).replace(
                            "  ", " "
                        )
                    )
                )
                self.logger.exception("Error sending SMS")
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
                if "has not been enabled for MMS" in e.msg:
                    e.msg = "Twilio number has not been enabled for MMS."
                elif "Please use only valid http and https urls" in e.msg:
                    e.msg = "Media URL is invalid - please use a link to a " \
                            "media file."
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
                        str(e).replace(
                            "\r", ""
                        ).replace(
                            "\n", " "
                        ).replace(
                            "  ", " "
                        )
                    )
                )
                self.logger.exception("Error sending MMS")
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
        sender = str(sender).strip()
        c = self.load_contact(number=sender)
        name = "default"

        if c is not None:
            name = c.name

        if name not in self.config["targetting"]:
            name = "default"

            if name not in self.config["targetting"]:
                self.logger.trace("No default target found.")
                return

        targets = self.config["targetting"][name]

        f_str = self.config["formatting"].get(
            "sms",
            "SMS | {FROM} | {MESSAGE}"
        )

        from_ = name

        if c is not None:
            from_ = c.name
        elif from_ == "default":
            from_ = sender

        message = str(message).replace("\r", "")
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

    pass  # So the regions work in PyCharm
