
__all__ = ['Application']

from .exceptions import PossibleUserError
from .runtime import hosts, tasks, tasks_names, tasks_permissions


class Application:

    def __init__(self, config, posfile, inventory):
        self.config = config
        self.posfile = posfile
        self.inventory = inventory


    def get_task(self):
        task = self.config.args.task
        if task not in tasks:
            raise PossibleUserError(f"Task '{task}' not found in posfile '{self.posfile.posfile}'")
        return tasks[task]


    def get_hosts(self):
        global hosts 
        target = self.config.args.target
        if target in self.inventory.hosts:
            result = [target]
        elif target in self.inventory.groups:
            result = list(self.inventory.groups[target].hosts)
        else:
            raise PossibleUserError(f"Target '{target}' not found in inventory '{self.inventory.inventory}'")
        result.sort()
        hosts.extend(result[:])
        return result


    def check_permissions(self, task_name, target_hosts):
        for pretty_name in tasks:
            if pretty_name in tasks_names:
                func_name = tasks_names[pretty_name]
            else:
                func_name = pretty_name
            if func_name not in tasks_permissions:
                tasks_permissions[func_name] = set()
            for permission in tasks_permissions[func_name]:
                if permission not in self.inventory.hosts and permission not in self.inventory.groups:
                    raise PossibleUserError(f"Unknown permission '{permission}' in @allow list of function '{func_name}'")

        if task_name in tasks_names:
            func_name = tasks_names[task_name]
        else:
            func_name = task_name

        allowed_hosts = set()
        for permission in tasks_permissions[func_name]:
            if permission in self.inventory.hosts:
                allowed_hosts.add(permission)
            else:
                allowed_hosts.update(self.inventory.groups[permission].hosts)

        for host in target_hosts:
            if host not in allowed_hosts:
                raise PossibleUserError(f"Target host '{host}' not allowed for task '{func_name}', permission denied.")


    def run(self):
        task_name = self.config.args.task
        task = self.get_task()
        target_hosts = self.get_hosts()
        self.check_permissions(task_name, target_hosts)
        task(target_hosts)

