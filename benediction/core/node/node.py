from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from dataclasses import InitVar, dataclass, field

from benediction import errors
from benediction.core.frame import ConstrainedFrame
from benediction.core.node.spec import NodeSpec, NodeSpecKwargs


@dataclass(slots=True, repr=False)
class Node(ABC):
    """Object that forms part of a hierarchy of relations to parent and child Nodes."""

    # relational nodes
    parent: Node | None = field(default=None, init=False)
    children: list[Node] = field(default_factory=list)
    # NodeSpec governing constraints on frames and allocation of space to child Nodes
    spec: NodeSpec = field(init=False, repr=False)
    spec_kwargs: InitVar[NodeSpecKwargs | None] = field(default=None, kw_only=True)
    # constrained frame
    cframe: ConstrainedFrame = field(init=False, repr=False)

    def __post_init__(self, spec_kwargs: NodeSpecKwargs | None):
        self.spec = NodeSpec.from_kwargs(**spec_kwargs) if spec_kwargs else NodeSpec.default
        self.cframe = ConstrainedFrame.from_spec(self.spec)
        # TODO (?): .move(old_parent, new_parent) that removes node from list in old parent
        for node in self.children:
            node.parent = self

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join([str(c) for c in self.children])})"

    @typing.overload
    def __getitem__(self, __i: typing.SupportsIndex) -> Node:
        ...

    @typing.overload
    def __getitem__(self, __s: slice) -> list[Node]:
        ...

    def __getitem__(self, i):
        return self.children.__getitem__(i)

    @property
    def frame(self):
        """Inner Frame associated with Node."""
        return self.cframe.frame

    def append(self, node: Node):
        """Append a new child Node."""
        self.children.append(node)
        node.parent = self

    def apply(self, fn: typing.Callable[[Node], typing.Any], depth: int = -1, to_self: bool = True):
        """Apply function to (optional) self and all child Nodes recursively."""
        if to_self:
            fn(self)
        # break on 0 depth => continue indefinitely if depth<0
        if depth == 0:
            return
        # apply to every child at decremented depth
        for child in self.children:
            child.apply(fn, depth - 1)

    def flatten(self, depth: int = -1, include_self: bool = True):
        """Get flattened list of child Nodes."""
        nodes = []
        self.apply(lambda node: nodes.append(node), depth, include_self)
        return nodes

    @abstractmethod
    def update_frame(
        self,
        top: int | None = None,
        left: int | None = None,
        height: int | None = None,
        width: int | None = None,
        *args,
        **kwargs,
    ):
        """Update the Frame dimensions of the Node."""
        raise NotImplementedError


# NOTE: this node type is mainly intended for building "last-depth" components, i.e. nodes that have
# a small / static number of children - layouts should be built with LayoutNodes, which uses a
# top-down approach to allocation of frames (defining available space at the root node) instead of a
# bottoms-up approach that relies on explicitly setting frame dimensions on child nodes
@dataclass(slots=True, repr=False)
class ContainerNode(Node):
    """Node object with dimensions dictated by its children."""

    def update_frame(
        self,
        top: int | None = None,
        left: int | None = None,
        height: int | None = None,
        width: int | None = None,
    ):
        """Update frame to the smallest region that contains the given dimensions and all child Nodes."""
        # NOTE: this is a bottoms-up approach - basically, assume the child nodes have dealt with
        # their frames explicitly and infer the boundary from them, ignoring all constraints (since
        # we are not working relative to an outer frame)
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
            raise errors.NodeFrameError("Could not infer container dimensions.")
