from __future__ import annotations

import typing
from dataclasses import dataclass, field

from benediction.core.layout.frame import ConstrainedFrame


@dataclass(slots=True, repr=False)
class Node:
    """Object that forms part of a hierarchy of relations to parent and child Nodes."""

    # relational nodes
    parent: Node | None = None
    children: list[Node] = field(default_factory=list)
    # constrained frame
    cframe: ConstrainedFrame = field(default_factory=ConstrainedFrame, init=False)

    def __post_init__(self):
        if self.parent:
            self.parent.children.append(self)

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join([str(c) for c in self.children])})"

    @property
    def frame(self):
        """Inner Frame associated with Node."""
        return self.cframe.frame

    def apply(self, fn: typing.Callable[[Node], typing.Any], depth: int = -1, to_self: bool = True):
        """Apply function to (optional) self and all child nodes recursively."""
        if to_self:
            fn(self)
        # break on 0 depth => continue indefinitely if depth<0
        if depth == 0:
            return
        # apply to every child at decremented depth
        for child in self.children:
            child.apply(fn, depth - 1)

    def flatten(self, depth: int = -1, include_self: bool = True):
        """Get flattened list of child nodes."""
        nodes = []
        self.apply(lambda node: nodes.append(node), depth, include_self)
        return nodes

    def update_frame(
        self,
        top: int | None = None,
        left: int | None = None,
        width: int | None = None,
        height: int | None = None,
    ):
        """Update frame to the smallest region that contains the given dimensions and all child nodes."""
        # NOTE: default behavior of the base node is a bottoms-up approach - basically, assume the
        # child nodes have dealt with their frames explicitly and infer the boundary from them,
        # ignoring all constraints (since we are not working relative to an outer frame)
        right, bottom = None, None

        def update_boundaries(node: Node):
            nonlocal top, left, right, bottom
            frame = node.frame
            # update running top/left/right/bottom boundaries
            if frame.is_ready:
                top = frame.top_abs if top is None or frame.top_abs < top else top
                left = frame.left_abs if left is None or frame.left_abs < left else left
                right = frame.right_abs if right is None or frame.right_abs > right else right
                bottom = frame.bottom_abs if bottom is None or frame.bottom_abs > bottom else bottom

        # update boundaries from recursion through child nodes
        self.apply(update_boundaries, to_self=False)
        width = width if right is None or left is None else (right - left) + 1
        height = height if top is None or bottom is None else (bottom - top) + 1

        if not any((top is None, left is None, width is None, height is None)):
            # update inner frame directly (ignoring constraints)
            self.cframe.frame.set_dimensions(top, left, height, width)  # type: ignore
        else:
            raise ValueError("WAAH")