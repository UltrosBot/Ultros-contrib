# coding=utf-8
from system.protocols.generic.factory import BaseFactory

__author__ = 'Gareth Coles'


class Factory(BaseFactory):
    def connect(self):
        self.buildProtocol(None)
