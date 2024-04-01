import pytest

from benediction.core.node import Column, Row


@pytest.fixture
def nodes():
    root = Row([Column([Row(), Row()]), Column()])
    return root


@pytest.fixture
def styled_nodes():
    root = Row([Column([Row(style="default"), Row()], bold=True), Column()], italic=True)
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


def test_style_inheritance(styled_nodes):
    assert styled_nodes.style.italic
    # first column inherits italic flag
    assert styled_nodes[0].style.italic and styled_nodes[0].style.bold
    # first column inherits italic flag (but is not bold)
    assert styled_nodes[1].style.italic and not styled_nodes[1].style.bold
    # first row of first column has styles overwritten to default
    assert not styled_nodes[0][0].style.italic and not styled_nodes[0][0].style.bold
    # second row inherits both bold and italic flag
    assert styled_nodes[0][1].style.italic and styled_nodes[0][1].style.bold

    # updating spec triggers invalidation of child caches
    styled_nodes.update_style(italic=False, blink=True)
    assert not styled_nodes.style.italic and styled_nodes.style.blink
    assert not styled_nodes[0].style.italic and styled_nodes[0].style.blink and styled_nodes[0].style.bold
