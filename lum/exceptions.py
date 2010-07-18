#
# -*- coding: utf-8 -*-

class LumException(Exception):

    def __init__(self, message):
        self._message = message

    def __repr__(self):
        return "<LumException: %s" % self._message

    def __str__(self):
        return self.__repr__(self)
