__author__ = 'Gareth Coles'

from plugins.web.request_handler import RequestHandler


class Route(RequestHandler):

    #: :type: TwilioPlugin
    twilio = None

    def initialize(self):
        self.twilio = self.plugin.factory_manager.plugman.get_plugin("Twilio")

    def get(self):
        from_ = self.get_argument("From", default="")
        message = self.get_argument("Body", default="")

        if not (len(from_) and len(message)):
            return self.send_error(400)

        self.set_header("Content-Type", "text/xml")

        try:
            self.twilio.do_targets(from_, message)
        except Exception:
            self.twilio.logger.exception("Error in SMS message handler!")
        finally:
            self.finish("<Response></Response>")
