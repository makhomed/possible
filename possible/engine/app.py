
__all__ = ['application']

import inspect

from .exceptions import PossibleApplicationError

class Application:
    def __init__(self):
        self.config = None
        self.inventory = None
        self.posfile = None
        self.tasks = dict()

    def run(self):
        name = self.config.task
        args = self.config.args
        if name is None:
            raise PossibleApplicationError(f"Task must be defined in command line or in configuration file '{self.config.workdir/self.config.config}'")
        if name not in self.tasks:
            raise PossibleApplicationError(f"Task '{name}' not found in posfile '{self.posfile.posfile}'")
        task = self.tasks[name]
        signature = inspect.signature(task)
        if len(signature.parameters) != len(args):
            raise PossibleApplicationError(f"Task '{task}' expect {len(signature.parameters)} parameters, but {len(self.config.args)} parameters given")
        task(*args)

application = Application()

