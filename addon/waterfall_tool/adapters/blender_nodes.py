from __future__ import annotations

import bpy


def ensure_waterfall_node_group():
    group = bpy.data.node_groups.get("WFT_RibbonSheet")
    if group is not None:
        return group

    group = bpy.data.node_groups.new("WFT_RibbonSheet", "GeometryNodeTree")
    group.interface.new_socket(
        name="Geometry",
        in_out="INPUT",
        socket_type="NodeSocketGeometry",
    )
    group.interface.new_socket(
        name="Geometry",
        in_out="OUTPUT",
        socket_type="NodeSocketGeometry",
    )
    input_node = group.nodes.new("NodeGroupInput")
    output_node = group.nodes.new("NodeGroupOutput")
    group.links.new(input_node.outputs[0], output_node.inputs[0])
    return group
