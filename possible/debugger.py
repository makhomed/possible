
__all__ = ['debug']

from .utils import Singleton

class Debug(metaclass=Singleton):
        def __init__(self):
            self.__debug = True

        def __bool__(self):
            return self.__debug

        def enable(self):
            self.debug = True

        def disable(self):
            self.debug = False

debug = Debug()

