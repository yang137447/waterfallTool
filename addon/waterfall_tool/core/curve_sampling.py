from __future__ import annotations

from math import acos, ceil

from .types import CurveSample, MeshSettings, TrajectoryPoint
from .vector_math import dot, length, lerp, normalize, sub


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


def resample_polyline(
    points: list[TrajectoryPoint],
    base_segment_density: float,
    curvature_refine_strength: float,
) -> list[CurveSample]:
    if not points:
        return []
    if len(points) == 1:
        point = points[0]
        return [CurveSample(position=point.position, tangent=(0.0, 0.0, -1.0), speed=point.speed, arc_length=0.0, t=0.0)]

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
        density = max(0.1, base_segment_density) * (1.0 + curvature * max(0.0, curvature_refine_strength))
        steps = max(1, int(ceil(segment_length * density)))

        for step in range(steps):
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

    final = points[-1]
    previous = points[-2]
    samples.append(
        CurveSample(
            position=final.position,
            tangent=normalize(sub(final.position, previous.position)),
            speed=final.speed,
            arc_length=total_length,
            t=1.0,
        )
    )
    return samples
