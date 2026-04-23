from __future__ import annotations

from math import cos, exp, radians, sin

from .curve_sampling import compute_width, resample_polyline
from .frames import build_frames
from .types import CurveSample, MeshData, MeshSettings, TrajectoryPoint, Vector3
from .vector_math import add, length, lerp, normalize, scale, sub


def _rotate_in_frame(normal: Vector3, binormal: Vector3, angle_degrees: float) -> Vector3:
    angle = radians(angle_degrees)
    return add(scale(normal, cos(angle)), scale(binormal, sin(angle)))


def _build_strip_specs(settings: MeshSettings) -> tuple[tuple[float, bool], ...]:
    primary_strip = (settings.cross_angle_degrees, False)
    cross_strip = (0.0, True)
    return (primary_strip, cross_strip) if settings.enable_cross_strip else (primary_strip,)


def _find_cross_ramp_start_arc_length(samples: list[CurveSample]) -> float:
    if not samples:
        return 0.0
    for index in range(1, len(samples)):
        previous_attached = samples[index - 1].surface_normal is not None
        current_attached = samples[index].surface_normal is not None
        if previous_attached and not current_attached:
            return samples[index].arc_length
    return samples[0].arc_length


def _cross_ramp_weight(sample: CurveSample, settings: MeshSettings, ramp_start_arc_length: float) -> float:
    if settings.cross_ramp_length <= 1.0e-8:
        return 1.0
    t = (sample.arc_length - ramp_start_arc_length) / settings.cross_ramp_length
    t = max(0.0, min(1.0, t))
    # Smoothstep: slow start near the lip and full width after transition length.
    return t * t * (3.0 - 2.0 * t)


def _build_expansion_widths(samples: list[CurveSample], settings: MeshSettings) -> list[float]:
    accumulated_expansion = 0.0
    expansion_widths: list[float] = []
    if not samples:
        return expansion_widths

    expansion_widths.append(0.0)
    for i in range(1, len(samples)):
        prev_sample = samples[i - 1]
        curr_sample = samples[i]

        delta_time = 0.0
        avg_speed = (prev_sample.speed + curr_sample.speed) * 0.5
        if avg_speed > 1.0e-4:
            dist = curr_sample.arc_length - prev_sample.arc_length
            delta_time = dist / avg_speed

        speed_increase = max(0.0, curr_sample.speed - prev_sample.speed)
        expansion_step = speed_increase * settings.speed_expansion * delta_time
        accumulated_expansion += expansion_step
        expansion_widths.append(accumulated_expansion)

    return expansion_widths


def _end_face_max_z(
    sample: CurveSample,
    frame,
    expansion_width: float,
    settings: MeshSettings,
    strip_specs: tuple[tuple[float, bool], ...],
    ramp_start_arc_length: float,
) -> float:
    result = sample.position[2]
    for strip_angle, is_cross_strip in strip_specs:
        width_multiplier = settings.cross_width_scale if is_cross_strip else 1.0
        if is_cross_strip:
            width_multiplier *= _cross_ramp_weight(sample, settings, ramp_start_arc_length)
        half_width = compute_width(settings, sample.t, expansion_width) * 0.5 * width_multiplier
        axis = _rotate_in_frame(frame.normal, frame.binormal, strip_angle)
        result = max(result, sample.position[2] + abs(axis[2]) * half_width)
    return result


def _extend_points_until_end_face_is_below_cutoff_plane(
    points: list[TrajectoryPoint],
    cutoff_height: float,
    settings: MeshSettings,
) -> list[TrajectoryPoint]:
    if len(points) < 2:
        return points

    strip_specs = _build_strip_specs(settings)
    overrun = max(0.25, float(settings.longitudinal_step_length))

    working = list(points)
    for _ in range(8):
        samples = resample_polyline(
            working,
            settings.longitudinal_step_length,
            settings.curvature_min_angle_degrees,
        )
        if len(samples) < 2:
            return working

        frames = build_frames(samples)
        expansion_widths = _build_expansion_widths(samples, settings)
        ramp_start_arc_length = _find_cross_ramp_start_arc_length(samples)
        last_max_z = _end_face_max_z(samples[-1], frames[-1], expansion_widths[-1], settings, strip_specs, ramp_start_arc_length)
        if last_max_z <= cutoff_height - 1.0e-6:
            return working

        dz_needed = (last_max_z - cutoff_height) + overrun
        last = working[-1]
        prev = working[-2]
        direction = normalize(last.velocity) if length(last.velocity) > 1.0e-8 else normalize(sub(last.position, prev.position))
        if length(direction) <= 1.0e-8 or direction[2] >= -1.0e-4:
            direction = (0.0, 0.0, -1.0)
        distance = dz_needed / max(1.0e-4, -direction[2])
        new_position = add(last.position, scale(direction, distance))
        working.append(
            TrajectoryPoint(
                position=new_position,
                velocity=last.velocity,
                speed=last.speed,
                attached=last.attached,
            )
        )

    return working


def _build_speed_stretched_v(points: list[TrajectoryPoint], samples: list[CurveSample], base_speed: float, speed_smoothing_length: float) -> list[float]:
    if not points or not samples:
        return []

    reference_speed = max(1.0e-4, base_speed)
    smoothing_length = max(0.0, speed_smoothing_length)

    point_distances = [0.0]
    point_v = [0.0]

    accumulated_d = 0.0
    accumulated_v = 0.0
    inv_speed_state = 1.0 / max(1.0e-4, points[0].speed)

    for index in range(len(points) - 1):
        start = points[index]
        end = points[index + 1]
        segment_length = length(sub(end.position, start.position))
        accumulated_d += segment_length

        segment_speed = max(1.0e-4, (start.speed + end.speed) * 0.5)
        inv_speed = 1.0 / segment_speed
        if smoothing_length > 0.0:
            alpha = 1.0 - exp(-max(0.0, segment_length) / max(1.0e-8, smoothing_length))
            inv_speed_state = inv_speed_state + (inv_speed - inv_speed_state) * alpha
            inv_speed = inv_speed_state

        accumulated_v += segment_length * reference_speed * inv_speed
        point_distances.append(accumulated_d)
        point_v.append(accumulated_v)

    total_length = point_distances[-1]
    if total_length <= 1.0e-8:
        return [0.0 for _ in samples]

    stretched_v: list[float] = []
    seg_index = 0
    last_seg = len(point_distances) - 2
    for sample in samples:
        target_d = max(0.0, min(total_length, float(sample.arc_length)))
        while seg_index < last_seg and point_distances[seg_index + 1] < target_d:
            seg_index += 1
        d0 = point_distances[seg_index]
        d1 = point_distances[seg_index + 1]
        t = 0.0 if (d1 - d0) <= 1.0e-8 else (target_d - d0) / (d1 - d0)
        stretched_v.append(point_v[seg_index] + (point_v[seg_index + 1] - point_v[seg_index]) * t)

    return stretched_v


def _interpolate_sample(a: CurveSample, b: CurveSample, t: float, global_t: float) -> CurveSample:
    tangent = normalize(lerp(a.tangent, b.tangent, t))
    if length(tangent) <= 1.0e-8:
        tangent = b.tangent if length(b.tangent) > 1.0e-8 else a.tangent
        
    surface_normal = None
    if a.surface_normal is not None and b.surface_normal is not None:
        surface_normal = normalize(lerp(a.surface_normal, b.surface_normal, t))
        if length(surface_normal) <= 1.0e-8:
            surface_normal = b.surface_normal if length(b.surface_normal) > 1.0e-8 else a.surface_normal
    elif a.surface_normal is not None:
        surface_normal = a.surface_normal
    elif b.surface_normal is not None:
        surface_normal = b.surface_normal

    return CurveSample(
        position=lerp(a.position, b.position, t),
        tangent=tangent,
        speed=a.speed + (b.speed - a.speed) * t,
        arc_length=a.arc_length + (b.arc_length - a.arc_length) * t,
        t=global_t,
        surface_normal=surface_normal,
    )


def _row_vertex_index(strip_start: int, row_stride: int, sample_index: int, column_index: int) -> int:
    return strip_start + sample_index * row_stride + column_index


def _clip_polygon_against_cutoff_plane(
    vertices: list[Vector3],
    indices: list[int],
    uvs: list[tuple[float, float]],
    cutoff_height: float,
    edge_cache: dict[tuple[int, int], tuple[int, float]],
) -> list[tuple[int, tuple[float, float]]]:
    if not indices or len(indices) != len(uvs):
        return []

    eps = 1.0e-8

    def inside(vertex_index: int) -> bool:
        return vertices[vertex_index][2] >= cutoff_height - eps

    def get_intersection(prev_idx: int, curr_idx: int, prev_uv: tuple[float, float], curr_uv: tuple[float, float]):
        key = (prev_idx, curr_idx) if prev_idx < curr_idx else (curr_idx, prev_idx)
        cached = edge_cache.get(key)
        if cached is None:
            low_idx, high_idx = key
            low = vertices[low_idx]
            high = vertices[high_idx]
            span = high[2] - low[2]
            t_low = 0.0 if abs(span) <= eps else (cutoff_height - low[2]) / span
            t_low = 0.0 if t_low < 0.0 else (1.0 if t_low > 1.0 else t_low)
            pos = lerp(low, high, t_low)
            pos = (pos[0], pos[1], cutoff_height)
            new_index = len(vertices)
            vertices.append(pos)
            edge_cache[key] = (new_index, t_low)
            cached = (new_index, t_low)

        new_index, t_low = cached
        t = t_low if prev_idx == key[0] else (1.0 - t_low)
        uv = (prev_uv[0] + (curr_uv[0] - prev_uv[0]) * t, prev_uv[1] + (curr_uv[1] - prev_uv[1]) * t)
        return new_index, uv

    output: list[tuple[int, tuple[float, float]]] = []
    prev_idx = indices[-1]
    prev_uv = uvs[-1]
    prev_inside = inside(prev_idx)

    for curr_idx, curr_uv in zip(indices, uvs, strict=True):
        curr_inside = inside(curr_idx)
        if curr_inside:
            if not prev_inside:
                output.append(get_intersection(prev_idx, curr_idx, prev_uv, curr_uv))
            output.append((curr_idx, curr_uv))
        elif prev_inside:
            output.append(get_intersection(prev_idx, curr_idx, prev_uv, curr_uv))

        prev_idx = curr_idx
        prev_uv = curr_uv
        prev_inside = curr_inside

    return output


def _clip_mesh_to_cutoff_plane(mesh: MeshData, cutoff_height: float) -> MeshData:
    if not mesh.vertices or not mesh.faces:
        return mesh

    vertices = list(mesh.vertices)
    faces: list[tuple[int, ...]] = []
    uv0: list[list[tuple[float, float]]] = []
    edge_cache: dict[tuple[int, int], tuple[int, float]] = {}

    if mesh.uv0:
        source = zip(mesh.faces, mesh.uv0, strict=True)
        for face, face_uvs in source:
            indices = list(face)
            clipped = _clip_polygon_against_cutoff_plane(vertices, indices, face_uvs, cutoff_height, edge_cache)
            if len(clipped) < 3:
                continue
            clipped_indices = [v[0] for v in clipped]
            clipped_uvs = [v[1] for v in clipped]
            if len(clipped_indices) == 3:
                faces.append((clipped_indices[0], clipped_indices[1], clipped_indices[2]))
                uv0.append([clipped_uvs[0], clipped_uvs[1], clipped_uvs[2]])
                continue
            if len(clipped_indices) == 4:
                faces.append((clipped_indices[0], clipped_indices[1], clipped_indices[2], clipped_indices[3]))
                uv0.append([clipped_uvs[0], clipped_uvs[1], clipped_uvs[2], clipped_uvs[3]])
                continue

            root_i = clipped_indices[0]
            root_uv = clipped_uvs[0]
            for k in range(1, len(clipped_indices) - 1):
                faces.append((root_i, clipped_indices[k], clipped_indices[k + 1]))
                uv0.append([root_uv, clipped_uvs[k], clipped_uvs[k + 1]])
    else:
        for face in mesh.faces:
            indices = list(face)
            clipped = _clip_polygon_against_cutoff_plane(vertices, indices, [(0.0, 0.0)] * len(indices), cutoff_height, edge_cache)
            if len(clipped) < 3:
                continue
            clipped_indices = [v[0] for v in clipped]
            if len(clipped_indices) == 3:
                faces.append((clipped_indices[0], clipped_indices[1], clipped_indices[2]))
                continue
            if len(clipped_indices) == 4:
                faces.append((clipped_indices[0], clipped_indices[1], clipped_indices[2], clipped_indices[3]))
                continue
            root_i = clipped_indices[0]
            for k in range(1, len(clipped_indices) - 1):
                faces.append((root_i, clipped_indices[k], clipped_indices[k + 1]))

    if not faces:
        return MeshData()

    used_indices = sorted({vertex_index for face in faces for vertex_index in face})
    remap = {old_index: new_index for new_index, old_index in enumerate(used_indices)}
    compact_vertices = [vertices[index] for index in used_indices]
    compact_faces = [tuple(remap[index] for index in face) for face in faces]

    return MeshData(vertices=compact_vertices, faces=compact_faces, uv0=uv0)


def build_x_card_mesh(points: list[TrajectoryPoint], settings: MeshSettings) -> MeshData:
    cutoff_height = settings.cutoff_height
    align_to_cutoff = bool(settings.align_end_to_cutoff_plane) and cutoff_height is not None
    if align_to_cutoff:
        points = _extend_points_until_end_face_is_below_cutoff_plane(points, float(cutoff_height), settings)

    samples = resample_polyline(
        points,
        settings.longitudinal_step_length,
        settings.curvature_min_angle_degrees,
    )
    if len(samples) < 2:
        return MeshData()

    frames = build_frames(samples)
    stretched_v = _build_speed_stretched_v(points, samples, settings.uv_base_speed, settings.uv_speed_smoothing_length)
    mesh = MeshData()
    strip_specs = _build_strip_specs(settings)
    cross_ramp_start_arc_length = _find_cross_ramp_start_arc_length(samples)
    row_stride = max(1, settings.width_density) + 1
    expansion_widths = _build_expansion_widths(samples, settings)

    for strip_angle, is_cross_strip in strip_specs:
        strip_start = len(mesh.vertices)
        base_width_multiplier = settings.cross_width_scale if is_cross_strip else 1.0

        for sample_index, (sample, frame, exp_width) in enumerate(zip(samples, frames, expansion_widths, strict=True)):
            width_multiplier = base_width_multiplier
            if is_cross_strip:
                width_multiplier *= _cross_ramp_weight(sample, settings, cross_ramp_start_arc_length)
            half_width = compute_width(settings, sample.t, exp_width) * 0.5 * width_multiplier
            axis = _rotate_in_frame(frame.normal, frame.binormal, strip_angle)
            for column in range(row_stride):
                u = 0.0 if row_stride == 1 else column / (row_stride - 1)
                offset = (-half_width) + (half_width * 2.0) * u
                vertex = add(sample.position, scale(axis, offset))
                mesh.vertices.append(vertex)

        for index in range(len(samples) - 1):
            start_v = stretched_v[index]
            end_v = stretched_v[index + 1]
            for column in range(row_stride - 1):
                a = _row_vertex_index(strip_start, row_stride, index, column)
                b = _row_vertex_index(strip_start, row_stride, index, column + 1)
                c = _row_vertex_index(strip_start, row_stride, index + 1, column + 1)
                d = _row_vertex_index(strip_start, row_stride, index + 1, column)
                mesh.faces.append((a, b, c, d))
                u0 = column / (row_stride - 1)
                u1 = (column + 1) / (row_stride - 1)
                mesh.uv0.append([(u0, start_v), (u1, start_v), (u1, end_v), (u0, end_v)])

    if align_to_cutoff:
        return _clip_mesh_to_cutoff_plane(mesh, float(cutoff_height))

    return mesh
