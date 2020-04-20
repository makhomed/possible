
__all__ = ['Application']

from possible.engine.exceptions import PossibleUserError
from possible.engine.runtime import _tasks, _funcs_permissions, _func_defaults
from possible.engine.runtime import _hosts  # noqa: F401


class Application:

    def __init__(self, config, posfile, inventory):
        self.config = config
        self.posfile = posfile
        self.inventory = inventory

    def get_task(self, task_name):
        if task_name not in _tasks:
            raise PossibleUserError(f"Task '{task_name}' not found in posfile '{self.posfile.posfile}'.")
        return _tasks[task_name]

    def get_hosts(self, task_name):
        target = self.config.args.target
        if target is None:
            func_name = _tasks[task_name].__name__
            if func_name in _func_defaults:
                target = _func_defaults[func_name]
        if target is None:
            result = []
        elif target in self.inventory.hosts:
            result = [target]
        elif target in self.inventory.groups:
            result = list(self.inventory.groups[target].hosts)
        else:
            raise PossibleUserError(f"Target '{target}' not found in inventory '{self.inventory.inventory}'.")
        result.sort()
        global _hosts
        _hosts.extend(result[:])
        return result

    def check_all_permissions(self):
        for task_name in _tasks:
            func_name = _tasks[task_name].__name__
            if func_name not in _funcs_permissions:
                _funcs_permissions[func_name] = set()
            for permission in _funcs_permissions[func_name]:
                if permission not in self.inventory.hosts and permission not in self.inventory.groups:
                    raise PossibleUserError(f"Unknown permission '{permission}' in @allow list of task '{task_name}'.")

    def check_permissions(self, task_name, target_hosts):
        allowed_hosts = set()
        func_name = _tasks[task_name].__name__
        for permission in _funcs_permissions[func_name]:
            if permission in self.inventory.hosts:
                allowed_hosts.add(permission)
            else:
                allowed_hosts.update(self.inventory.groups[permission].hosts)
        for host in target_hosts:
            if host not in allowed_hosts:
                raise PossibleUserError(f"Target host '{host}' not allowed for task '{task_name}', permission denied.")

    def run(self):
        task_name = self.config.args.task
        task = self.get_task(task_name)
        target_hosts = self.get_hosts(task_name)
        self.check_all_permissions()
        self.check_permissions(task_name, target_hosts)
        task(target_hosts)
