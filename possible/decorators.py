
__all__ = ['task', 'allow']

from .engine import _tasks, _task_names_to_func_names, _funcs_permissions
from .engine import PossibleUserError

def task(arg):

    def decorator(func):
        if task_name in _tasks:
            raise PossibleUserError(f"Task '{task_name}' already defined.")
        _tasks[task_name] = func
        _task_names_to_func_names[task_name] = func.__name__
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

