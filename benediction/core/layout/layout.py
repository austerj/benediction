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
    gap_x: typing.NotRequired[int | float]


class ColumnKwargs(LayoutKwargs):
    w: typing.NotRequired[int | float | None]
    min_w: typing.NotRequired[int | float | None]
    max_w: typing.NotRequired[int | float | None]
    gap_y: typing.NotRequired[int | float]


class LayoutNodeKwargs(RowKwargs, ColumnKwargs):
    ...


@dataclass(slots=True, frozen=True)
class LayoutNodeSpec:
    """Attributes related to LayoutNode styling and space allocation."""

    # row
    h: int | float | None
    min_h: int | float | None
    max_h: int | float | None
    gap_x: int | float
    # column
    w: int | float | None
    min_w: int | float | None
    max_w: int | float | None
    gap_y: int | float
    # margins
    margin_top: int | float
    margin_bottom: int | float
    margin_left: int | float
    margin_right: int | float
    # padding
    padding_top: int | float
    padding_bottom: int | float
    padding_left: int | float
    padding_right: int | float
    # style
    style: Style

    @classmethod
    def from_kwargs(
        cls,
        # row
        h: int | float | None = None,
        min_h: int | float | None = None,
        max_h: int | float | None = None,
        gap_x: int | float = 0,
        # column
        w: int | float | None = None,
        min_w: int | float | None = None,
        max_w: int | float | None = None,
        gap_y: int | float = 0,
        # margins
        m: int | float | None = None,
        my: int | float | None = None,
        mx: int | float | None = None,
        mt: int | float | None = None,
        mb: int | float | None = None,
        ml: int | float | None = None,
        mr: int | float | None = None,
        # padding
        p: int | float | None = None,
        py: int | float | None = None,
        px: int | float | None = None,
        pt: int | float | None = None,
        pb: int | float | None = None,
        pl: int | float | None = None,
        pr: int | float | None = None,
        # style
        style: Style | typing.Literal["default"] = Style.default,
        **style_kwargs: typing.Unpack[WindowStyleKwargs],
    ):
        return cls(
            # row
            h,
            min_h,
            max_h,
            gap_x,
            # column
            w,
            min_w,
            max_w,
            gap_y,
            # margins with priority given to most specific keyword
            margin_top=mt if mt is not None else my if my is not None else m if m is not None else 0,
            margin_bottom=mb if mb is not None else my if my is not None else m if m is not None else 0,
            margin_left=ml if ml is not None else mx if mx is not None else m if m is not None else 0,
            margin_right=mr if mr is not None else mx if mx is not None else m if m is not None else 0,
            # padding with priority given to most specific keyword
            padding_top=pt if pt is not None else py if py is not None else p if p is not None else 0,
            padding_bottom=pb if pb is not None else py if py is not None else p if p is not None else 0,
            padding_left=pl if pl is not None else px if px is not None else p if p is not None else 0,
            padding_right=pr if pr is not None else px if px is not None else p if p is not None else 0,
            # style
            style=(Style.default if style == "default" else style).derive(**style_kwargs),
        )


@dataclass(slots=True, repr=False)
class LayoutNode(Node):
    """Node that forms part of a row-column layout with top-down control of dimensions."""

    is_row: bool = field(kw_only=True)
    spec: LayoutNodeSpec = field(kw_only=True, repr=False)

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
