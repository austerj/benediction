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


@pytest.fixture
def sized_nodes():
    # depth 0
    root = Node()
    # depth 1
    node_0 = Node(root)
    node_0.cframe.frame.set_dimensions(6, 1, 7, 7)
    # depth 2
    node_0_0 = Node(node_0)
    node_0_0.cframe.frame.set_dimensions(1, 2, 5, 5)
    node_0_1 = Node(node_0)
    node_0_2 = Node(node_0)
    node_0_2.cframe.frame.set_dimensions(12, 7, 2, 2)
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


def test_update_frame(sized_nodes):
    # NOTE: easiest way to verify the validity of these tests is by writing out the layout in a
    # spreadsheet and mark each cell with the node that contains it

    # initial frame is not ready
    assert not sized_nodes.frame.is_ready

    # update dimensions to smallest region that contains all children
    sized_nodes.update_frame()

    # new dimensions are as expected (containing all children)
    assert sized_nodes.frame.top_abs == 1
    assert sized_nodes.frame.left_abs == 1
    assert sized_nodes.frame.right_abs == 8
    assert sized_nodes.frame.bottom_abs == 13
    assert sized_nodes.frame.width_outer == 8
    assert sized_nodes.frame.height_outer == 13

    # updating frame of depth 1 node overwrites the existing frame
    node_0 = sized_nodes.children[0]
    node_0.update_frame()
    assert node_0.frame.top_abs == 1
    assert node_0.frame.left_abs == 2
    assert node_0.frame.right_abs == 8
    assert node_0.frame.bottom_abs == 13
    assert node_0.frame.width_outer == 7
    assert node_0.frame.height_outer == 13

    # original frame hasn't been updated yet
    assert sized_nodes.frame.width_outer == 8
    # after updating it will match the depth 1 boundary
    sized_nodes.update_frame()
    assert sized_nodes.frame.width_outer == 7
