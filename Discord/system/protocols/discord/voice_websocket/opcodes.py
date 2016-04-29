# coding=utf-8

__author__ = 'Gareth Coles'


IDENTIFY = 0
SELECT_PROTOCOL = 1
READY = 2
HEARTBEAT = 3
SESSION_DESCRIPTION = 4
SPEAKING = 5


def get_name(opcode):
    if opcode == IDENTIFY:
        return "IDENTIFY"
    elif opcode == SELECT_PROTOCOL:
        return "SELECT_PROTOCOL"
    elif opcode == READY:
        return "READY"
    elif opcode == HEARTBEAT:
        return "HEARTBEAT"
    elif opcode == SESSION_DESCRIPTION:
        return "SESSION_DESCRIPTION"
    elif opcode == SPEAKING:
        return "SPEAKING"
    return "UNKNOWN"
