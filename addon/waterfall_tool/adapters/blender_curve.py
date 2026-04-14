from __future__ import annotations

from ..core.types import TrajectoryPoint


def create_or_update_flow_curve(context, name: str, points: list[TrajectoryPoint]):
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
    spline = curve_obj.data.splines[0]
    spline_points = getattr(spline, "points", None)
    if spline_points is None:
        return ([], [])
    speed_cache = list(curve_obj.get("waterfall_speed_cache", []))
    positions = []
    speeds = []
    for index, spline_point in enumerate(spline_points):
        world = curve_obj.matrix_world @ spline_point.co.to_3d()
        positions.append(tuple(world))
        speeds.append(float(speed_cache[index]) if index < len(speed_cache) else 1.0)
    return (positions, speeds)
