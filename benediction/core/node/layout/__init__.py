import typing

from benediction.core.node.layout.layout import LayoutNode
from benediction.core.node.node import Node
from benediction.core.node.spec import ColumnSpecKwargs, RowSpecKwargs


# wrappers for LayoutNode constructor with initial row / column config and appropriate kwarg hints
def Row(children: list[Node] | None = None, **kwargs: typing.Unpack[RowSpecKwargs]):
    return LayoutNode(children if children is not None else [], is_row=True, spec_kwargs=kwargs)  # type: ignore


def Column(children: list[Node] | None = None, **kwargs: typing.Unpack[ColumnSpecKwargs]):
    return LayoutNode(children if children is not None else [], is_row=False, spec_kwargs=kwargs)  # type: ignore
