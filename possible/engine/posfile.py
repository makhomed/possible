
__all__ = ['Posfile']

import importlib
import sys

from .exceptions import PossiblePosfileError
from .runtime import tasks

class Posfile:
    def __init__(self, config):
        posfile = config.workdir / 'posfile.py'
        if not posfile.exists() or not posfile.is_file():
            raise PossiblePosfileError(f"Posfile '{posfile}' not exists")
        self.posfile = posfile
        if config.workdir not in sys.path:
            sys.path.insert(0, str(config.workdir))
        self.module = importlib.import_module('posfile')

    def list_of_tasks(self):
        desc = dict()
        for name in tasks:
            task = tasks[name]
            if task.__doc__ is not None:
                desc[name] = task.__doc__.split('\n')[0].strip()
            else:
                desc[name] = ''
        nlen = 0
        for name in tasks:
            if len(name) > nlen:
                nlen = len(name)
        lines = list()
        for name in tasks:
            description = desc[name]
            line = f"{name:{nlen}} # {description}"
            lines.append(line)
        lines.sort()
        return '\n'.join(lines)

