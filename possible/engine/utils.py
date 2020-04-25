
__all__ = ['debug', 'eprint', 'to_bytes', 'to_str']

import sys
import traceback


def eprint(*args, **kwargs):
    if args and isinstance(args[0], Exception):
        e = args[0]
        if debug:
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

    def print(self, *args):
        if self.__debug:
            eprint(*args)

    def __str__(self):
        if self.__debug:
            return "debug enabled"
        else:
            return "debug disabled"


debug = Debug()


def to_bytes(obj):
    if obj is None:
        return None
    if isinstance(obj, bytes):
        return obj
    elif isinstance(obj, int):
        return str(obj).encode('utf-8')
    elif isinstance(obj, str):
        return obj.encode('utf-8')
    else:
        print(type(obj))
        raise TypeError('obj must be a str or bytes type')


def to_str(obj):
    if isinstance(obj, str):
        return obj
    elif isinstance(obj, bytes):
        return obj.decode('utf-8')
    else:
        raise TypeError('obj must be a bytes or str type')
