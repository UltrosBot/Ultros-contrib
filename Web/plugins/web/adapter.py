__author__ = 'Gareth Coles'

from bottle import TwistedServer
from twisted.internet import reactor
from twisted.internet.defer import DeferredList
from twisted.python.threadpool import ThreadPool
from twisted.web import server, wsgi

from system.singleton import Singleton
from utils.log import getLogger


class Server(TwistedServer):
    __metaclass__ = Singleton

    factory = None
    handler = None
    port = None
    resource = None
    thread_pool = None

    def __init__(self):
        self.logger = getLogger("Web/Adapter")
        reactor.addSystemEventTrigger('after', 'shutdown', self.really_stop)
        super(Server, self).__init__()

    def __call__(self, host="127.0.0.1", port=8080, **config):
        self.logger.debug("== Settings ==")
        self.logger.debug("> Options: %s" % config)
        self.logger.debug("> Host: %s" % host)
        self.logger.debug("> Port: %s" % port)
        self.options = config
        self.host = host
        self.port = int(port)

        return self

    def stop(self):
        ds = []
        if self.port is not None:
            ds.append(self.port.stopListening())
        if self.factory is not None:
            self.factory.stopFactory()

        self.factory = None
        self.handler = None
        self.port = None
        self.resource = None

        return DeferredList(ds)

    def really_stop(self):
        self.stop()

        if self.thread_pool is not None:
            self.thread_pool.stop()
            self.thread_pool = None

    def run(self, handler):
        self.thread_pool = ThreadPool()
        self.thread_pool.start()

        self.handler = handler
        self.resource = wsgi.WSGIResource(reactor, self.thread_pool,
                                          self.handler)
        self.factory = server.Site(self.resource)
        self.port = reactor.listenTCP(self.port, self.factory,
                                      interface=self.host)

        reactor.run()  # Honestly, just so the method doesn't block
