from __future__ import annotations

from dataclasses import replace
from math import acos, ceil, pi

from .types import CurveSample, MeshSettings, TrajectoryPoint
from .vector_math import EPSILON, dot, length, lerp, normalize, sub


def compute_width(settings: MeshSettings, normalized_t: float) -> float:
    t = min(1.0, max(0.0, normalized_t))
    shaped = t ** max(0.001, settings.width_falloff)
    return settings.start_width + (settings.end_width - settings.start_width) * shaped


def _segment_curvature(points: list[TrajectoryPoint], index: int) -> float:
    if index <= 0 or index >= len(points) - 1:
        return 0.0
    incoming = normalize(sub(points[index].position, points[index - 1].position))
    outgoing = normalize(sub(points[index + 1].position, points[index].position))
    return acos(min(1.0, max(-1.0, dot(incoming, outgoing))))


def _curvature_density_multiplier(curvature: float, strength: float, max_multiplier: float) -> float:
    normalized_curvature = min(1.0, max(0.0, curvature / pi))
    boost = 1.0 + normalized_curvature * max(0.0, strength)
    upper_bound = max(1.0, max_multiplier)
    return min(upper_bound, max(1.0, boost))


def resample_polyline(
    points: list[TrajectoryPoint],
    base_segment_density: float,
    curvature_refine_strength: float,
    curvature_density_max_multiplier: float = 4.0,
) -> list[CurveSample]:
    if not points:
        return []

    collapsed_points: list[TrajectoryPoint] = []
    for point in points:
        if not collapsed_points or length(sub(point.position, collapsed_points[-1].position)) > EPSILON:
            collapsed_points.append(point)
        else:
            collapsed_points[-1] = replace(point, position=collapsed_points[-1].position)

    if len(collapsed_points) == 1:
        point = collapsed_points[0]
        return [CurveSample(position=point.position, tangent=(0.0, 0.0, -1.0), speed=point.speed, arc_length=0.0, t=0.0)]
    points = collapsed_points

    segment_lengths: list[float] = []
    total_length = 0.0
    for index in range(len(points) - 1):
        segment_length = length(sub(points[index + 1].position, points[index].position))
        segment_lengths.append(segment_length)
        total_length += segment_length

    samples: list[CurveSample] = []
    walked = 0.0
    for index, segment_length in enumerate(segment_lengths):
        a = points[index]
        b = points[index + 1]
        tangent = normalize(sub(b.position, a.position))
        curvature = max(_segment_curvature(points, index), _segment_curvature(points, index + 1))
        density_multiplier = _curvature_density_multiplier(
            curvature,
            curvature_refine_strength,
            curvature_density_max_multiplier,
        )
        density = max(0.01, base_segment_density) * density_multiplier
        steps = max(1, int(ceil(segment_length * density)))

        for step in range(steps + 1):
            if index > 0 and step == 0:
                continue
            local_t = step / steps
            arc_length = walked + segment_length * local_t
            normalized_t = 0.0 if total_length <= 1.0e-8 else arc_length / total_length
            speed = a.speed + (b.speed - a.speed) * local_t
            samples.append(
                CurveSample(
                    position=lerp(a.position, b.position, local_t),
                    tangent=tangent,
                    speed=speed,
                    arc_length=arc_length,
                    t=normalized_t,
                )
            )
        walked += segment_length

    return samples
