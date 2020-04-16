
__all__ = ['_debug', 'eprint', 'Singleton']

import sys
import threading
import traceback

def eprint(*args, **kwargs):
    if args and isinstance(args[0], Exception):
        e = args[0]
        if _debug:
            print(''.join(traceback.format_exception(type(e), e, e.__traceback__)), file=sys.stderr, flush=True)
        else:
            print(type(e).__name__, end=': ', file=sys.stderr, flush=True)
            print(*args, file=sys.stderr, flush=True, **kwargs)
    else:
        print(*args, file=sys.stderr, flush=True, **kwargs)

class Singleton(type):
    """Metaclass for classes that wish to implement Singleton
    functionality.  If an instance of the class exists, it's returned,
    otherwise a single instance is instantiated and returned.
    """
    def __init__(cls, name, bases, dct):
        super(Singleton, cls).__init__(name, bases, dct)
        cls.__instance = None
        cls.__rlock = threading.RLock()

    def __call__(cls, *args, **kw):
        if cls.__instance is not None:
            return cls.__instance

        with cls.__rlock:
            if cls.__instance is None:
                cls.__instance = super(Singleton, cls).__call__(*args, **kw)

        return cls.__instance

class Debug(metaclass=Singleton):
        def __init__(self):
            self.__debug = False

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

_debug = Debug()

