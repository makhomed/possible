
__all__ = ['task', 'allow', 'default']

from .engine import _tasks, _funcs_permissions, _func_defaults
from .engine import PossibleUserError


def task(arg):

    def decorator(func):
        if task_name in _tasks:
            raise PossibleUserError(f"Task '{task_name}' already defined.")
        _tasks[task_name] = func
        return func

    if callable(arg):
        task_name = arg.__name__
        return decorator(arg)
    else:
        task_name = arg
        return decorator


def allow(*args):

    def decorator(func):
        func_name = func.__name__
        if func_name not in _funcs_permissions:
            _funcs_permissions[func_name] = set()
        _funcs_permissions[func_name].update(args)
        return func

    if len(args) == 1 and callable(args[0]):
        func_name = args[0].__name__
        raise PossibleUserError(f"Function '{func_name}': @allow list required.")
    else:
        return decorator


def default(arg):

    def decorator(func):
        _func_defaults[func.__name__] = arg
        return func

    if callable(arg):
        func_name = arg.__name__
        raise PossibleUserError(f"Function '{func_name}': @default argument required.")
    else:
        return decorator
