import pytest

from benediction.core.layout import Column, Row


@pytest.fixture
def nodes():
    root = Row([Column([Row(), Row()]), Column()])
    return root


def test_transpose(nodes):
    assert [n.orientation for n in nodes.flatten()] == ["row", "col", "row", "row", "col"]

    # transpose with depth 0 only flips the first node
    nodes.transpose(0)
    assert [n.orientation for n in nodes.flatten()] == ["col", "col", "row", "row", "col"]

    # transpose with depth 1 flips the first two levels
    nodes.transpose(1)
    assert [n.orientation for n in nodes.flatten()] == ["row", "row", "row", "row", "row"]

    # transpose with depth -1 flips all nodes
    nodes.transpose(-1)
    assert [n.orientation for n in nodes.flatten()] == ["col", "col", "col", "col", "col"]
