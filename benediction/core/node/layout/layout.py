from __future__ import annotations

import typing
from dataclasses import dataclass, field

from benediction import errors
from benediction._utils import Bounds, clip, to_abs
from benediction.core.node.layout.solver import SpaceAllocator
from benediction.core.node.node import Node


@dataclass(slots=True, repr=False)
class LayoutNode(Node):
    """Node that forms part of a row-column layout with top-down control of dimensions."""

    is_row: bool = field(kw_only=True)
    _solver: SpaceAllocator | None = field(default=None, init=False)

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
        if self.parent:
            p_frame = self.parent.frame
            height_outer, width_outer = p_frame.height_outer, p_frame.width_outer
        else:
            height_outer, width_outer = height, width

        top, left, height, width = self.cframe.set_dimensions(top, left, height, width, height_outer, width_outer)

        if not self.children:
            return

        start = left if self.is_row else top
        gap = to_abs(self.spec.gap_x if self.is_row else self.spec.gap_y, width if self.is_row else height)
        for node, space in self._allocate_space(width if self.is_row else height):
            node.update_frame(
                top if self.is_row else start,
                left if self.is_col else start,
                height if self.is_row else space,
                width if self.is_col else space,
            )
            start += space + gap

    def _allocate_space(self, space: int):
        """Compute allocated space for each item and return iterator of item-space pairs."""
        items = self.children
        spec = self.spec
        idx_to_space: dict[int, int] = {}

        allocated_space = 0
        implicit_items: list[tuple[int, Node, Bounds]] = []

        # subtract gaps from space - "added back" via shifts to positions in update()
        # TODO: generalize to distribution of items (e.g. justify, left, right etc.)
        gap = to_abs(spec.gap_x if self.is_row else spec.gap_y, space)
        space -= gap * max(len(items) - 1, 0)

        # allocate absolute and relative items
        for idx, item in enumerate(items):
            cframe = item.cframe
            item_space = cframe.width if self.is_row else cframe.height
            if isinstance(item_space, int):
                # absolute is simple - no bounds, always equals assigned value
                item_space = item_space
            else:
                bounds = cframe.width_bounds(space) if self.is_row else cframe.height_bounds(space)
                # delay allocation for implicit items
                if item_space is None:
                    implicit_items.append((idx, item, bounds))
                    continue
                # relative may have bounds
                item_space = clip(to_abs(item_space, space), bounds)
            # store in dict to retain mapping to original order
            idx_to_space[idx] = item_space
            allocated_space += item_space

        if allocated_space > space:
            raise errors.InsufficientSpaceError("Allocated more space than available.")

        # allocate implicit elements based on remaining space
        if implicit_items:
            bounds = tuple(item[2] for item in implicit_items)
            remaining_space = space - allocated_space

            # update solver if bounds have changed
            if not self._solver or self._solver.bounds != bounds:
                self._solver = SpaceAllocator(bounds)

            # solve for the constrained distribution of integers and add results to space dict
            implicit_items_space = self._solver.solve(remaining_space)
            if any(item_space <= 0 for item_space in implicit_items_space):
                raise errors.InsufficientSpaceError("Failed to allocate implicit space.")

            for i, (idx, _, _) in enumerate(implicit_items):
                idx_to_space[idx] = implicit_items_space[i]

        # return items and their allocated space for iteration
        return zip(self.children, (idx_to_space[i] for i in range(len(items))))
