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

    spline = curve_obj.data.splines[0]
    positions = _read_evaluated_curve_positions(curve_obj)
    spline_points = getattr(spline, "points", None)
    if spline_points is not None:
        if not positions:
            for spline_point in spline_points:
                world = curve_obj.matrix_world @ spline_point.co.to_3d()
                positions.append(tuple(world))
    else:
        bezier_positions = _read_bezier_curve_positions(curve_obj, spline)
        bezier_points = list(getattr(spline, "bezier_points", ()))
        if bezier_positions and (not positions or len(positions) <= len(bezier_points)):
            positions = bezier_positions
        if not positions:
            return ([], [])

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
        matrix_world = getattr(evaluated, "matrix_world", curve_obj.matrix_world)
        return [tuple(matrix_world @ vertex.co) for vertex in mesh.vertices]
    finally:
        evaluated.to_mesh_clear()


def _read_bezier_curve_positions(curve_obj, spline) -> list[tuple[float, float, float]]:
    bezier_points = list(getattr(spline, "bezier_points", ()))
    if not bezier_points:
        return []

    resolution = max(1, int(getattr(spline, "resolution_u", getattr(curve_obj.data, "resolution_u", 12))))
    cyclic = bool(getattr(spline, "use_cyclic_u", False))
    segment_count = len(bezier_points) if cyclic else len(bezier_points) - 1
    if segment_count <= 0:
        world = curve_obj.matrix_world @ bezier_points[0].co
        return [tuple(world)]

    positions: list[tuple[float, float, float]] = []
    for segment_index in range(segment_count):
        start = bezier_points[segment_index]
        end = bezier_points[(segment_index + 1) % len(bezier_points)]
        for step in range(resolution + 1):
            if segment_index > 0 and step == 0:
                continue
            t = step / resolution
            point = _sample_cubic_bezier(
                start.co,
                start.handle_right,
                end.handle_left,
                end.co,
                t,
            )
            world = curve_obj.matrix_world @ point
            positions.append(tuple(world))
    return positions


def _sample_cubic_bezier(p0, p1, p2, p3, t: float):
    one_minus_t = 1.0 - t
    x0, y0, z0 = tuple(p0)
    x1, y1, z1 = tuple(p1)
    x2, y2, z2 = tuple(p2)
    x3, y3, z3 = tuple(p3)
    return type(p0)(
        (
            x0 * (one_minus_t ** 3)
            + x1 * (3.0 * one_minus_t * one_minus_t * t)
            + x2 * (3.0 * one_minus_t * t * t)
            + x3 * (t ** 3),
            y0 * (one_minus_t ** 3)
            + y1 * (3.0 * one_minus_t * one_minus_t * t)
            + y2 * (3.0 * one_minus_t * t * t)
            + y3 * (t ** 3),
            z0 * (one_minus_t ** 3)
            + z1 * (3.0 * one_minus_t * one_minus_t * t)
            + z2 * (3.0 * one_minus_t * t * t)
            + z3 * (t ** 3),
        )
    )


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
