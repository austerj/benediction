from abc import ABC


class HexesError(Exception, ABC):
    ...


# errors raised by / related to layouts
class LayoutError(HexesError):
    ...


class InsufficientSpaceError(LayoutError):
    ...


class UnboundWindowError(LayoutError):
    ...


# errors raised by / related to windows
class WindowError(HexesError):
    ...


class WindowOverflowError(WindowError):
    ...


class WindowNotInitializedError(WindowError):
    ...


# errors raised by / related to styles
class StyleError(HexesError):
    ...


class ColorError(StyleError):
    ...
