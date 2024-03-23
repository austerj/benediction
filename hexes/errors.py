from abc import ABC


class HexesError(Exception, ABC):
    ...


class InsufficientSpaceError(HexesError):
    ...


class WindowOverflowError(HexesError):
    ...


class WindowNotInitializedError(HexesError):
    ...


class UnboundWindowError(HexesError):
    ...


class LayoutError(HexesError):
    ...


class ColorError(HexesError):
    ...
