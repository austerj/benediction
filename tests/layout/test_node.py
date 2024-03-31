import pytest

from benediction.core.layout.node import Node


@pytest.fixture
def nodes():
    # depth 0
    root = Node()
    # depth 1
    node_0 = Node(root)
    node_1 = Node(root)
    # depth 2
    node_0_0 = Node(node_0)
    node_0_1 = Node(node_0)
    node_0_2 = Node(node_0)
    node_1_0 = Node(node_1)
    node_1_1 = Node(node_1)
    # depth 3
    node_1_1_0 = Node(node_1_1)
    node_1_1_1 = Node(node_1_1)
    return root


def test_apply(nodes):
    # function passed to apply is called recursively by each child node
    i = 0

    def increment(node):
        nonlocal i
        i += 1

    nodes.apply(increment)
    assert i == 10


def test_flatten(nodes):
    # flattened node has expected number of elements
    assert len(nodes.flatten(0)) == 1
    assert len(nodes.flatten(1)) == 3
    assert len(nodes.flatten(2)) == 8
    assert len(nodes.flatten(3)) == 10
