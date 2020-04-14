
__all__ = ['hosts']

from possible.engine import application
from possible.engine import PossibleUserError

def hosts(target):
    inventory = application.inventory
    if target in inventory.hosts:
        return [target]
    elif target in inventory.groups:
        result = list(inventory.groups[target].hosts)
        result.sort()
        return result
    else:
        raise PossibleUserError(f"Target '{target}' is not valid host or group name")

