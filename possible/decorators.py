
__all__ = ['task']

from .engine import tasks
from .engine import PossiblePosfileError

def task(arg):

    def decorator(func):
        if name in tasks:
            raise PossiblePosfileError(f"Task '{name}' already defined")
        tasks[name] = func
        return func

    if callable(arg):
        name = arg.__name__
        return decorator(arg)
    else:
        name = arg
        return decorator

