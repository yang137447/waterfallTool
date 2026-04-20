from __future__ import annotations

from dataclasses import dataclass, field

Vector3 = tuple[float, float, float]
Vector2 = tuple[float, float]


@dataclass(frozen=True)
class EmitterSettings:
    speed: float = 8.0
    gravity: float = 9.81
    drag: float = 0.0
    time_step: float = 0.05
    step_count: int = 80
    attach_strength: float = 0.7
    detach_threshold: float = 0.35


@dataclass(frozen=True)
class MeshSettings:
    base_segment_density: float = 1.0
    curvature_refine_strength: float = 1.0
    curvature_density_max_multiplier: float = 4.0
    target_face_count: int = 0
    max_segment_count: int = 0
    start_width: float = 1.0
    end_width: float = 1.0
    width_falloff: float = 1.0
    cross_angle_degrees: float = 90.0
    uv_speed_scale: float = 1.0


@dataclass(frozen=True)
class CollisionSample:
    hit: bool
    point: Vector3 = (0.0, 0.0, 0.0)
    normal: Vector3 = (0.0, 0.0, 1.0)
    support: float = 0.0


@dataclass(frozen=True)
class TrajectoryPoint:
    position: Vector3
    velocity: Vector3
    speed: float
    attached: bool = False


@dataclass(frozen=True)
class CurveSample:
    position: Vector3
    tangent: Vector3
    speed: float
    arc_length: float
    t: float


@dataclass(frozen=True)
class Frame:
    tangent: Vector3
    normal: Vector3
    binormal: Vector3


@dataclass(frozen=True)
class MeshData:
    vertices: list[Vector3] = field(default_factory=list)
    faces: list[tuple[int, int, int, int]] = field(default_factory=list)
    uv0: list[list[Vector2]] = field(default_factory=list)
    uv1: list[list[Vector2]] = field(default_factory=list)


class CollisionProvider:
    def sample(self, start: Vector3, end: Vector3) -> CollisionSample:
        return CollisionSample(hit=False)
