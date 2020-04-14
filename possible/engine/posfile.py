
__all__ = ['Posfile']

import importlib
import inspect
import sys

from .app import application
from .exceptions import PossiblePosfileError

class Posfile:
    def __init__(self, config):
        posfile = config.workdir / 'posfile.py'
        if not posfile.exists() or not posfile.is_file():
            raise PossiblePosfileError(f"Posfile '{posfile}' not exists")
        self.posfile = posfile
        if config.workdir not in sys.path:
            sys.path.insert(0, str(config.workdir))
        self.module = importlib.import_module('posfile')

    def tasks(self):
        desc = dict()
        for name in application.tasks:
            task = application.tasks[name]
            if task.__doc__ is not None:
                desc[name] = task.__doc__.split('\n')[0].strip()
            else:
                desc[name] = ''
        sigs = dict()
        for name in application.tasks:
            task = application.tasks[name]
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

