# coding=utf-8
from kitchen.text.converters import to_bytes
from txrequests import Session

from system.decorators.ratelimit import RateLimiter, RateLimitExceededError
from system.plugins.plugin import PluginObject
from system.storage.formats import YAML

__author__ = 'Sean'
__all__ = ["DomainrPlugin", "DomainrError", "Domainr"]


class DomainrPlugin(PluginObject):

    _commands = None

    def setup(self):
        # Initial config load
        try:
            self._config = self.storage.get_file(self, "config", YAML,
                                                 "plugins/domainr.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            self.logger.error("Disabling..")
            self._disable_self()
            return
        if not self._config.exists:
            self.logger.error("Unable to find config/plugins/domainr.yml")
            self.logger.error("Disabling...")
            self._disable_self()
            return

        # Load stuff
        self._load()

        self._config.add_callback(self._load)

        # Register commands
        self.commands.register_command(
            "domainrsearch", self.search_cmd, self, "domainr.search",
            aliases=[
                "domainr", "domains"
            ], default=True
        )
        self.commands.register_command(
            "domainrinfo", self.info_cmd, self, "domainr.info",
            aliases=[
                "domaininfo", "domain"
            ],
            default=True
        )

    def reload(self):
        self._load()
        return True

    def _load(self):
        api_key = self._config.get("api-key", None)
        client_id = self._config.get("client_id", None)
        if api_key is None and client_id is None:
            self.logger.error(
                "Unable to find api-key or client-id in config. API requests "
                "will probably fail."
            )
        self.api = Domainr(api_key, client_id)

    def _respond(self, target, msg):
        """
        Convenience function for responding to something with a prefix. Not
        only does this avoid confusion, but it also stops people being able to
        execute other bot commands in the case that we need to put any
        user-supplied data at the start of a message.
        """
        target.respond("Domainr: " + msg)

    def _msg(self, protocol, target, *args):
        """
        Sends messages different ways, depending on protocol can_flood setting.
        If can_flood, each arg (and item in arg, if arg is list) is sent on its
        own line.
        If not can_flood, all args and join with a space, and args that are a
        list are joined with comma-space.
        Example:
            Call:
                _msg(proto, target, "Foo:", ["bar", "baz", "quux"])
            Can flood output:
                Foo:
                bar
                baz
                quux
            Cannot flood output:
            Foo: bar, baz, quux
        :param protocol:
        :param target:
        :param args:
        :return:
        """
        if protocol.can_flood:
            for msg in args:
                if isinstance(msg, list):
                    for m in msg:
                        self._respond(target, m)
                else:
                    self._respond(target, msg)
        else:
            to_send = []
            for msg in args:
                if isinstance(msg, list):
                    msg = ", ".join(msg)
                to_send.append(msg)
            self._respond(target, " ".join(to_send))

    def search_cmd(self, protocol, caller, source, command, raw_args,
                   parsed_args):
        if len(raw_args) == 0:
            caller.respond("Usage: {CHARS}%s <query>" % command)
            return
        else:
            try:
                deferred = self.api.search(raw_args)
                deferred.addCallbacks(
                    lambda r: self._search_cmd_result(protocol,
                                                      caller,
                                                      source,
                                                      r),
                    lambda f: self._cmd_error(caller, f)
                )
            except RateLimitExceededError:
                caller.respond("Command on cooldown - try again later")

    def info_cmd(self, protocol, caller, source, command, raw_args,
                 parsed_args):
        if len(raw_args) == 0:
            caller.respond("Usage: {CHARS}%s <domain>" % command)
            return
        else:
            try:
                deferred = self.api.info(raw_args)
                deferred.addCallbacks(
                    lambda r: self._info_cmd_result(protocol,
                                                    caller,
                                                    source,
                                                    r),
                    lambda f: self._cmd_error(caller, f)
                )
            except RateLimitExceededError:
                caller.respond("Command on cooldown - try again later")

    def _search_cmd_result(self, protocol, caller, source, result):
        """
        Receives the API response for search
        """
        loud = self._commands.perm_handler.check("domainr.search.loud",
                                                 caller,
                                                 source,
                                                 protocol)
        target = None
        if loud:
            target = source
        else:
            target = caller
        try:
            if "results" in result:
                msgs = []
                for res in result["results"]:
                    self.logger.trace(res)
                    msg = u"%s%s - %s" % (res["domain"],
                                          res["path"],
                                          res["availability"])
                    msgs.append(msg)
                self._msg(protocol, target, msgs)
            elif "message" in result:
                self.logger.error(
                    "Message from Domainr API:\r\n{}", result["message"]
                )
            else:
                self.logger.error(
                    "Unexpected response from API:\r\n{}", to_bytes(result)
                )
        except:
            self.logger.exception("Please tell the developer about this error")

    def _info_cmd_result(self, protocol, caller, source, result):
        """
        Receives the API response for info
        """
        loud = self._commands.perm_handler.check("domainr.info.loud",
                                                 caller,
                                                 source,
                                                 protocol)
        target = None
        if loud:
            target = source
        else:
            target = caller
        try:
            msgs = []
            msgs.append(u"Availability: %s" % result["availability"])
            if result["availability"] in (Domainr.AVAILABLE, Domainr.MAYBE):
                msgs.append(u"Register: %s" % result["register_url"])
            self._msg(protocol, target, msgs)
        except:
            self.logger.exception("Please tell the developer about this error")

    def _cmd_error(self, caller, failure):
        """
        :type failure: twisted.python.failure.Failure
        """
        # Some errors will be caused by user input
        if failure.check(DomainrError):
            self._respond(caller, failure.value.message)
        else:
            self.logger.error("Error while fetching info",
                              exc_info=(
                                  failure.type,
                                  failure.value,
                                  failure.tb
                              ))
            caller.respond("There was an error while contacting Domainr - "
                           "please alert a bot admin or try again later")


class Domainr(object):
    """
    Basic Domainr API wrapper. Returns parsed JSON response.
    """

    # Availability responses
    AVAILABLE = "available"
    TAKEN = "taken"
    UNAVAILABLE = "unavailable"
    MAYBE = "maybe"
    TLD = "tld"

    # API key and client_id auth use different domains
    API_URL_CID = "https://api.domainr.com/v1/"
    API_URL_KEY = "https://domainr.p.mashape.com/v1/"

    def __init__(self, api_key=None, client_id=None):
        self.api_key = api_key
        self.client_id = client_id
        self._session = Session()

    def _handle_response(self, response):
        result = response.json()

        if "error" in result:
            raise DomainrError(**result["error"])
        elif "error_message" in result:
            # Apparently the API doesn't follow the docs...
            raise DomainrError(message=result["error_message"])
        else:
            return result

    # I'll have to play around to see what the best limit/buffer is, but it
    # should be ~60 per minute anyway.
    # Sod it, the rate limiting plugin (coming soon) can deal with
    # burst/slowdown - we'll just set this to 60 per 60.
    # 2015/10/07 - This is way over (~260x) what the free tier allows, but this
    # has to work with the paid tier too. Additionally, limiting the free tier
    # would have to be done in terms of at least daily time periods to allow
    # for bursts. I'll consider how best to deal with this. It's not like we
    # were making 10,000 calls per month before anyway, but it's definitely
    # something that's used in rapid bursts between long periods of non-use.
    # Config options would likely be best.
    @RateLimiter(limit=60, buffer=10, time_period=60)
    def _make_request(self, method, payload):
        """
        Actually make the HTTP request.
        :rtype : twisted.internet.defer.Deferred
        """
        url = self.API_URL_KEY
        if self.client_id is not None:
            payload["client_id"] = self.client_id
            url = self.API_URL_CID
        elif self.api_key is not None:
            payload["mashape-key"] = self.api_key
        deferred = self._session.get(url + method, params=payload)
        deferred.addCallback(self._handle_response)
        return deferred

    def search(self, query):
        """
        Search for domain suggestions for the given query.
        :rtype : twisted.internet.defer.Deferred
        """
        payload = {
            "q": query
        }
        return self._make_request("search", payload)

    def info(self, domain):
        """
        Get info for given domain.
        :rtype : twisted.internet.defer.Deferred
        """
        payload = {
            "q": domain
        }
        return self._make_request("info", payload)


class DomainrError(Exception):

    def __init__(self, message, status=None, *args, **kwargs):
        Exception.__init__(self, message)
        self.message = message
        self.status = status
        # These should be empty, unless domainr changes their API.
        self._args = args
        self._kwargs = kwargs

    def __str__(self):
        status_msg = ""
        if self.status is not None:
            status_msg = "[%s] " % self.status
        msg = "%s: %s%s" % (self.__class__, status_msg, self.message)
        if len(self._args) > 0:
            msg += " | Args: %s" % ", ".join(self._args)
        if len(self._kwargs) > 0:
            msg += " | KWArgs: %s" % ", ".join(
                "%s: %s" % (k, v) for k, v in self._kwargs.iteritems()
            )
        return msg
