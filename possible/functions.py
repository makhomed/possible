
__all__ = ['hosts']

from possible.engine import application
from possible.engine import PossibleRuntimeError

def hosts(target):
    inventory = application.inventory
    if target in inventory.hosts:
        return [target]
    elif target in inventory.groups:
        return list(inventory.groups[target].hosts)
    else:
        raise PossibleRuntimeError(f"Target '{target}' is not valid host or group name")

