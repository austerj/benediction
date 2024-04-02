from __future__ import annotations

import typing
from dataclasses import dataclass

from benediction import errors
from benediction.core.node import Node
from benediction.core.node.layout import Column, LayoutNode, Row
from benediction.core.node.spec import ColumnSpecKwargs, NodeSpecKwargs, RowSpecKwargs
from benediction.core.window import AbstractWindow


@dataclass(slots=True)
class LayoutNodeFactory:
    """Intermediary factory object for nested LayoutNodes."""

    _parent: LayoutNodeFactory | None
    node: LayoutNode
    _last_added: LayoutNode | None = None

    def end(self):
        """End subdivision and step back in the layout hierarchy."""
        # short-hand for consistent notation in method chaining when wanting to go back to the
        # parent level following subdivision of a sub-item; e.g. adding more root columns after
        # subdividing a row of a root column
        return self.parent

    @property
    def parent(self):
        if self._parent is None:
            raise errors.LayoutError("Layout root reached: cannot access parent.")
        return self._parent

    @property
    def last_added(self):
        if self._last_added is None:
            raise errors.LayoutError("Cannot subdivide: no Nodes have been added.")
        return self._last_added

    def col(self, window: AbstractWindow | None = None, **kwargs: typing.Unpack[ColumnSpecKwargs]):
        """Add new column with fixed or dynamic width."""
        if self.node.is_col:
            # adding col from a col node => appending a col to the parent column (and moving back)
            self.parent.col(window, **kwargs)
            return self.parent
        else:
            # adding col from row node => append a col to the row node
            new_col = Column(**kwargs).bind(window)
            self._last_added = new_col
            self.node.append(new_col)
        return self

    def row(
        self,
        window: AbstractWindow | None = None,
        **kwargs: typing.Unpack[RowSpecKwargs],
    ):
        """Add new row with fixed or dynamic height."""
        if self.node.is_row:
            # adding row from a row node => appending a row to the parent column (and moving back)
            self.parent.row(window, **kwargs)
            return self.parent
        else:
            # adding row from column node => append a row to the column node
            new_row = Row(**kwargs).bind(window)
            self._last_added = new_row
            self.node.append(new_row)
        return self

    def subd(self):
        """Subdivide latest Node."""
        return LayoutNodeFactory(self, self.last_added)


class Layout:
    """Partitioning of a region into a responsive layout of nested rows and columns."""

    def __init__(
        self,
        __node_window: AbstractWindow | None = None,
        **kwargs: typing.Unpack[NodeSpecKwargs],
    ):
        self.__node = None
        self.__node_window = __node_window
        self.kwargs = kwargs

    def __repr__(self):
        return f"{self.__class__.__name__}({self.node if self.__node is not None else ''})"

    def row(self, window: AbstractWindow | None = None, **kwargs: typing.Unpack[RowSpecKwargs]):
        """Subdivide layout into rows via chained methods."""
        if self.__node is None:
            self.__node = Column(**self.kwargs).bind(self.__node_window)
        elif self.__node.is_row:
            raise errors.LayoutError("Cannot add row to row-major layout.")
        return LayoutNodeFactory(None, self.node).row(window, **kwargs)

    def col(self, window: AbstractWindow | None = None, **kwargs: typing.Unpack[ColumnSpecKwargs]):
        """Subdivide layout into columns via chained methods."""
        if self.__node is None:
            self.__node = Row(**self.kwargs).bind(self.__node_window)
        elif self.__node.is_col:
            raise errors.LayoutError("Cannot add column to column-major layout.")
        return LayoutNodeFactory(None, self.node).col(window, **kwargs)

    @property
    def node(self) -> LayoutNode:
        if self.__node is None:
            raise errors.LayoutError("No root node in layout - add a node with 'col' or 'row' methods.")
        return self.__node

    @property
    def order(self):
        """Order of layout (row / column major)."""
        return self.node.orientation

    @typing.overload
    def __getitem__(self, __i: typing.SupportsIndex) -> Node:
        ...

    @typing.overload
    def __getitem__(self, __s: slice) -> list[Node]:
        ...

    def __getitem__(self, i):
        return self.node.__getitem__(i)
