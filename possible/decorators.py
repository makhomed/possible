
__all__ = ['task']

import functools

from .engine import tasks
from .engine import PossiblePosfileError

def task(argument):

    def decorator(func):
        if name in tasks:
            raise PossiblePosfileError(f"Task '{name}' already defined")
        tasks[name] = func

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    if callable(argument):
        func = argument
        name = func.__name__
        return decorator(func)
    else:
        name = argument
        return decorator

