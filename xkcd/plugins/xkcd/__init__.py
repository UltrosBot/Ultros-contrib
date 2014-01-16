import random
import requests
import time
from bs4 import BeautifulSoup

from system.command_manager import CommandManager
from system.plugin import PluginObject
from utils.config import YamlConfig
from utils.data import YamlData

__author__ = 'Sean'


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


class Plugin(PluginObject):

    ARCHIVE_TIME = 60 * 12  # Update archive every 12 hours

    commands = None
    config = None

    def setup(self):
        ### Grab important shit
        self.commands = CommandManager.instance()

        ### Open the data file (comic data cache)
        try:
            self.comic_cache = YamlData("plugins/xkcd/comic-cache.yml")
        except Exception:
            self.logger.exception("Error loading comic-cache!")
            self.logger.error("Disabling...")
            self._disable_self()
        try:
            self.archive = YamlData("plugins/xkcd/archive.yml")
        except Exception:
            self.logger.exception("Error loading archive!")
            self.logger.error("Disabling...")
            self._disable_self()

        ### Initial config/data setup stuff
        self._load()

        ### Register commands
        self.commands.register_command("xkcd",
                                       self.xkcd_cmd,
                                       self,
                                       "xkcd.xkcd")

    def reload(self):
        try:
            self.comic_cache.reload()
            self.archive.reload()
        except Exception:
            self.logger.exception("Error reloading data files!")
            return False
        self._load()
        return True

    def _load(self):
        altered = False
        if "last-update" not in self.archive:
            self.archive["last-update"] = 0
            altered = True
        if "latest" not in self.archive:
            self.archive["latest"] = 0
            altered = True
        if "by-id" not in self.archive:
            self.archive["by-id"] = {}
            altered = True
        if altered:
            self.archive.save()

    def _send_comic(self, target, comic):
        target.respond('[xkcd] "%s" - %s' % (comic["title"],
                                             ("http://xkcd.com/%s/" %
                                              comic["num"])))

    def xkcd_cmd(self, caller, source, args, protocol):
        ### Decide what they want to do
        comic = None
        if len(args) == 0:
            ### Get random
            comic = self.get_random_comic()
            self._send_comic(source, comic)
        else:
            ### Get specific
            ## Attempt to use single arg as ID if applicable
            cid = None
            if len(args) == 1:
                try:
                    cid = int(args[0])
                except ValueError:
                    pass
            if cid is None:
                ## Get comic by title
                term = " ".join(args)
                try:
                    comic = self.get_comic_by_term(term)
                    self._send_comic(source, comic)
                except NoSuchComicError as e:
                    caller.respond("Could not find a comic matching that term "
                                   "- if you know one, tell a bot admin")
                    return
                except ConnectionError as e:
                    self.logger.exception("Error while getting comic '%s'" %
                                          comic)
                    caller.response("Error while fetching comic info - try "
                                    "again later")
                    return
            else:
                ## Get comic by id
                try:
                    comic = self.get_comic_by_id(cid)
                    self._send_comic(source, comic)
                except NoSuchComicError as e:
                    caller.respond("No comic with that ID")
                    return
                except ConnectionError as e:
                    self.logger.exception("Error while getting comic '%s'" %
                                          comic)
                    caller.response("Error while fetching comic info - try "
                                    "again later")
                    return

    def get_comic(self, url):
        """
        Returns the info for the given comic
        :param url: Comic URL in format http://xkcd.com/1316/
        :return: Dict of info
        """
        term = "xkcd.com/"
        pos = url.find(term)
        if pos < 0:
            return None
        pos += len(term)
        end = url.find("/")
        if end < 0:
            end = len(url) - 1
        comic_id = url[pos:end]
        return self.get_comic_by_id(comic_id)

    def get_random_comic(self):
        self._ensure_archive_freshness()
        latest = self.archive["latest"]
        cid = random.randint(1, latest)
        while cid not in self.archive["by-id"]:
            # In case a comic is ever removed/skipped (paranoid programming)
            cid = random.randint(1, latest)
        return self.get_comic_by_id(cid)

    def get_comic_by_id(self, comic_id):
        """
        Returns the info for the given comic
        :param url: Comic ID number
        :return: Dict of info
        """
        if comic_id not in self.comic_cache:
            try:
                res = requests.get("http://xkcd.com/%s/info.0.json" % comic_id)
                if res.status_code == 403:
                    raise NoSuchComicError("Comic '%s' doesn't exist" %
                                           comic_id)
                with self.comic_cache:
                    self.comic_cache[comic_id] = res.json()
            except Exception as e:
                raise ConnectionError("Couldn't get info for comic '%s'" %
                                      comic_id)
        return dict(self.comic_cache[comic_id])

    def get_comic_by_term(self, term):
        """
        Returns the info for a comic that matches the given term (title)
        :param url: Comic ID number
        :return: Dict of info
        """
        ### Update the archive, if necessary
        self._ensure_archive_freshness()
        ### Search the archive for the given term
        term = term.lower()
        half_match = None
        with self.archive.mutex:
            for cid, item in self.archive["by-id"].iteritems():
                if term == item:
                    half_match = cid
                    break
                elif term in item:
                    half_match = cid
        if half_match is None:
            return None
        return self.get_comic_by_id(half_match)

    def _ensure_archive_freshness(self):
        with self.archive.mutex:
            if time.time() - self.archive["last-update"] > self.ARCHIVE_TIME:
                self.logger.debug("Updating archive...")
                try:
                    response = requests.get("http://xkcd.com/archive/")
                    soup = BeautifulSoup(response.content)
                    links = soup.select("#middleContainer a")
                    latest = 1
                    for link in links:
                        href = None
                        try:
                            href = link["href"]
                            cid = int(href.strip("/"))
                            self.archive["by-id"][cid] = link.text.lower()
                            if cid > latest:
                                latest = cid
                        except Exception as e:
                            self.logger.exception("Error while updating "
                                                  "archive cache - unexpected "
                                                  "href '%s'" % href)
                    self.archive["latest"] = latest
                    self.archive.save()
                    self.archive["last-update"] = time.time()
                except Exception as e:
                    self.logger.exception("Error while updating archive cache "
                                          "- using old version")

# Note: The comic info (comic-cache) isn't actually of any use as it currently
# stands (unless another plugin wants to use it), as we only use the name and
# id number, which we have from the archive anyway (although we lower it when
# storing it to optimise searching, but that can be changed). I've left it in
# for now in case I can think of a use for it.
