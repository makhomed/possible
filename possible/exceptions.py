
__all__ = ['PossibleError', 'PossibleConfigError', 'PossibleConfigWarning', 'PossibleInventoryError']

class PossibleError(Exception): pass

class PossibleConfigError(PossibleError): pass

class PossibleInventoryError(PossibleError): pass

class PossibleConfigWarning(UserWarning): pass

