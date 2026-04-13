from __future__ import annotations

from ..core.types import TrajectoryPoint


def create_or_update_flow_curve(context, name: str, points: list[TrajectoryPoint]):
    import bpy

    curve_obj = bpy.data.objects.get(name)
    if curve_obj is None:
        curve_data = bpy.data.curves.new(name=name, type="CURVE")
        curve_data.dimensions = "3D"
        curve_obj = bpy.data.objects.new(name, curve_data)
        context.collection.objects.link(curve_obj)
    else:
        curve_data = curve_obj.data
        curve_data.splines.clear()

    spline = curve_data.splines.new("POLY")
    spline.points.add(max(0, len(points) - 1))
    for spline_point, trajectory_point in zip(spline.points, points, strict=True):
        x, y, z = trajectory_point.position
        spline_point.co = (x, y, z, 1.0)

    curve_obj["waterfall_flow_curve"] = True
    curve_obj["waterfall_speed_cache"] = [point.speed for point in points]
    return curve_obj


def read_flow_curve_points(curve_obj) -> tuple[list[tuple[float, float, float]], list[float]]:
    if not curve_obj.data.splines:
        return ([], [])
    spline = curve_obj.data.splines[0]
    speed_cache = list(curve_obj.get("waterfall_speed_cache", []))
    positions = []
    speeds = []
    for index, spline_point in enumerate(spline.points):
        world = curve_obj.matrix_world @ spline_point.co.to_3d()
        positions.append(tuple(world))
        speeds.append(float(speed_cache[index]) if index < len(speed_cache) else 1.0)
    return (positions, speeds)
