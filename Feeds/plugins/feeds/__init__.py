# coding=utf-8
__author__ = 'Gareth Coles'

import feedparser

from twisted.internet import reactor
from twisted.internet.task import LoopingCall

from system.plugin import PluginObject
from system.plugin_manager import YamlPluginManagerSingleton
from system.event_manager import EventManager

from utils.config import YamlConfig


class Plugin(PluginObject):

    config = None
    events = None
    manager = None
    plugman = None
    urls = None

    feeds = []
    feed_times = {}
    targets = {}

    tasks = {}
    failures = {}

    def setup(self):
        self.logger.debug("Entered setup method.")
        try:
            self.config = YamlConfig("plugins/feeds.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            self.logger.error("Disabling..")
            self._disable_self()
            return
        if not self.config.exists:
            self.logger.error("Unable to find config/plugins/feeds.yml")
            self.logger.error("Disabling..")
            self._disable_self()
            return

        self.events = EventManager.instance()
        self.plugman = YamlPluginManagerSingleton.instance()
        self.urls = self.plugman.getPluginByName("URLs").plugin_object

        self.logger.info("Waiting 30 seconds to set up.")

        reactor.callLater(30, self.delayed_setup)

    def delayed_setup(self):
        for name, target in self.config["targets"].items():
            proto = target["protocol"]
            if proto in self.factory_manager.factories:
                self.targets[name] = target
            else:
                self.logger.warn("Unknown protocol '%s' in target '%s'"
                                 % (proto, name))

        for feed in self.config["feeds"]:
            append = True
            for target in feed["targets"]:
                if target["name"] not in self.targets:
                    self.logger.warn("Unknown target '%s' for feed '%s'"
                                     % (target["name"], feed["name"]))
                    append = False
                    break

            if append:
                self.feeds.append(feed)

        for feed in self.feeds:
            task = LoopingCall(self.check_feed, feed)
            self.tasks[feed["name"]] = task
            self.check_feed(feed)
            task.start(feed["frequency"])

    def check_feed(self, feed):
        name = "<Unable to get feed name>"
        self.logger.debug("Feed: %s" % feed)
        try:  # Have to catch all exceptions, or the task will cancel.
            name = feed["name"]

            if name not in self.failures:
                self.failures[name] = 0

            if self.failures[name] > 5:
                self.logger.warn("Disabling update task for feed '%s' as "
                                 "there has been lots of errors." % name)
                self.tasks[name].stop()
                return

            d = feedparser.parse(feed["url"])

            self.logger.debug("Feed object: %s" % d)
            self.logger.debug("Entries: %s" % d.entries)

            if name in self.feed_times:
                last = self.feed_times[name]
                if last == d.entries[0].updated:
                    return
            else:
                self.feed_times[name] = d.entries[0].updated
                self.logger.debug("Feed '%s' initialized." % name)
                if not feed["instantly-relay"]:
                    return

            self.logger.info("Feed updated: '%s'" % feed)

            entry = d.entries[0]
            entry["name"] = name

            if "title" not in entry:
                entry["title"] = "(No title)"

            url = "No URL"
            if "link" in entry:
                url = self.urls.tinyurl(entry["link"])

            for target in feed["targets"]:
                fmt = target["format"]
                formatted = fmt.replace("{NAME}", name)
                formatted = formatted.replace("{TITLE}", entry["title"])
                formatted = formatted.replace("{URL}", url)
                target = self.targets[target["name"]]

                self.relay(target["protocol"], target["target"],
                           target["type"], formatted)
        except:
            self.logger.exception("Error in update task for feed '%s'." % name)

    def relay(self, protocol, target, target_type, message):
        p = self.factory_manager.get_protocol(protocol)
        p.send_msg(target, message, target_type)
