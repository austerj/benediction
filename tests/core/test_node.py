import pytest

from benediction import errors
from benediction.core.node import ContainerNode


@pytest.fixture
def nodes():
    # depth 0
    root = ContainerNode(
        [
            # depth 1
            node_0 := ContainerNode(
                [
                    # depth 2
                    node_0_0 := ContainerNode(),
                    node_0_1 := ContainerNode(),
                    node_0_2 := ContainerNode(),
                ]
            ),
            node_1 := ContainerNode(
                [
                    # depth 2
                    node_1_0 := ContainerNode(),
                    node_1_1 := ContainerNode(
                        [
                            # depth 3
                            node_1_1_0 := ContainerNode(),
                            node_1_1_1 := ContainerNode(),
                        ]
                    ),
                ]
            ),
        ]
    )
    return root


@pytest.fixture
def sized_nodes():
    # depth 0
    root = ContainerNode(
        [
            # depth 1
            node_0 := ContainerNode(
                [
                    # depth 2
                    node_0_0 := ContainerNode(),
                    node_0_1 := ContainerNode(),
                    node_0_2 := ContainerNode(),
                ]
            ),
        ]
    )
    node_0.cframe.frame.set_dimensions(6, 1, 7, 7)
    node_0_0.cframe.frame.set_dimensions(1, 2, 5, 5)
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
    sized_nodes[0].update_frame()
    assert sized_nodes[0].frame.top_abs == 1
    assert sized_nodes[0].frame.left_abs == 2
    assert sized_nodes[0].frame.right_abs == 8
    assert sized_nodes[0].frame.bottom_abs == 13
    assert sized_nodes[0].frame.width_outer == 7
    assert sized_nodes[0].frame.height_outer == 13

    # original frame hasn't been updated yet
    assert sized_nodes.frame.width_outer == 8
    # after updating it will match the depth 1 boundary
    sized_nodes.update_frame()
    assert sized_nodes.frame.width_outer == 7

    # cannot infer frame when no child nodes have frames defined
    unsized_nodes = ContainerNode([ContainerNode()])
    with pytest.raises(errors.NodeFrameError):
        unsized_nodes.update_frame()
    # ...but works if giving explicit dimensions
    unsized_nodes.update_frame(0, 0, 10, 5)
    assert unsized_nodes.frame.height == 10
    assert unsized_nodes.frame.width == 5


def test_parent_removal(sized_nodes):
    # child is in original node
    old_parent = sized_nodes
    child = old_parent[0]
    assert child in old_parent

    # moving a node to another parent removes it from the original
    new_parent = ContainerNode([child])
    assert child in new_parent
    assert child not in old_parent
