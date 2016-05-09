# coding=utf-8

__author__ = 'Gareth Coles'


class Game(object):
    def __init__(self, game, _type=None, url=None):
        # TODO: Document what type and url are
        self.game = game
        self.type = _type
        self.url = url
