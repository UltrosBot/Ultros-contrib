# coding=utf-8

__author__ = 'Gareth Coles'

# Constants first

# Allows creating of instant invites
CREATE_INSTANT_INVITE = 0x0000001

# Allows kicking members
KICK_MEMBERS = 0x0000002

# Allows banning members
BAN_MEMBERS = 0x0000004

# Allows management and editing of roles
MANAGE_ROLES = 0x0000008

# Allows management and editing of channels
MANAGE_CHANNELS = 0x0000010

# Allows management and editing of the guild
MANAGE_GUILD = 0x0000020

# Allows reading messages in a channel. The channel will not appear for users
# without this permission
READ_MESSAGES = 0x0000400

# Allows for sending messages in a channel.
SEND_MESSAGES = 0x0000800

# Allows for sending of /tts messages
SEND_TTS_MESSAGES = 0x0001000

# Allows for deleting messages
MANAGE_MESSAGES = 0x0002000

# Links sent by this user will be auto-embedded
EMBED_LINKS = 0x0004000

# Allows for uploading images and files
ATTACH_FILES = 0x0008000

# Allows for reading messages history
READ_MESSAGE_HISTORY = 0x0010000

# Allows for using the @everyone tag to notify all users in a channel
MENTION_EVERYONE = 0x0020000

# Allows for joining of a voice channel
CONNECT = 0x0100000

# Allows for speaking in a voice channel
SPEAK = 0x0200000

# Allows for muting members in a voice channel
MUTE_MEMBERS = 0x0400000

# Allows for deafening of members in a voice channel
DEAFEN_MEMBERS = 0x0800000

# Allows for moving of members between voice channels
MOVE_MEMBERS = 0x1000000

# Allows for using voice-activity-detection in a voice channel
USE_VAD = 0x2000000

# Allows for modification of own nickname
CHANGE_NICKNAME = 0x4000000

# Allows for modification of other users nicknames
MANAGE_NICKNAMES = 0x8000000


permissions = {
    "create instant invite": CREATE_INSTANT_INVITE,
    "kick members": KICK_MEMBERS,
    "ban members": BAN_MEMBERS,
    "manage roles": MANAGE_ROLES,
    "manage channels": MANAGE_CHANNELS,
    "manage guild": MANAGE_GUILD,
    "read messages": READ_MESSAGES,
    "send messages": SEND_MESSAGES,
    "send tts messages": SEND_TTS_MESSAGES,
    "manage messages": MANAGE_MESSAGES,
    "embed links": EMBED_LINKS,
    "attach files": ATTACH_FILES,
    "read message history": READ_MESSAGE_HISTORY,
    "mention everyone": MENTION_EVERYONE,
    "connect": CONNECT,
    "speak": SPEAK,
    "mute U": MUTE_MEMBERS,
    "deafen members": DEAFEN_MEMBERS,
    "move members": MOVE_MEMBERS,
    "use vad": USE_VAD,
    "change nickname": CHANGE_NICKNAME,
    "manage nicknames": MANAGE_NICKNAMES
}


def get_permissions(integer):
    found = []

    for k, v in permissions.items():
        if integer & v:
            found.append(k)

    return found


def to_integer(*perms):
    done = 0

    for perm in perms:
        if isinstance(perm, basestring):
            perm = permissions[perm]

        done |= perm

    return done


def to_names(*perms):
    found = []

    for k, v in permissions:
        if v in perms:
            found.append(k)

    return found


def from_names(*perms):
    return [permissions[k] for k in perms]


def has_perm(integer, perm):
    if isinstance(perm, basestring):
        perm = permissions[perm]
    return integer & perm
