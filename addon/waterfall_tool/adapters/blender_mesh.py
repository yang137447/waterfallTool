from __future__ import annotations

from ..core.types import MeshData


def _set_follow_parent(obj, parent) -> None:
    if parent is None:
        return
    if obj.parent == parent:
        return
    obj.parent = parent
    obj.matrix_parent_inverse = parent.matrix_world.inverted()
    obj.matrix_world = parent.matrix_world


def create_or_update_mesh_object(context, name: str, mesh_data: MeshData, *, generated: bool = True, parent=None):
    import bpy
    import mathutils

    obj = bpy.data.objects.get(name)
    if _can_reuse_generated_mesh_object(obj):
        blender_mesh = obj.data
        blender_mesh.clear_geometry()
    else:
        blender_mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, blender_mesh)
        context.collection.objects.link(obj)

    _set_follow_parent(obj, parent)

    world_to_local = obj.matrix_world.inverted()
    local_vertices = [tuple(world_to_local @ mathutils.Vector(vertex)) for vertex in mesh_data.vertices]

    blender_mesh.from_pydata(local_vertices, [], mesh_data.faces)
    blender_mesh.update()
    _clear_uv_layers(blender_mesh)

    if mesh_data.uv0:
        uv0 = blender_mesh.uv_layers.new(name="UV0")
        _write_uv_layer(uv0, mesh_data.uv0)

    obj["waterfall_generated"] = generated
    return obj


def _can_reuse_generated_mesh_object(obj) -> bool:
    if obj is None:
        return False
    if getattr(obj, "type", None) != "MESH":
        return False
    if not obj.get("waterfall_generated"):
        return False
    mesh = getattr(obj, "data", None)
    return all(hasattr(mesh, attr) for attr in ("clear_geometry", "from_pydata", "uv_layers"))


def _clear_uv_layers(blender_mesh):
    while len(blender_mesh.uv_layers):
        blender_mesh.uv_layers.remove(blender_mesh.uv_layers[0])


def _write_uv_layer(layer, face_uvs):
    loop_index = 0
    for face in face_uvs:
        for uv in face:
            layer.data[loop_index].uv = uv
            loop_index += 1
