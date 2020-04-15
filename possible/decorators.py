
__all__ = ['task', 'allow']

from .engine import tasks, tasks_names, tasks_permissions
from .engine import PossibleUserError

def task(arg):

    def decorator(func):
        if name in tasks:
            raise PossibleUserError(f"Task '{name}' already defined.")
        tasks[name] = func
        if name != func.__name__:
            tasks_names[name] = func.__name__
        return func

    if callable(arg):
        name = arg.__name__
        return decorator(arg)
    else:
        name = arg
        return decorator


def allow(*args):

    def decorator(func):
        name = func.__name__
        if name not in tasks_permissions:
            tasks_permissions[name] = set()
        tasks_permissions[name].update(args)
        return func

    if len(args) == 1 and callable(args[0]):
        name = args[0].__name__
        raise PossibleUserError(f"Function '{name}': allow list required.")
    else:
        return decorator

