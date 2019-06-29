
__all__ = ['task', 'hosts', 'Posfile', 'Application']

import functools
import importlib
import inspect
import sys

from .exceptions import PossiblePosfileError, PossibleApplicationError, PossibleRuntimeError


_tasks = dict()
_application = None


def task(argument):
    def decorator(task):
        if name in _tasks:
            raise PossiblePosfileError(f"Task '{name}' already defined")
        _tasks[name] = task
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


def hosts(target):
    application = _application
    inventory = application.inventory
    if target in inventory.hosts:
        return [target]
    elif target in inventory.groups:
        _hosts = []
        group = inventory.groups[target]
        return list(group.hosts)
    else:
        raise PossibleRuntimeError(f"Target {target} is not valid host or group name")


class Posfile:
    def __init__(self, config):
        posfile = config.workdir / (config.posfile + '.py')
        if not posfile.exists() or not posfile.is_file():
            raise PossiblePosfileError(f"Posfile '{posfile}' not exists")
        self.posfile = posfile
        if config.workdir not in sys.path:
            sys.path.insert(0, str(config.workdir))
        self.module = importlib.import_module(config.posfile)

    def tasks(self):
        desc = dict()
        for name in _tasks:
            task = _tasks[name]
            if task.__doc__ is not None:
                desc[name] = task.__doc__.split('\n')[0].strip()
            else:
                desc[name] = ''
        sigs = dict()
        for name in _tasks:
            task = _tasks[name]
            sigs[name] = name + str(inspect.signature(task))
        nlen = 0
        for name in sigs:
            if len(sigs[name]) > nlen:
                nlen = len(sigs[name])
        lines = list()
        for name in sorted(sigs):
            description = desc[name]
            signature = sigs[name]
            line = f"{signature:{nlen}} {description}"
            lines.append(line)
        return '\n'.join(lines)


class Application:
    def __init__(self, config, inventory, posfile):
        self.config = config
        self.inventory = inventory
        self.posfile = posfile
        global _application
        assert _application is None
        _application = self

    def run(self):
        name = self.config.task
        args = self.config.args
        if name is None:
            raise PossibleApplicationError(f"Task must be defined in command line or in configuration file '{self.config.workdir/self.config.config}'")
        if name not in _tasks:
            raise PossibleApplicationError(f"Task '{name}' not found in posfile '{self.posfile.posfile}'")
        task = _tasks[name]
        signature = inspect.signature(task)
        if len(signature.parameters) != len(args):
            raise PossibleApplicationError(f"Task '{task}' expect {len(signature.parameters)} parameters, but {len(self.config.args)} parameters given")
        task(*args)

