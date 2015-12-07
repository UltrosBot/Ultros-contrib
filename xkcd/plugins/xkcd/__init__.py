# coding=utf-8

import time
import treq
import random

from bs4 import BeautifulSoup
from twisted.internet import defer

from system.plugins.plugin import PluginObject
from system.storage.formats import YAML

__author__ = 'Sean'
__all__ = ["xkcdError", "xkcdPlugin", "NoSuchComicError", "ConnectionError"]


# Some people think making your own exceptions is pointless. They're wrong.
# Fuck 'em.
class xkcdError(Exception):
    """
    Generic exception in this module
    """
    pass


class NoSuchComicError(xkcdError):
    """
    The requested comic doesn't exist
    """
    pass


class ConnectionError(xkcdError):
    """
    Technical hitch killed our shit(ch?)
    """
    pass


class xkcdPlugin(PluginObject):
    # TODO: treq -> txrequests

    _config = None

    _comic_cache = None
    _archive = None

    def setup(self):
        # Initial config load
        try:
            self._config = self.storage.get_file(self, "config", YAML,
                                                 "plugins/xkcd.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            self.logger.error("Disabling...")
            self._disable_self()
            return
        if not self._config.exists:
            self.logger.error("Unable to find config/plugins/xkcd.yml")
            self.logger.error("Disabling...")
            self._disable_self()
            return
        # Same for the data files
        try:
            self._comic_cache = self.storage.get_file(
                self, "data", YAML,
                "plugins/xkcd/comic-cache.yml"
            )
        except Exception:
            self.logger.exception("Error loading comic-cache!")
            self.logger.error("Disabling...")
            self._disable_self()
        try:
            self._archive = self.storage.get_file(self, "data", YAML,
                                                  "plugins/xkcd/archive.yml")
        except Exception:
            self.logger.exception("Error loading archive!")
            self.logger.error("Disabling...")
            self._disable_self()

        # Initial data file setup and stuff
        self._load()

        self._config.add_callback(self._load)
        self._comic_cache.add_callback(self._load)
        self._archive.add_callback(self._load)

        # Register commands
        self.commands.register_command("xkcd",
                                       self.xkcd_cmd,
                                       self,
                                       "xkcd.xkcd", default=True)

    def reload(self):
        # Reload config
        try:
            self._config.reload()
        except:
            self.logger.exception("Error reloading config file!")
            return False
        # Reload data
        try:
            self._comic_cache.reload()
            self._archive.reload()
        except:
            self.logger.exception("Error reloading data files!")
            return False
        # Everything went fine
        return True

    def _load(self):
        altered = False
        if "last-update" not in self._archive:
            self._archive["last-update"] = 0
            altered = True
        if "latest" not in self._archive:
            self._archive["latest"] = 0
            altered = True
        if "by-id" not in self._archive:
            self._archive["by-id"] = {}
            altered = True
        if altered:
            self._archive.save()

    def _archive_time(self):
        return self._config["archive-time"]

    def _respond(self, target, msg):
        """
        Convenience function for responding to something with a prefix. Not
        only does this avoid confusion, but it also stops people being able to
        execute other bot commands in the case that we need to put any
        user-supplied data at the start of a message.
        """
        target.respond("[xkcd] " + msg)

    def _log_failure(self, failure, msg="Exception occurred"):
        self.logger.error(msg,
                          exc_info=(failure.type, failure.value, failure.tb))

    def xkcd_cmd(self, protocol, caller, source, command, raw_args,
                 parsed_args):
        self.logger.trace("xkcd_cmd()")
        args = raw_args.split()  # Quick fix for new command handler signature
        # Decide what they want to do
        if len(args) == 0:
            # Get random
            self.logger.trace("xkcd_cmd - get random")
            d = self.get_random_comic()
            d.addCallbacks(self._xkcd_command_get_comic_callback,
                           self._log_failure,
                           [source])
        else:
            # Get specific
            ## Attempt to use single arg as ID if applicable
            cid = None
            if len(args) == 1:
                try:
                    cid = int(args[0])
                except ValueError:
                    pass
            ## Actually get the comic
            if cid is None:
                ## Get comic by title
                self.logger.trace("xkcd_cmd - get by term")
                d = self.get_comic_by_term(raw_args)
                d.addCallbacks(self._xkcd_command_get_comic_callback,
                               self._xkcd_command_get_comic_errback,
                               callbackArgs=[source],
                               errbackArgs=[caller, cid, False])
            else:
                ## Get comic by id
                self.logger.trace("xkcd_cmd - get by ID")
                d = self.get_comic_by_id(cid)
                d.addCallbacks(self._xkcd_command_get_comic_callback,
                               self._xkcd_command_get_comic_errback,
                               callbackArgs=[source],
                               errbackArgs=[caller, cid, True])

    def _xkcd_command_get_comic_callback(self, comic, target):
        self.logger.trace("_xkcd_command_get_comic_callback()")
        self._respond(target,
                      '"%s" - %s' % (
                          comic["title"],
                          ("http://xkcd.com/%s/" % comic["num"])
                      ))

    def _xkcd_command_get_comic_errback(self, failure, target, cid, is_id):
        if failure.check(NoSuchComicError):
            if is_id:
                self._respond(target, "No comic with that ID")
            else:
                self._respond(target,
                              "Could not find a comic matching that term - "
                              "if you know one, tell a bot admin")
        elif failure.check(ConnectionError):
            self._log_failure(failure, "Error while getting comic '%s'" % cid)
            self._respond(target,
                          "Error while fetching comic info - try again later")
        else:
            self._log_failure(failure, "Unexpected exception occurred")

    def get_comic(self, url):
        """
        Returns the info for the given comic
        :param url: Comic URL in format http://xkcd.com/1316/
        :return: Deferred that fires with a dict of info
        """
        self.logger.debug("Getting comic (from url)")
        term = "xkcd.com/"
        pos = url.find(term)
        if pos < 0:
            return defer.succeed(None)
        pos += len(term)
        end = url.find("/")
        if end < 0:
            end = len(url) - 1
        comic_id = url[pos:end]
        return self.get_comic_by_id(comic_id)

    def get_random_comic(self):
        """
        Returns the info for a random comic
        :return: Deferred that fires with a dict of info
        """
        self.logger.debug("Getting random comic")
        d = self._ensure_archive_freshness()
        d.addBoth(
            lambda r: self._get_random_comic()
        )
        return d

    def _get_random_comic(self):
        self.logger.trace("_get_random_comic()")
        latest = self._archive["latest"]
        cid = random.randint(1, latest)
        while cid not in self._archive["by-id"]:
            # In case a comic is ever removed/skipped (paranoid programming)
            cid = random.randint(1, latest)
        return self.get_comic_by_id(cid)

    def get_comic_by_term(self, term):
        """
        Returns the info for a comic that matches the given term (title)
        :param url: Comic ID number
        :return: Deferred that fires with a dict of info
        """
        self.logger.debug("Getting comic by term")
        # Update the archive, if necessary
        d = self._ensure_archive_freshness()
        d.addBoth(
            lambda r: self._get_comic_by_term(term)
        )
        return d

    def _get_comic_by_term(self, term):
        self.logger.trace("_get_comic_by_term()")
        # Search the archive for the given term
        term = term.lower()
        half_match = None
        with self._archive.mutex:
            for cid, item in self._archive["by-id"].iteritems():
                if term == item:
                    half_match = cid
                    break
                elif term in item:
                    half_match = cid
        if half_match is None:
            return defer.succeed(None)
        return self.get_comic_by_id(half_match)

    def get_comic_by_id(self, comic_id):
        """
        Returns the info for the given comic
        :param url: Comic ID number
        :return: Deferred that fires with a dict of info
        """
        self.logger.debug("Getting comic by ID")
        if comic_id in self._comic_cache:
            return defer.succeed(dict(self._comic_cache[comic_id]))
        else:
            d = treq.get("http://xkcd.com/%s/info.0.json" % comic_id)
            d.addCallbacks(self._get_comic_result,
                           self._get_comic_error,
                           [comic_id])
            return d

    def _get_comic_result(self, result, comic_id):
        self.logger.trace("_get_comic_result()")
        if result.code == 200:
            d = result.json()
            d.addCallbacks(self._get_comic_result_json,
                           self._get_comic_error,
                           [comic_id])
            return d
        elif result.code == 404:
            return defer.fail(NoSuchComicError(comic_id))
        else:
            return defer.fail(
                ConnectionError(
                    "Unexpected response code: %s" % result.code)
            )

    def _get_comic_result_json(self, result, comic_id):
        self.logger.trace("_get_comic_result_json()")
        with self._comic_cache:
            self._comic_cache[comic_id] = result
        return result

    def _get_comic_error(self, failure):
        self._log_failure(failure, "Error while fetching comic")

    def _ensure_archive_freshness(self):
        self.logger.trace("Ensuring archive freshness")
        if time.time() - self._archive["last-update"] > self._archive_time:
            return self._update_archive()
        else:
            return defer.succeed(True)

    def _update_archive(self):
        self.logger.debug("Updating archive...")
        d = treq.get("http://xkcd.com/archive/")
        d.addCallbacks(
            self._update_archive_callback,
            self._log_failure,
            errbackArgs=["Error while updating archive (fetching)"]
        )
        return d

    def _update_archive_callback(self, response):
        self.logger.trace("_update_archive_callback()")
        d = response.content()
        d.addCallbacks(
            self._update_archive_content_callback,
            self._log_failure,
            errbackArgs=["Error while updating archive (reading)"]
        )
        return d

    def _update_archive_content_callback(self, content):
        self.logger.trace("_update_archive_content_callback()")
        with self._archive.mutex:
            try:
                soup = BeautifulSoup(content)
                links = soup.select("#middleContainer a")
                latest = 1
                for link in links:
                    href = None
                    try:
                        href = link["href"]
                        cid = int(href.strip("/"))
                        self._archive["by-id"][cid] = link.text.lower()
                        if cid > latest:
                            latest = cid
                    except Exception as e:
                        self.logger.exception("Error while updating archive "
                                              "cache - unexpected href '%s'"
                                              % href)
                self._archive["latest"] = latest
                self._archive["last-update"] = time.time()
                return defer.succeed(True)
            except Exception as e:
                self.logger.exception("Error while updating archive cache "
                                      "- using old version")
                return defer.fail()

# Note: The comic info (comic-cache) isn't actually of any use as it currently
# stands (unless another plugin wants to use it), as we only use the name and
# id number, which we have from the archive anyway (although we lower it when
# storing it to optimise searching, but that can be changed). I've left it in
# for now in case I can think of a use for it.
