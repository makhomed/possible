
__all__ = ['eprint', 'Singleton']

import traceback
from threading import RLock
import sys

def eprint(*args, **kwargs):
    if args and isinstance(args[0], Exception):
        e = args[0]
        print(''.join(traceback.format_exception(type(e), e, e.__traceback__)), file=sys.stderr, flush=True)
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
        cls.__rlock = RLock()

    def __call__(cls, *args, **kw):
        if cls.__instance is not None:
            return cls.__instance

        with cls.__rlock:
            if cls.__instance is None:
                cls.__instance = super(Singleton, cls).__call__(*args, **kw)

        return cls.__instance


class Display(metaclass=Singleton):
        pass
