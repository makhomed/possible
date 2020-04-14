
__all__ = ['application']

import inspect

from .exceptions import PossibleUserError

class Application:
    def __init__(self):
        self.config = None
        self.posfile = None
        self.inventory = None
        self.tasks = dict()

    def run(self):
        name = self.config.args.task
        target = self.config.args.target
        if name is None:
            raise PossibleUserError("Task must be defined")
        if name not in self.tasks:
            raise PossibleUserError(f"Task '{name}' not found in posfile '{self.posfile.posfile}'")
        task = self.tasks[name]
        signature = inspect.signature(task)
        task(target)

application = Application()

