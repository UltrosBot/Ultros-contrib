__author__ = 'Gareth Coles'

import datetime

from system.protocols.generic.user import User as BaseUser
from system.translations import Translations
_ = Translations().get()


class User(BaseUser):

    # {
    #     u'status': 3,
    #     u'username': u'Julu',
    #     u'language': u'en',
    #     u'gRole': None,
    #     u'level': 8,
    #     u'avatarID': u'2014hw02',
    #     u'joined': u'2013-10-20 15:25:17.010000',
    #     u'priority': 2,
    #     u'uIndex': None,
    #     u'role': 4,
    #     u'vote': 1,
    #     u'grab': False,
    #     u'badge': 2,
    #     u'id': 3959272,
    #     u'friend': False,
    #     u'_position': {
    #         u'c': 83,
    #         u'r': 19
    #     }
    # }

    authorized = False
    auth_name = ""

    status = -1  # Available/Gaming/Away
    username = ""  # User's username
    language = ""  # User's language
    gRole = None  # Admin/brand ambassador?
    level = 0  # XP level
    avatarID = ""  # Avatar ID
    joined = None  # Sign-up date
    priority = 0  # ???
    uIndex = None  # ???
    role = 0  # Room staff level
    vote = 0  # Wooted/Meh'd
    grab = False  # Grabbed
    badge = 0  # Early adopter/beta tester badges
    id = 0000000  # User ID
    friend = False  # Whether they're our friend
    position = {  # ???
        "c": 0,
        "r": 0
    }

    @property
    def nickname(self):
        return self.username

    @property
    def waitlist_position(self):
        return self.protocol.call_api("getWaitListPosition", self.id)

    def __init__(self, username, protocol=None, is_tracked=False):
        self.username = username
        self.protocol = protocol
        self.is_tracked = is_tracked

    def update_info(self, user_object):
        self.status = user_object.get("status", 0)
        self.username = user_object.get("username", "")
        self.language = user_object.get("language", "")
        self.gRole = user_object.get("gRole", None)
        self.level = user_object.get("level", 0)
        self.avatarID = user_object.get("avatarID", "")
        self.joined = datetime.datetime.strptime(
            user_object.get(
                "joined",
                "1970-01-01 00:00:00.000000"
            ),
            "%Y-%m-%d %H:%M:%S.%f"
        )
        self.priority = user_object.get("priority", 0)
        self.uIndex = user_object.get("uIndex", None)
        self.role = user_object.get("role", 0)
        self.vote = user_object.get("vote", 0)
        self.grab = user_object.get("grab", False)
        self.badge = user_object.get("badge", 0)
        self.id = user_object.get("id", 0)
        self.friend = user_object.get("friend", False)
        self.position = user_object.get("_position", {
            "c": 0,
            "r": 0
        })

    def respond(self, message):
        return self.protocol.send_msg(self, message)

    # region Plug-specific stuff

    @property
    def did_woot(self):
        return self.vote == 1

    @property
    def did_meh(self):
        return self.vote == -1

    # endregion

    # region permissions

    def can_kick(self, user, channel=None):
        """
        Whether or not this User can kick "user" from "channel". If unsure,
        this should return False. The calling code can always attempt a kick
        anyway if they so wish.
        """
        return False

    def can_ban(self, user, channel=None):
        """
        Whether or not this User can ban "user" from "channel". If unsure, this
        should return False. The calling code can always attempt a kick anyway
        if they so wish.
        """
        return False

    # endregion

    def __str__(self):
        return self.name
