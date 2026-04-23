from __future__ import annotations

try:
    import bpy
except ModuleNotFoundError:
    bpy = None


GUIDE_PREFIX = "__WaterfallCutoffGuide__"


def build_cutoff_outline(
    cutoff_height: float,
    offset_x: float,
    offset_y: float,
    size_x: float,
    size_y: float,
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int]]]:
    half_x = max(0.001, size_x) * 0.5
    half_y = max(0.001, size_y) * 0.5
    z = cutoff_height
    vertices = [
        (offset_x - half_x, offset_y - half_y, z),
        (offset_x + half_x, offset_y - half_y, z),
        (offset_x + half_x, offset_y + half_y, z),
        (offset_x - half_x, offset_y + half_y, z),
    ]
    edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
    return vertices, edges


def _guide_name(scene) -> str:
    return f"{GUIDE_PREFIX}{scene.name}"


def ensure_cutoff_guide(scene) -> None:
    if bpy is None or scene is None:
        return

    settings = getattr(scene, "waterfall_global", None)
    if settings is None:
        return

    guide_name = _guide_name(scene)

    obj = bpy.data.objects.get(guide_name)
    if obj is None:
        mesh = bpy.data.meshes.new(f"{guide_name}_Mesh")
        obj = bpy.data.objects.new(guide_name, mesh)
        scene.collection.objects.link(obj)
        obj["waterfall_cutoff_guide"] = True

    vertices, edges = build_cutoff_outline(
        settings.cutoff_height,
        settings.cutoff_offset_x,
        settings.cutoff_offset_y,
        settings.cutoff_size_x,
        settings.cutoff_size_y,
    )

    mesh = obj.data
    mesh.clear_geometry()
    mesh.from_pydata(vertices, edges, [])
    mesh.update()

    obj.display_type = "WIRE"
    obj.hide_render = True
    obj.hide_select = True
    obj.show_in_front = True
    obj.hide_viewport = not settings.show_cutoff_guide
