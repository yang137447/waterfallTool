from __future__ import annotations

import math


Vec3 = tuple[float, float, float]


def _lerp(a: Vec3, b: Vec3, t: float) -> Vec3:
    return (
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
        a[2] + (b[2] - a[2]) * t,
    )


def _distance(a: Vec3, b: Vec3) -> float:
    return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2 + (b[2] - a[2]) ** 2)


def sample_polyline_evenly(points: tuple[Vec3, ...], count: int) -> list[Vec3]:
    if count <= 0 or not points:
        return []
    if len(points) == 1:
        return [points[0]] * count

    segment_lengths = [_distance(points[index], points[index + 1]) for index in range(len(points) - 1)]
    total_length = sum(segment_lengths)
    if total_length == 0.0:
        return [points[0]] * count

    targets = [total_length * index / (count - 1) for index in range(count)] if count > 1 else [0.0]
    samples: list[Vec3] = []
    traversed = 0.0
    segment_index = 0

    for target in targets:
        while segment_index < len(segment_lengths) - 1 and traversed + segment_lengths[segment_index] < target:
            traversed += segment_lengths[segment_index]
            segment_index += 1

        segment_start = points[segment_index]
        segment_end = points[segment_index + 1]
        segment_length = segment_lengths[segment_index]
        local_target = 0.0 if segment_length == 0.0 else (target - traversed) / segment_length
        samples.append(_lerp(segment_start, segment_end, local_target))

    return samples
