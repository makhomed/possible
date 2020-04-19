
__all__ = ['_debug', 'eprint']

import sys
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


class Debug():
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
