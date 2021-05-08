
__all__ = ['Posfile']

import importlib
import sys
import os

from possible.engine.exceptions import PossiblePosfileError
from possible.engine import runtime


class Posfile:
    def __init__(self, config):
        posfile = config.workdir / 'posfile.py'
        if not posfile.is_file():
            if config.workdir.stem == 'inventory' or config.workdir.stem == 'files':
                parent_dir = config.workdir.parents[0]
                config.workdir = parent_dir
                posfile = config.workdir / 'posfile.py'
                os.chdir(config.workdir)
        if not posfile.is_file():
            raise PossiblePosfileError(f"Posfile '{posfile}' not exists")
        self.posfile = posfile
        if config.workdir not in sys.path:
            sys.path.insert(0, str(config.workdir))
        self.module = importlib.import_module('posfile')

    def list_of_tasks(self):
        description = dict()
        for task_name in runtime.tasks:
            task = runtime.tasks[task_name]
            if task.__doc__ is not None:
                description[task_name] = task.__doc__.strip().split('\n')[0].strip()
            else:
                description[task_name] = task_name.replace('-', ' ')
        nlen = len(max(runtime.tasks.keys(), key=len))
        all_lines = dict()
        for task_name in runtime.tasks:
            all_lines[task_name]=f"{task_name:{nlen}} = {description[task_name]}"

        lines_by_group = dict()
        for task_name in runtime.tasks:
            group = runtime.groups.get(task_name, '')
            if group not in lines_by_group:
                lines_by_group[group] = list()
            lines_by_group[group].append(all_lines[task_name])
        out = list()
        out.append('')
        for group in sorted(lines_by_group.keys()):
            if group:
                out.append('[' + group + ']')
            lines_by_group[group].sort()
            for line in lines_by_group[group]:
                 out.append(line)
            out.append('')

        return '\n'.join(out)
        



#        lines.sort()
#        return '\n'.join(lines)
