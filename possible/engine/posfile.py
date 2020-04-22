
__all__ = ['Posfile']

import importlib
import sys

from possible.engine.exceptions import PossiblePosfileError
from possible.engine import runtime


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
        description = dict()
        for name in runtime.tasks:
            task = runtime.tasks[name]
            if task.__doc__ is not None:
                description[name] = task.__doc__.strip().split('\n')[0].strip()
            else:
                description[name] = ''
        nlen = len(max(runtime.tasks.keys(), key=len))
        lines = list()
        for name in runtime.tasks:
            lines.append(f"{name:{nlen}} # {description[name]}")
        lines.sort()
        return '\n'.join(lines)
