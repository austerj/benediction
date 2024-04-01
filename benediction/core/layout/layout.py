from __future__ import annotations

import typing
from dataclasses import dataclass, field

from benediction.core.node import Node


@dataclass(slots=True, repr=False)
class LayoutNode(Node):
    """Node that forms part of a row-column layout with top-down control of dimensions."""

    is_row: bool = field(kw_only=True)
    # gap to add between items
    gap_x: int | float | None = None
    gap_y: int | float | None = None

    def __repr__(self):
        return f"{'Row' if self.is_row else 'Column'}({', '.join([str(c) if isinstance(c, LayoutNode) else '...' for c in self.children])})"

    @property
    def is_col(self) -> bool:
        return not (self.is_row)

    @property
    def orientation(self) -> typing.Literal["row", "col"]:
        return "row" if self.is_row else "col"

    def transpose(self, depth: int = 0):
        """Flip orientation of all LayoutNodes until depth has been reached."""

        def flip_orientation(node: Node):
            if isinstance(node, LayoutNode):
                node.is_row = not (node.is_row)

        self.apply(flip_orientation, depth)

    def update_frame(self, top: int, left: int, height: int, width: int):
        """Update ConstrainedFrame of self and all child nodes."""
        # TODO


# TBD
@dataclass(slots=True, repr=False)
class LayoutRoot(LayoutNode):
    """Root node of a row-column layout."""

    ...


# wrappers for LayoutNode constructor with initial row / column config
# TODO: RowKwargs / ColumnKwargs (and handle kwargs in LayoutNode post_init)
def Row(children: list[Node] = [], gap_x: int | float | None = None):
    return LayoutNode(children=children, gap_x=gap_x, is_row=True)


def Column(children: list[Node] = [], gap_y: int | float | None = None):
    return LayoutNode(children=children, gap_y=gap_y, is_row=False)
