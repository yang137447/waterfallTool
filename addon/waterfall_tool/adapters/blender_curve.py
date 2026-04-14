from __future__ import annotations

from ..core.types import TrajectoryPoint


def _set_follow_parent(obj, parent) -> None:
    if parent is None:
        return
    obj.parent = parent
    obj.matrix_parent_inverse = parent.matrix_world.inverted()
    obj.matrix_world = parent.matrix_world


def create_or_update_flow_curve(context, name: str, points: list[TrajectoryPoint], *, parent=None):
    import bpy
    import mathutils

    curve_obj = bpy.data.objects.get(name)
    if _can_reuse_flow_curve_object(curve_obj):
        curve_data = curve_obj.data
        curve_data.splines.clear()
    else:
        curve_data = bpy.data.curves.new(name=name, type="CURVE")
        curve_data.dimensions = "3D"
        curve_obj = bpy.data.objects.new(name, curve_data)
        context.collection.objects.link(curve_obj)

    _set_follow_parent(curve_obj, parent)

    if points:
        spline = curve_data.splines.new("POLY")
        spline.points.add(max(0, len(points) - 1))
        world_to_local = curve_obj.matrix_world.inverted()
        for spline_point, trajectory_point in zip(spline.points, points, strict=True):
            local_position = world_to_local @ mathutils.Vector(trajectory_point.position)
            x, y, z = local_position
            spline_point.co = (x, y, z, 1.0)

    curve_obj["waterfall_flow_curve"] = True
    curve_obj["waterfall_speed_cache"] = [point.speed for point in points]
    return curve_obj


def _can_reuse_flow_curve_object(curve_obj) -> bool:
    if curve_obj is None:
        return False
    if getattr(curve_obj, "type", None) != "CURVE":
        return False
    if not curve_obj.get("waterfall_flow_curve"):
        return False
    curve_data = getattr(curve_obj, "data", None)
    return hasattr(curve_data, "splines")


def read_flow_curve_points(curve_obj) -> tuple[list[tuple[float, float, float]], list[float]]:
    if not curve_obj.data.splines:
        return ([], [])

    positions = _read_evaluated_curve_positions(curve_obj)
    if not positions:
        spline = curve_obj.data.splines[0]
        spline_points = getattr(spline, "points", None)
        if spline_points is None:
            return ([], [])
        for spline_point in spline_points:
            world = curve_obj.matrix_world @ spline_point.co.to_3d()
            positions.append(tuple(world))

    speeds = _interpolate_speed_cache(curve_obj.get("waterfall_speed_cache", []), len(positions))
    return (positions, speeds)


def _read_evaluated_curve_positions(curve_obj) -> list[tuple[float, float, float]]:
    try:
        import bpy
    except ModuleNotFoundError:
        return []

    if not hasattr(curve_obj, "evaluated_get"):
        return []
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = curve_obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        return [tuple(curve_obj.matrix_world @ vertex.co) for vertex in mesh.vertices]
    finally:
        evaluated.to_mesh_clear()


def _interpolate_speed_cache(speed_cache, count: int) -> list[float]:
    if count <= 0:
        return []
    if not speed_cache:
        return [1.0] * count
    speeds = [float(speed) for speed in speed_cache]
    if len(speeds) == 1:
        return [speeds[0]] * count
    if len(speeds) == count:
        return speeds

    last_index = len(speeds) - 1
    result: list[float] = []
    for index in range(count):
        t = 0.0 if count == 1 else index / (count - 1)
        sample_index = t * last_index
        low = int(sample_index)
        high = min(last_index, low + 1)
        local_t = sample_index - low
        value = speeds[low] + (speeds[high] - speeds[low]) * local_t
        result.append(value)
    return result
