
__all__ = ['PossibleError', 'PossibleConfigError', 'PossibleInventoryError']

class PossibleError(Exception): pass

class PossibleConfigError(PossibleError): pass

class PossibleInventoryError(PossibleError): pass

