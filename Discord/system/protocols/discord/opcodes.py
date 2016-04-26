# coding=utf-8

__author__ = 'Gareth Coles'

DISPATCH = 0
HEARTBEAT = 1
IDENTIFY = 2
STATUS_UPDATE = 3
VOICE_STATE_UPDATE = 4
VOICE_SERVER_PING = 5
RESUME = 6
RECONNECT = 7
REQUEST_GUILD_MEMBERS = 8
INVALID_SESSION = 9


def get_name(opcode):
    if opcode == DISPATCH:
        return "DISPATCH"
    elif opcode == HEARTBEAT:
        return "HEARTBEAT"
    elif opcode == IDENTIFY:
        return "IDENTIFY"
    elif opcode == STATUS_UPDATE:
        return "STATUS_UPDATE"
    elif opcode == VOICE_STATE_UPDATE:
        return "VOICE_STATE_UPDATE"
    elif opcode == VOICE_SERVER_PING:
        return "VOICE_SERVER_PING"
    elif opcode == RESUME:
        return "RESUME"
    elif opcode == RECONNECT:
        return "RECONNECT"
    elif opcode == REQUEST_GUILD_MEMBERS:
        return "REQUEST_GUILD_MEMBERS"
    elif opcode == INVALID_SESSION:
        return "INVALID_SESSION"
    return "UNKNOWN"
