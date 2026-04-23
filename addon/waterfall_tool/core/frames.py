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
    
    # 1. Compute raw normal vectors
    raw_normals: list[Vector3 | None] = [None] * len(samples)
    for i in range(len(samples)):
        tangent = normalize(samples[i].tangent)
        if length(tangent) <= 1.0e-8:
            tangent = (0.0, 0.0, -1.0)
            
        if samples[i].surface_normal is not None:
            # We want binormal (cross strip) to align with surface normal
            # So binormal = surface_normal, and normal (main strip) = cross(tangent, binormal)
            # This makes the main strip flat against the surface and cross strip stick out.
            binormal = normalize(samples[i].surface_normal)
            n = cross(tangent, binormal)
            if length(n) > 1.0e-4:
                raw_normals[i] = normalize(n)
        else:
            delta = (0.0, 0.0, 0.0)
            if 0 < i < len(samples) - 1:
                delta = (
                    samples[i+1].tangent[0] - samples[i-1].tangent[0],
                    samples[i+1].tangent[1] - samples[i-1].tangent[1],
                    samples[i+1].tangent[2] - samples[i-1].tangent[2],
                )
                
            cn = project_on_plane(delta, tangent)
            if length(cn) > 1.0e-4:
                raw_normals[i] = normalize(cn)
            
    # 2. Fill in None values and prevent flips
    last_valid = None
    for i in range(len(raw_normals)):
        n = raw_normals[i]
        if n is not None:
            if last_valid is not None and dot(n, last_valid) < 0.0:
                n = (-n[0], -n[1], -n[2])
                raw_normals[i] = n
            last_valid = n
            
    # If no valid curvature anywhere, fallback to simple parallel transport
    if last_valid is None:
        return _build_parallel_transport_frames(samples)
        
    # Forward propagate
    current = None
    for i in range(len(raw_normals)):
        if raw_normals[i] is not None:
            current = raw_normals[i]
        elif current is not None:
            raw_normals[i] = current
            
    # Backward propagate for the beginning
    current = None
    for i in range(len(raw_normals) - 1, -1, -1):
        if raw_normals[i] is not None:
            current = raw_normals[i]
        elif current is not None:
            raw_normals[i] = current

    # 3. Smooth the normals to avoid sudden twists
    smoothed_normals = []
    window = min(10, max(2, len(samples) // 5))
    for i in range(len(raw_normals)):
        start = max(0, i - window)
        end = min(len(raw_normals), i + window + 1)
        avg = [0.0, 0.0, 0.0]
        for j in range(start, end):
            if raw_normals[j] is not None:
                avg[0] += raw_normals[j][0]
                avg[1] += raw_normals[j][1]
                avg[2] += raw_normals[j][2]
        if length((avg[0], avg[1], avg[2])) > 1.0e-8:
            smoothed_normals.append(normalize((avg[0], avg[1], avg[2])))
        else:
            smoothed_normals.append(raw_normals[i]) # fallback to unsmoothed

    # 4. Build final frames
    previous_normal: Vector3 | None = None
    for i, sample in enumerate(samples):
        tangent = normalize(sample.tangent)
        if length(tangent) <= 1.0e-8:
            tangent = (0.0, 0.0, -1.0)

        if sample.surface_normal is not None:
            # Attached points must keep the main strip in the surface tangent plane.
            aligned_surface_normal = normalize(sample.surface_normal)
            normal = cross(tangent, aligned_surface_normal)
            if length(normal) <= 1.0e-8:
                normal = _fallback_normal(tangent)
            else:
                normal = normalize(normal)
            binormal = normalize(cross(tangent, normal))
        else:
            target_n = smoothed_normals[i]
            if target_n is not None:
                normal = project_on_plane(target_n, tangent)
                if length(normal) <= 1.0e-8:
                    normal = _fallback_normal(tangent)
                else:
                    normal = normalize(normal)
            else:
                normal = _fallback_normal(tangent)

            binormal = normalize(cross(tangent, normal))
            normal = normalize(cross(binormal, tangent))

        if previous_normal is not None and dot(normal, previous_normal) < 0.0:
            normal = (-normal[0], -normal[1], -normal[2])
            binormal = (-binormal[0], -binormal[1], -binormal[2])

        frames.append(Frame(tangent=tangent, normal=normal, binormal=binormal))
        previous_normal = normal

    return frames


def _build_parallel_transport_frames(samples: list[CurveSample]) -> list[Frame]:
    frames: list[Frame] = []
    previous_normal: Vector3 | None = None

    for sample in samples:
        tangent = normalize(sample.tangent)
        if length(tangent) <= 1.0e-8:
            tangent = (0.0, 0.0, -1.0)

        if sample.surface_normal is not None:
            binormal = normalize(sample.surface_normal)
            normal = cross(tangent, binormal)
            if length(normal) <= 1.0e-8:
                normal = _fallback_normal(tangent)
            else:
                normal = normalize(normal)
            binormal = normalize(cross(tangent, normal))
        else:
            if previous_normal is None:
                normal = _fallback_normal(tangent)
            else:
                normal = project_on_plane(previous_normal, tangent)
                if length(normal) <= 1.0e-8:
                    normal = _fallback_normal(tangent)
                normal = normalize(normal)
            binormal = normalize(cross(tangent, normal))

            if previous_normal is not None and dot(normal, previous_normal) < 0.0:
                normal = (-normal[0], -normal[1], -normal[2])
                binormal = (-binormal[0], -binormal[1], -binormal[2])

        frames.append(Frame(tangent=tangent, normal=normal, binormal=binormal))
        previous_normal = normal

    return frames
