
__all__ = ['Application']

from .exceptions import PossibleUserError
from .runtime import tasks, hosts

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

    def run(self):
        self.get_task()(self.get_hosts())

