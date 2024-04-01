import typing

import benediction.core.layout.layout as _layout
from benediction.core.node import Node
from benediction.core.spec import ColumnSpecKwargs, NodeSpecKwargs, RowSpecKwargs


# wrapper to pass kwargs as dict to LayoutNode constructor
def LayoutNode(children: list[Node] = [], is_row: bool = True, **kwargs: typing.Unpack[NodeSpecKwargs]):
    return _layout.LayoutNode(children, is_row=is_row, spec_kwargs=kwargs)


# wrappers for LayoutNode constructor with initial row / column config and appropriate kwarg hints
def Row(children: list[Node] = [], **kwargs: typing.Unpack[RowSpecKwargs]):
    return LayoutNode(children, is_row=True, **kwargs)


def Column(children: list[Node] = [], **kwargs: typing.Unpack[ColumnSpecKwargs]):
    return LayoutNode(children, is_row=False, **kwargs)
