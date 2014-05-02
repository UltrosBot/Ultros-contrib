__author__ = 'Gareth Coles'


class Contact(object):
    """
    This is a Twilio contact. It's an abstraction so that we can have
    easy response commands and stuff.
    """

    _number = ""
    name = ""
    plugin = ""

    def __init__(self, number, name, plugin):
        """
        :type plugin: TwilioPlugin
        """
        self.name = name
        self.plugin = plugin

        self.set_number(number)

    @property
    def number(self):
        return self._number

    def set_number(self, number):
        if number.startswith("00"):
            number = "+" + number[2:]

        if not number.startswith("+"):
            raise ValueError("Number must start with a +")

        self._number = number

    def send_message(self, message, media_url=None):
        self.plugin.send_sms(self, message, media_url)
