from __future__ import annotations

import typing
from dataclasses import dataclass, field

from benediction.core.node import Node
from benediction.style.style import Style, WindowStyleKwargs


class LayoutKwargs(WindowStyleKwargs):
    style: typing.NotRequired[Style | typing.Literal["default"]]
    # margins
    m: typing.NotRequired[int | float | None]
    my: typing.NotRequired[int | float | None]
    mx: typing.NotRequired[int | float | None]
    mt: typing.NotRequired[int | float | None]
    mb: typing.NotRequired[int | float | None]
    ml: typing.NotRequired[int | float | None]
    mr: typing.NotRequired[int | float | None]
    # padding
    p: typing.NotRequired[int | float | None]
    py: typing.NotRequired[int | float | None]
    px: typing.NotRequired[int | float | None]
    pt: typing.NotRequired[int | float | None]
    pb: typing.NotRequired[int | float | None]
    pl: typing.NotRequired[int | float | None]
    pr: typing.NotRequired[int | float | None]


class RowKwargs(LayoutKwargs):
    h: typing.NotRequired[int | float | None]
    min_h: typing.NotRequired[int | float | None]
    max_h: typing.NotRequired[int | float | None]
    gap_x: typing.NotRequired[int | float | None]


class ColumnKwargs(LayoutKwargs):
    w: typing.NotRequired[int | float | None]
    min_w: typing.NotRequired[int | float | None]
    max_w: typing.NotRequired[int | float | None]
    gap_y: typing.NotRequired[int | float | None]


class LayoutNodeKwargs(RowKwargs, ColumnKwargs):
    ...


@dataclass(slots=True, repr=False)
class LayoutNode(Node):
    """Node that forms part of a row-column layout with top-down control of dimensions."""

    is_row: bool = field(kw_only=True)
    kwargs: LayoutNodeKwargs = field(default_factory=LayoutNodeKwargs)

    def __repr__(self):
        return f"{'Row' if self.is_row else 'Column'}({', '.join([str(c) if isinstance(c, LayoutNode) else '...' for c in self.children])})"

    @property
    def is_col(self) -> bool:
        return not (self.is_row)

    @property
    def orientation(self) -> typing.Literal["row", "col"]:
        """Current orientation of the LayoutNode ('row' or 'col')."""
        return "row" if self.is_row else "col"

    def transpose(self, depth: int = 0):
        """Flip orientation of all LayoutNodes until depth has been reached."""

        def flip_orientation(node: Node):
            if isinstance(node, LayoutNode):
                node.is_row = not node.is_row

        self.apply(flip_orientation, depth)

    def update_frame(self, top: int, left: int, height: int, width: int):
        """Update the Frame dimensions of all child nodes."""
        # TODO


# TBD
@dataclass(slots=True, repr=False)
class LayoutRoot(LayoutNode):
    """Root node of a row-column layout."""

    ...
