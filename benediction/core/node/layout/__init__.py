import typing

from benediction.core.node.layout.layout import LayoutNode as _LayoutNode
from benediction.core.node.node import Node
from benediction.core.node.spec import ColumnSpecKwargs, NodeSpecKwargs, RowSpecKwargs


# wrapper to pass kwargs as dict to LayoutNode constructor
def LayoutNode(children: list[Node] | None = None, is_row: bool = True, **kwargs: typing.Unpack[NodeSpecKwargs]):
    return _LayoutNode(children if children is not None else [], is_row=is_row, spec_kwargs=kwargs)


# wrappers for LayoutNode constructor with initial row / column config and appropriate kwarg hints
def Row(children: list[Node] | None = None, **kwargs: typing.Unpack[RowSpecKwargs]):
    return LayoutNode(children if children is not None else [], is_row=True, **kwargs)


def Column(children: list[Node] | None = None, **kwargs: typing.Unpack[ColumnSpecKwargs]):
    return LayoutNode(children if children is not None else [], is_row=False, **kwargs)
