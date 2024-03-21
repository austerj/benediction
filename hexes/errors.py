from abc import ABC


class HexesError(Exception, ABC):
    ...


class InsufficientSpaceError(HexesError):
    ...
