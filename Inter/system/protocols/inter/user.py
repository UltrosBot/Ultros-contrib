__author__ = 'Gareth Coles'

from system.protocols.generic.user import User as BaseUser
from system.translations import Translations
_ = Translations().get()


class User(BaseUser):

    server = ""

    def respond(self, message):
        self.protocol.send_msg("%s: %s" % (self.name, message))

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, User):
            return self.name == other.name
        return False

    def __ne__(self, other):
        if isinstance(other, User):
            return self.name != other.name
        return True
