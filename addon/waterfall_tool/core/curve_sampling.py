from __future__ import annotations

from dataclasses import replace
from math import acos, ceil, degrees

from .types import CurveSample, MeshSettings, TrajectoryPoint
from .vector_math import EPSILON, dot, length, lerp, normalize, sub


def compute_width(settings: MeshSettings, normalized_t: float, expansion_width: float = 0.0) -> float:
    t = min(1.0, max(0.0, normalized_t))
    shaped = t ** max(0.001, settings.width_falloff)
    relative_scale = settings.start_width + (settings.end_width - settings.start_width) * shaped
    
    basis_width = max(0.001, settings.base_width + expansion_width)
    
    return basis_width * max(0.0, relative_scale)


def _segment_curvature(points: list[TrajectoryPoint], index: int) -> float:
    if index <= 0 or index >= len(points) - 1:
        return 0.0
    incoming = normalize(sub(points[index].position, points[index - 1].position))
    outgoing = normalize(sub(points[index + 1].position, points[index].position))
    return acos(min(1.0, max(-1.0, dot(incoming, outgoing))))


def _effective_step_length(curvature_radians: float, base_step_length: float, min_angle_degrees: float) -> float:
    base = max(0.001, base_step_length)
    angle_degrees = degrees(max(0.0, curvature_radians))
    threshold = max(0.1, min_angle_degrees)
    if angle_degrees <= threshold:
        return base
    scale = threshold / max(threshold, angle_degrees)
    return max(0.001, base * scale)


def _sample_tangent(samples: list[CurveSample], index: int) -> tuple[float, float, float]:
    if len(samples) == 1:
        return (0.0, 0.0, -1.0)

    if index <= 0:
        direction = sub(samples[1].position, samples[0].position)
    elif index >= len(samples) - 1:
        direction = sub(samples[-1].position, samples[-2].position)
    else:
        direction = sub(samples[index + 1].position, samples[index - 1].position)

    tangent = normalize(direction)
    if length(tangent) <= 1.0e-8:
        return (0.0, 0.0, -1.0)
    return tangent


def resample_polyline(
    points: list[TrajectoryPoint],
    longitudinal_step_length: float,
    curvature_min_angle_degrees: float,
) -> list[CurveSample]:
    if not points:
        return []

    # Filter out virtually identical points to avoid divide-by-zero
    collapsed_points: list[TrajectoryPoint] = []
    for point in points:
        if not collapsed_points or length(sub(point.position, collapsed_points[-1].position)) > EPSILON:
            collapsed_points.append(point)
        else:
            collapsed_points[-1] = replace(point, position=collapsed_points[-1].position)

    if len(collapsed_points) == 1:
        point = collapsed_points[0]
        return [CurveSample(position=point.position, tangent=(0.0, 0.0, -1.0), speed=point.speed, arc_length=0.0, t=0.0, surface_normal=point.surface_normal)]
    points = collapsed_points

    # Calculate cumulative arc lengths
    cum_lengths = [0.0]
    for i in range(len(points) - 1):
        cum_lengths.append(cum_lengths[-1] + length(sub(points[i + 1].position, points[i].position)))
    total_length = cum_lengths[-1]

    if total_length <= EPSILON:
        p0, p1 = points[0], points[-1]
        return [
            CurveSample(position=p0.position, tangent=(0.0, 0.0, -1.0), speed=p0.speed, arc_length=0.0, t=0.0, surface_normal=p0.surface_normal),
            CurveSample(position=p1.position, tangent=(0.0, 0.0, -1.0), speed=p1.speed, arc_length=total_length, t=1.0, surface_normal=p1.surface_normal)
        ]

    samples: list[CurveSample] = []
    target_d = 0.0
    current_idx = 0

    while target_d < total_length:
        while current_idx < len(points) - 1 and cum_lengths[current_idx + 1] < target_d:
            current_idx += 1
            
        if current_idx >= len(points) - 1:
            current_idx = len(points) - 2

        p1 = points[current_idx]
        p2 = points[current_idx + 1]
        seg_start = cum_lengths[current_idx]
        seg_len = cum_lengths[current_idx + 1] - seg_start

        t = 0.0 if seg_len <= EPSILON else (target_d - seg_start) / seg_len
        t = max(0.0, min(1.0, t))

        pos = lerp(p1.position, p2.position, t)
        speed = p1.speed + (p2.speed - p1.speed) * t

        n1 = p1.surface_normal
        n2 = p2.surface_normal
        surface_normal = None
        if n1 is not None and n2 is not None:
            surface_normal = normalize(lerp(n1, n2, t))
            if length(surface_normal) <= 1.0e-8:
                surface_normal = n2 if length(n2) > 1.0e-8 else n1
        elif n1 is not None:
            surface_normal = n1
        elif n2 is not None:
            surface_normal = n2

        samples.append(
            CurveSample(
                position=pos,
                tangent=(0.0, 0.0, -1.0),  # Will be smoothed later
                speed=speed,
                arc_length=target_d,
                t=target_d / total_length,
                surface_normal=surface_normal,
            )
        )

        curvature = max(_segment_curvature(points, current_idx), _segment_curvature(points, current_idx + 1))
        step_length = _effective_step_length(curvature, longitudinal_step_length, curvature_min_angle_degrees)
        target_d += max(0.001, step_length)

    # Ensure the exact end point is included
    p_last = points[-1]
    if samples and (total_length - samples[-1].arc_length) < 0.001:
        samples[-1] = CurveSample(
            position=p_last.position,
            tangent=(0.0, 0.0, -1.0),
            speed=p_last.speed,
            arc_length=total_length,
            t=1.0,
            surface_normal=p_last.surface_normal
        )
    else:
        samples.append(CurveSample(
            position=p_last.position,
            tangent=(0.0, 0.0, -1.0),
            speed=p_last.speed,
            arc_length=total_length,
            t=1.0,
            surface_normal=p_last.surface_normal
        ))

    # Smooth tangents
    for index, sample in enumerate(samples):
        samples[index] = replace(sample, tangent=_sample_tangent(samples, index))

    return samples
