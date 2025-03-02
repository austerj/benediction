from abc import ABC


class BenedictionError(Exception, ABC):
    ...


# errors raised by / related to the application layer
class ApplicationError(BenedictionError):
    ...


# errors raised by / related to layouts
class LayoutError(BenedictionError):
    ...


class FrameError(LayoutError):
    ...


class FrameConstraintError(FrameError):
    ...


class InsufficientSpaceError(LayoutError):
    ...


class UnboundWindowError(LayoutError):
    ...


# errors raised by / related to nodes
class NodeError(BenedictionError):
    ...


class NodeFrameError(NodeError, FrameError):
    ...


# errors raised by / related to windows
class WindowError(BenedictionError):
    ...


class WindowOverflowError(WindowError):
    ...


class WindowNotInitializedError(WindowError):
    ...


# errors raised by / related to styles
class StyleError(BenedictionError):
    ...


class ColorError(StyleError):
    ...


# errors raised by space allocation solver
class SolverError(BenedictionError):
    ...


# errors related to screen
class ScreenError(BenedictionError):
    ...
