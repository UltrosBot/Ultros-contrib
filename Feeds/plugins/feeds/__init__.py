# coding=utf-8

import feedparser

from twisted.internet import reactor
from twisted.internet.task import LoopingCall

from system.decorators.threads import run_async_threadpool
from system.plugins.plugin import PluginObject
from system.storage.formats import YAML

__author__ = 'Gareth Coles'
__all__ = ["FeedsPlugin"]


class FeedsPlugin(PluginObject):
    # TODO: Async support, new URLs plugin support

    config = None

    feeds = []

    failures = {}
    feed_times = {}
    targets = {}
    tasks = {}

    @property
    def urls(self):
        return self.plugins.get_plugin("URLs")

    def setup(self):
        self.logger.trace("Entered setup method.")
        try:
            self.config = self.storage.get_file(self, "config", YAML,
                                                "plugins/feeds.yml")
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

        self.config.add_callback(self.delayed_setup)

        self.logger.info("Waiting 30 seconds to set up.")

        reactor.callLater(30, self.delayed_setup)

    def delayed_setup(self):
        self.feeds = []

        self.failures.clear()
        self.feed_times.clear()
        self.targets.clear()
        self.tasks.clear()

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
            task.start(feed["frequency"])

    @run_async_threadpool
    def check_feed(self, feed):
        name = "<Unable to get feed name>"
        self.logger.trace("Feed: %s" % feed)
        try:  # Have to catch all exceptions, or the task will cancel.
            name = feed["name"]

            if name not in self.failures:
                self.failures[name] = 0

            if self.failures[name] > 5:
                self.logger.warn("Disabling update task for feed '%s' as "
                                 "there has been too many errors." % name)

                if name in self.tasks:
                    self.tasks[name].stop()

                return

            d = feedparser.parse(feed["url"])

            if name in self.feed_times:
                last = self.feed_times[name]
                if last == d.entries[0].updated:
                    return
            else:
                self.feed_times[name] = d.entries[0].updated
                self.logger.trace("Feed '%s' initialized." % name)
                if not feed["instantly-relay"]:
                    return

            entry = d.entries[0]
            entry["name"] = name

            self.logger.trace("Entry: %s" % entry)

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
            self.feed_times[name] = entry.updated
        except:
            self.logger.exception("Error in update task for feed '%s'." % name)

            if name not in self.failures:
                self.failures[name] = 0
            self.failures[name] += 1

    def relay(self, protocol, target, target_type, message):
        p = self.factory_manager.get_protocol(protocol)
        p.send_msg(target, message, target_type)

    def deactivate(self):
        for task in self.tasks.values():
            task.stop()
        self.tasks.clear()
