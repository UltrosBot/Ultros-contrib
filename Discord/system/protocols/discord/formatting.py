# coding=utf-8
import re


__author__ = 'Gareth Coles'

USER_MENTION_REGEX = re.compile(ur"^<@([\d]+)>$")
USER_NICK_MENTION_REGEX = re.compile(ur"^<@!([\d]+)>$")
CHANNEL_MENTION_REGEX = re.compile(ur"^<#([\d]+)>$")
ROLE_MENTION_REGEX = re.compile(ur"^<@&([\d]+)>$")

USER_REVERSE_REGEX = re.compile(ur"^@(.*#[\d]{4})$")
CHANNEL_REVERSE_REGEX = re.compile(ur"^#(.*#[\d]{4})$")
ROLE_REVERSE_REGEX = re.compile(ur"^@(.*)$")


def translate_mentions_from_server(guild, message):
    words = []

    for word in message.split(u" "):
        user_match = re.match(USER_MENTION_REGEX, word)
        nickname_match = re.match(USER_NICK_MENTION_REGEX, word)
        channel_match = re.match(CHANNEL_MENTION_REGEX, word)
        role_match = re.match(ROLE_MENTION_REGEX, word)

        if user_match:
            user = guild.get_user(int(user_match.group(0)))

            if user:
                words.append(user.username)
            else:
                words.append(word)
            continue

        if nickname_match:
            user = guild.get_user(int(nickname_match.group(0)))

            if user:
                words.append(user.nickname)
            else:
                words.append(word)
            continue

        if channel_match:
            channel = guild.get_channel(int(channel_match.group(0)))

            if channel:
                words.append(channel.name)
            else:
                words.append(word)
            continue

        if role_match:
            role = guild.get_role(int(role_match.group(0)))

            if role:
                words.append(role.name)
            else:
                words.append(word)
            continue

        words.append(word)

    return u" ".join(words)


def translate_mentions_to_server(guild, message):
    words = []

    for word in message.split(" "):
        user_match = re.match(USER_REVERSE_REGEX, word)
        channel_match = re.match(CHANNEL_REVERSE_REGEX, word)
        role_match = re.match(ROLE_REVERSE_REGEX, word)

        if user_match:
            user = guild.get_user(user_match.group(0))

            if user:
                words.append(u"<@{}>".format(user.id))
            else:
                words.append(word)
            continue

        if channel_match:
            channel = guild.get_channel(channel_match.group(0))

            if channel:
                words.append(u"<#{}>".format(channel.id))
            else:
                words.append(word)
            continue

        if role_match:
            role = guild.get_role(channel_match.group(0))

            if role:
                words.append(u"<@&{}>".format(role.id))
            else:
                words.append(word)
            continue

        words.append(word)

    return " ".join(words)
