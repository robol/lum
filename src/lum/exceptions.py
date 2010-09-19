#
# -*- coding: utf-8 -*-

class LumError(Exception):

    def __init__(self, message):
        self._message = message

    def __repr__(self):
        return "<LumError: %s>" % self._message

    def __str__(self):
        return self.__repr__(self)

class LumUserNotFoundError(Exception):
    pass

class LumUnsupportedError(Exception):
    pass
