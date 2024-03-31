from __future__ import annotations

import typing
from dataclasses import dataclass, field

from benediction.core.layout.frame import ConstrainedFrame


@dataclass(slots=True, repr=False)
class Node:
    """Object that forms a hierarchy of relations to parent and child Nodes."""

    # relational nodes
    parent: Node | None = None
    children: list[Node] = field(default_factory=list)
    # constrained frame
    _cframe: ConstrainedFrame = field(default_factory=ConstrainedFrame, init=False)

    def __post_init__(self):
        if self.parent:
            self.parent.children.append(self)

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join([str(c) for c in self.children])})"

    @property
    def frame(self):
        """Inner Frame associated with Node."""
        return self._cframe.frame

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

    def flatten(self, depth: int = -1):
        """Get flattened list of layout nodes."""
        nodes = []
        self.apply(lambda node: nodes.append(node), depth)
        return nodes
