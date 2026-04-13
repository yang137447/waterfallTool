from __future__ import annotations

from ..core.types import MeshData


def create_or_update_mesh_object(context, name: str, mesh_data: MeshData, *, generated: bool = True):
    import bpy

    obj = bpy.data.objects.get(name)
    if obj is None:
        blender_mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, blender_mesh)
        context.collection.objects.link(obj)
    else:
        blender_mesh = obj.data
        blender_mesh.clear_geometry()

    blender_mesh.from_pydata(mesh_data.vertices, [], mesh_data.faces)
    blender_mesh.update()

    if mesh_data.uv0:
        uv0 = blender_mesh.uv_layers.new(name="UV0")
        _write_uv_layer(uv0, mesh_data.uv0)
    if mesh_data.uv1:
        uv1 = blender_mesh.uv_layers.new(name="UV1_Speed")
        _write_uv_layer(uv1, mesh_data.uv1)

    obj["waterfall_generated"] = generated
    return obj


def _write_uv_layer(layer, face_uvs):
    loop_index = 0
    for face in face_uvs:
        for uv in face:
            layer.data[loop_index].uv = uv
            loop_index += 1
