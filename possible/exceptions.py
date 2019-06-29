
__all__ = ['PossibleError', 'PossibleConfigError', 'PossibleInventoryError', 'PossiblePosfileError', 'PossibleApplicationError', 'PossibleRuntimeError']

class PossibleError(Exception): pass

class PossibleConfigError(PossibleError): pass

class PossibleInventoryError(PossibleError): pass

class PossiblePosfileError(PossibleError): pass

class PossibleApplicationError(PossibleError): pass

class PossibleRuntimeError(PossibleError): pass

