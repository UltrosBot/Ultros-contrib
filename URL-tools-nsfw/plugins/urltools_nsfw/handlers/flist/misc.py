# coding=utf-8

from collections import defaultdict

__author__ = 'Gareth Coles'


def flatten_character(data):
    done = defaultdict(lambda: None)

    done[u"info"] = defaultdict(lambda: None)

    for section in data[u"info"].itervalues():
        section_done = defaultdict(lambda: None)
        section_name = section[u"group"].lower().replace(u" ", u"_")

        for group in section[u"items"]:
            group_name = group[u"name"].lower().replace(u" ", u"_")
            section_done[group_name] = group[u"value"]

        done[u"info"][section_name] = section_done

    return done


def flatten_kinks(data):
    done = defaultdict(lambda: None)
    done[u"types"] = defaultdict(lambda: None)
    done[u"preferences"] = defaultdict(lambda: None)

    for group in data[u"kinks"].values():
        type_flattened = defaultdict(lambda: None)

        for item in group[u"items"]:
            type_flattened[item[u"name"]] = item[u"choice"]

            if item[u"choice"] not in done[u"preferences"]:
                done[u"preferences"][item[u"choice"]] = []

            done[u"preferences"][item[u"choice"]].append(item[u"name"])

        group_name = group[u"group"].replace(u"&amp;", u"&")
        done[u"types"][group_name] = type_flattened

    return done
