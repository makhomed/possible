
__all__ = ['PossibleError', 'PossibleConfigError', 'PossibleConfigWarning', 'PossibleInventoryError', 'PossibleInventoryWarning']

class PossibleError(Exception): pass

class PossibleConfigError(PossibleError): pass

class PossibleConfigWarning(UserWarning): pass

class PossibleInventoryError(PossibleError): pass

class PossibleInventoryWarning(UserWarning): pass

