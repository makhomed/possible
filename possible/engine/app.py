
__all__ = ['Application']

from .exceptions import PossibleUserError
from .runtime import _hosts, _tasks, _task_names_to_func_names, _funcs_permissions


class Application:

    def __init__(self, config, posfile, inventory):
        self.config = config
        self.posfile = posfile
        self.inventory = inventory


    def get_task(self, task_name):
        if task_name not in _tasks:
            raise PossibleUserError(f"Task '{task}' not found in posfile '{self.posfile.posfile}'.")
        return _tasks[task_name]


    def get_hosts(self):
        global _hosts 
        target = self.config.args.target
        if target is None:
            result = []
        elif target in self.inventory.hosts:
            result = [target]
        elif target in self.inventory.groups:
            result = list(self.inventory.groups[target].hosts)
        else:
            raise PossibleUserError(f"Target '{target}' not found in inventory '{self.inventory.inventory}'.")
        result.sort()
        _hosts.extend(result[:])
        return result


    def check_all_permissions(self):
        for task_name in _tasks:
            func_name = _task_names_to_func_names[task_name]
            if func_name not in _funcs_permissions:
                _funcs_permissions[func_name] = set()
            for permission in _funcs_permissions[func_name]:
                if permission not in self.inventory.hosts and permission not in self.inventory.groups:
                    raise PossibleUserError(f"Unknown permission '{permission}' in @allow list of task '{task_name}'.")


    def check_permissions(self, task_name, target_hosts):
        allowed_hosts = set()
        func_name = _task_names_to_func_names[task_name]
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
        target_hosts = self.get_hosts()
        self.check_all_permissions()
        self.check_permissions(task_name, target_hosts)
        task(target_hosts)

