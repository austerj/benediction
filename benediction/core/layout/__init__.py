import typing

import benediction.core.layout.layout as _layout
from benediction.core.node import Node


# wrapper to pass kwargs as dict to LayoutNode constructor
def LayoutNode(children: list[Node] = [], is_row: bool = True, **kwargs: typing.Unpack[_layout.LayoutNodeKwargs]):
    return _layout.LayoutNode(children, is_row=is_row, kwargs=kwargs)


# wrappers for LayoutNode constructor with initial row / column config and appropriate kwarg hints
def Row(children: list[Node] = [], **kwargs: typing.Unpack[_layout.RowKwargs]):
    return LayoutNode(children, is_row=True, **kwargs)


def Column(children: list[Node] = [], **kwargs: typing.Unpack[_layout.ColumnKwargs]):
    return LayoutNode(children, is_row=False, **kwargs)
