
__all__ = ['task']

import functools

from possible.engine import application
from possible.engine import PossiblePosfileError

def task(argument):
    def decorator(task):
        if name in application.tasks:
            raise PossiblePosfileError(f"Task '{name}' already defined")
        application.tasks[name] = task
        @functools.wraps(task)
        def wrapper(*args, **kwargs):
            return task(*args, **kwargs)
        return wrapper
    if callable(argument):
        task = argument
        name = task.__name__
        return decorator(task)
    else:
        name = argument
        return decorator

