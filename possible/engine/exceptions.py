
class PossibleError(Exception):
    pass


class PossibleInventoryError(PossibleError):
    pass


class PossiblePosfileError(PossibleError):
    pass


class PossibleUserError(PossibleError):
    pass


class PossibleRuntimeError(PossibleError):
    pass


class PossibleFileNotFound(PossibleRuntimeError):
    pass
