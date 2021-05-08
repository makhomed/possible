
__all__ = ['task', 'group', 'allow']

from possible.engine import runtime
from possible.engine.exceptions import PossibleRuntimeError


def task(arg):

    def decorator(func):
        task_name = func.__name__.replace('_', '-')
        if task_name not in runtime.tasks:
            runtime.tasks[task_name] = func
        else:
            raise PossibleRuntimeError(f"Task '{task_name}' already defined.")
        return func

    def decorator_with_arguments(func):
        task_name = func.__name__.replace('_', '-')
        raise PossibleRuntimeError(f"Task '{task_name}': @task can't have arguments.")

    if callable(arg):
        return decorator(arg)
    else:
        return decorator_with_arguments


def group(arg):

    def decorator(func):
        task_name = func.__name__.replace('_', '-')
        if task_name not in runtime.groups:
            runtime.groups[task_name] = arg
        else:
            raise PossibleRuntimeError(f"Task '{task_name}': @group already defined.")
        return func

    if callable(arg):
        task_name = arg.__name__.replace('_', '-')
        raise PossibleRuntimeError(f"Task '{task_name}': @group name required.")
    else:
        return decorator


def allow(*args):

    def decorator(func):
        task_name = func.__name__.replace('_', '-')
        if task_name not in runtime.permissions:
            runtime.permissions[task_name] = set()
        runtime.permissions[task_name].update(args)
        return func

    if len(args) == 1 and callable(args[0]):
        task_name = args[0].__name__.replace('_', '-')
        raise PossibleRuntimeError(f"Task '{task_name}': @allow list required.")
    else:
        return decorator
