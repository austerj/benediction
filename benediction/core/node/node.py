from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from dataclasses import InitVar, dataclass, field

from benediction import errors
from benediction.core.frame import ConstrainedFrame
from benediction.core.node.spec import NodeSpec, NodeSpecKwargs
from benediction.core.window import AbstractWindow
from benediction.style.style import Style, WindowStyleKwargs


@dataclass(slots=True, repr=False)
class Node(ABC):
    """Object that forms part of a hierarchy of relations to parent and child Nodes."""

    # relational nodes
    parent: Node | None = field(default=None, init=False)
    children: list[Node] = field(default_factory=list)
    # NodeSpec governing styling, constraints on frames and allocation of space to child Nodes
    spec: NodeSpec = field(init=False)
    spec_kwargs: InitVar[NodeSpecKwargs | None] = field(default=None, kw_only=True)
    # constrained frame
    cframe: ConstrainedFrame = field(init=False, repr=False)
    # caching style to get inheritance at access-time + avoid recursively deriving Styles
    __cached_style: Style | None = field(default=None, init=False)
    # window mapped to Node frame
    _window: AbstractWindow | None = field(default=None, init=False)

    def __post_init__(self, spec_kwargs: NodeSpecKwargs | None):
        # set spec and frame
        spec_kwargs = {} if spec_kwargs is None else spec_kwargs
        self.spec = NodeSpec.from_kwargs(**spec_kwargs)
        self.cframe = ConstrainedFrame.from_spec(self.spec)

        # iterating over nodes followed by (unique) parents => only one assignment per parent
        # NOTE: using ids should be okay to use as proxy for unique objects here since it shouldn't
        # be possible for any of these objects to not stay alive (and have their ids replaced)
        parent_to_children: dict[int, list[int]] = {}
        parents: list[Node] = []
        for node in self.children:
            if (old_parent := node.parent) is not None:
                # add to dict
                if (parent_id := id(old_parent)) not in parent_to_children:
                    parent_to_children[parent_id] = [id(node)]
                    parents.append(old_parent)
                else:
                    parent_to_children[parent_id].append(id(node))
            # update parent of reassigned node
            node.parent = self
        # remove ids from parents
        for parent in parents:
            removed_ids = set(parent_to_children[id(parent)])
            parent.children = [node for node in parent.children if id(node) not in removed_ids]

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

    def __contains__(self, node: Node):
        # compare by id (i.e. by memory - NOT equality) - use with caution
        node_id = id(node)
        return any(node_id == id(child) for child in self.children)

    @property
    def frame(self):
        """Inner Frame associated with Node."""
        return self.cframe.frame

    @property
    def style(self):
        """Style object associated with Node."""
        # NOTE: caching allows for inheriting at access time and protects us against exponential
        # growth in recursively inheriting from parent Nodes (at the cost of dealing with
        # invalidation when styles change)
        if getattr(self, "_Node__cached_style", None) is not None:
            return self.__cached_style
        # construct Style from spec if not found in cache
        parent_style = self.parent.style if self.parent is not None else None
        derived_style = self.spec.derive_style(parent_style)
        # cache derived Style and return
        self.__cached_style = derived_style
        return derived_style

    def update_style(self, **kwargs: typing.Unpack[WindowStyleKwargs]):
        """Update Style and invalidate cached child styles."""
        # update style kwargs in spec
        self.spec = self.spec.update_style(**kwargs)
        # invalidate all cached styles (that may have derived from replaced Style)
        self.apply(lambda node: delattr(node, "_Node__cached_style"))
        return self

    def append(self, node: Node):
        """Append a new child Node."""
        if node in self.children:
            raise errors.NodeError("Cannot append Node: is already a child.")
        self.children.append(node)
        # remove from old parent
        if (old_parent := node.parent) is not None:
            for i, parent_node in enumerate(old_parent.children):
                if node is parent_node:
                    old_parent.children.pop(i)
                    break
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

    def bind(self, window: AbstractWindow | None):
        """Bind AbstractWindow to Node."""
        self._window = window
        return self

    @property
    def window(self):
        """AbstractWindow mapped to Node Frame."""
        if self._window is None:
            raise errors.UnboundWindowError("Window must be bound to Node before being accessed.")
        return self._window

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
