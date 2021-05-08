
__all__ = ['task', 'allow']

from possible.engine import runtime
from possible.engine.exceptions import PossibleRuntimeError


def task(arg):

    def decorator(func):
        if task_name in runtime.tasks:
            raise PossibleRuntimeError(f"Task '{task_name}' already defined.")
        runtime.tasks[task_name] = func
        return func

    if callable(arg):
        task_name = arg.__name__.replace('_', '-')
        return decorator(arg)
    else:
        task_name = arg
        return decorator


def allow(*args):

    def decorator(func):
        func_name = func.__name__
        if func_name not in runtime.funcs_permissions:
            runtime.funcs_permissions[func_name] = set()
        runtime.funcs_permissions[func_name].update(args)
        return func

    if len(args) == 1 and callable(args[0]):
        func_name = args[0].__name__
        raise PossibleRuntimeError(f"Function '{func_name}': @allow list required.")
    else:
        return decorator
