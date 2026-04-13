from __future__ import annotations

from math import cos, radians, sin

from .curve_sampling import compute_width, resample_polyline
from .frames import build_frames
from .types import MeshData, MeshSettings, TrajectoryPoint, Vector3
from .vector_math import add, scale


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


def build_x_card_mesh(points: list[TrajectoryPoint], settings: MeshSettings) -> MeshData:
    samples = resample_polyline(points, settings.base_segment_density, settings.curvature_refine_strength)
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
