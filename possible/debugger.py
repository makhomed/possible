
__all__ = ['debug']

from .utils import Singleton

class Debug(metaclass=Singleton):
        def __init__(self):
            self.__debug = True

        def __bool__(self):
            return self.__debug

        def enable(self):
            self.__debug = True

        def disable(self):
            self.__debug = False

        def __str__(self):
            if self.__debug:
                return "debug enabled"
            else:
                return "debug disabled"

debug = Debug()

