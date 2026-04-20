from __future__ import annotations

from math import ceil, cos, radians, sin

from .curve_sampling import compute_width, resample_polyline
from .frames import build_frames
from .types import CurveSample, MeshData, MeshSettings, TrajectoryPoint, Vector3
from .vector_math import add, length, lerp, normalize, scale


def _rotate_in_frame(normal: Vector3, binormal: Vector3, angle_degrees: float) -> Vector3:
    angle = radians(angle_degrees)
    return add(scale(normal, cos(angle)), scale(binormal, sin(angle)))


def _speed_range(speeds: list[float]) -> tuple[float, float]:
    if not speeds:
        return (0.0, 1.0)
    minimum = min(speeds)
    maximum = max(speeds)
    if abs(maximum - minimum) <= 1.0e-8:
        return (minimum, minimum + 1.0)
    return (minimum, maximum)


def _normalized_speed(speed: float, minimum: float, maximum: float, scale_value: float) -> float:
    value = (speed - minimum) / (maximum - minimum)
    return min(1.0, max(0.0, value * max(0.0, scale_value)))


def _target_point_count_from_faces(target_face_count: int) -> int:
    if target_face_count <= 0:
        return 0
    target_segments = max(1, int(ceil(target_face_count / 2.0)))
    return target_segments + 1


def _interpolate_sample(a: CurveSample, b: CurveSample, t: float, global_t: float) -> CurveSample:
    tangent = normalize(lerp(a.tangent, b.tangent, t))
    if length(tangent) <= 1.0e-8:
        tangent = b.tangent if length(b.tangent) > 1.0e-8 else a.tangent
    return CurveSample(
        position=lerp(a.position, b.position, t),
        tangent=tangent,
        speed=a.speed + (b.speed - a.speed) * t,
        arc_length=a.arc_length + (b.arc_length - a.arc_length) * t,
        t=global_t,
    )


def _retarget_curve_samples(samples: list[CurveSample], target_face_count: int) -> list[CurveSample]:
    target_points = _target_point_count_from_faces(target_face_count)
    if target_points <= 0 or len(samples) < 2 or len(samples) == target_points:
        return samples

    rebuilt: list[CurveSample] = []
    hi = 1
    for i in range(target_points):
        global_t = 0.0 if target_points == 1 else i / (target_points - 1)
        if global_t <= 0.0:
            rebuilt.append(samples[0])
            continue
        if global_t >= 1.0:
            rebuilt.append(samples[-1])
            continue

        while hi < len(samples) - 1 and samples[hi].t < global_t:
            hi += 1
        lo = hi - 1
        a = samples[lo]
        b = samples[hi]
        span = max(1.0e-8, b.t - a.t)
        local_t = (global_t - a.t) / span
        rebuilt.append(_interpolate_sample(a, b, local_t, global_t))
    return rebuilt


def _limit_curve_samples(samples: list[CurveSample], max_segment_count: int) -> list[CurveSample]:
    if max_segment_count <= 0:
        return samples

    target_points = max_segment_count + 1
    if len(samples) <= target_points:
        return samples

    last_index = len(samples) - 1
    picked_indices = []
    for i in range(target_points):
        raw = int(round(i * last_index / (target_points - 1)))
        if picked_indices and raw <= picked_indices[-1]:
            raw = min(last_index, picked_indices[-1] + 1)
        picked_indices.append(raw)
    picked_indices[-1] = last_index
    return [samples[index] for index in picked_indices]


def build_x_card_mesh(points: list[TrajectoryPoint], settings: MeshSettings) -> MeshData:
    samples = resample_polyline(
        points,
        settings.base_segment_density,
        settings.curvature_refine_strength,
        settings.curvature_density_max_multiplier,
    )
    samples = _retarget_curve_samples(samples, settings.target_face_count)
    samples = _limit_curve_samples(samples, settings.max_segment_count)
    if len(samples) < 2:
        return MeshData()

    frames = build_frames(samples)
    speed_min, speed_max = _speed_range([sample.speed for sample in samples])
    mesh = MeshData()
    strip_angles = (-settings.cross_angle_degrees * 0.5, settings.cross_angle_degrees * 0.5)

    for strip_angle in strip_angles:
        strip_start = len(mesh.vertices)
        for sample, frame in zip(samples, frames, strict=True):
            half_width = compute_width(settings, sample.t) * 0.5
            axis = _rotate_in_frame(frame.normal, frame.binormal, strip_angle)
            mesh.vertices.append(add(sample.position, scale(axis, -half_width)))
            mesh.vertices.append(add(sample.position, scale(axis, half_width)))

        for index in range(len(samples) - 1):
            a = strip_start + index * 2
            b = a + 1
            c = a + 3
            d = a + 2
            mesh.faces.append((a, b, c, d))
            start = samples[index]
            end = samples[index + 1]
            mesh.uv0.append([(0.0, start.arc_length), (1.0, start.arc_length), (1.0, end.arc_length), (0.0, end.arc_length)])
            start_speed = _normalized_speed(start.speed, speed_min, speed_max, settings.uv_speed_scale)
            end_speed = _normalized_speed(end.speed, speed_min, speed_max, settings.uv_speed_scale)
            mesh.uv1.append([(0.0, start_speed), (1.0, start_speed), (1.0, end_speed), (0.0, end_speed)])

    return mesh
