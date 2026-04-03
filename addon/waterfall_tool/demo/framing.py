from __future__ import annotations

from dataclasses import dataclass


Vec3 = tuple[float, float, float]


@dataclass(frozen=True)
class CameraFrame:
    location: Vec3
    target: Vec3


def compute_demo_camera_frame(bounds_min: Vec3, bounds_max: Vec3) -> CameraFrame:
    center = tuple((low + high) * 0.5 for low, high in zip(bounds_min, bounds_max))
    size = tuple(high - low for low, high in zip(bounds_min, bounds_max))
    radius = max(size)

    location = (
        center[0] - radius * 0.55,
        center[1] - radius * 1.45,
        center[2] + size[2] * 0.58,
    )
    target = (
        center[0] + size[0] * 0.05,
        center[1] - size[1] * 0.05,
        center[2] + size[2] * 0.12,
    )
    return CameraFrame(location=location, target=target)
