from abc import ABC


class HexesError(Exception, ABC):
    ...


class InsufficientSpaceError(HexesError):
    ...


class WindowNotInitializedError(HexesError):
    ...


class UnboundWindowError(HexesError):
    ...
