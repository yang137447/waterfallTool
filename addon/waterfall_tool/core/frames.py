from __future__ import annotations

from .types import CurveSample, Frame, Vector3
from .vector_math import cross, dot, length, normalize, project_on_plane

WORLD_UP: Vector3 = (0.0, 0.0, 1.0)
WORLD_RIGHT: Vector3 = (1.0, 0.0, 0.0)


def _fallback_normal(tangent: Vector3) -> Vector3:
    candidate = project_on_plane(WORLD_UP, tangent)
    if length(candidate) <= 1.0e-8:
        candidate = project_on_plane(WORLD_RIGHT, tangent)
    return normalize(candidate)


def build_frames(samples: list[CurveSample]) -> list[Frame]:
    frames: list[Frame] = []
    previous_normal: Vector3 | None = None

    for sample in samples:
        tangent = normalize(sample.tangent)
        if length(tangent) <= 1.0e-8:
            tangent = (0.0, 0.0, -1.0)

        if previous_normal is None:
            normal = _fallback_normal(tangent)
        else:
            normal = project_on_plane(previous_normal, tangent)
            if length(normal) <= 1.0e-8:
                normal = _fallback_normal(tangent)
            normal = normalize(normal)

        binormal = normalize(cross(tangent, normal))
        normal = normalize(cross(binormal, tangent))

        if previous_normal is not None and dot(normal, previous_normal) < 0.0:
            normal = (-normal[0], -normal[1], -normal[2])
            binormal = (-binormal[0], -binormal[1], -binormal[2])

        frames.append(Frame(tangent=tangent, normal=normal, binormal=binormal))
        previous_normal = normal

    return frames
