from __future__ import annotations

from dataclasses import dataclass, field

Vector3 = tuple[float, float, float]
Vector2 = tuple[float, float]


@dataclass(frozen=True)
class EmitterSettings:
    speed: float = 4.0
    gravity: float = 10.0
    drag: float = 0.0
    time_step: float = 0.1
    step_count: int = 24
    attach_strength: float = 0.5
    detach_threshold: float = 0.25


@dataclass(frozen=True)
class MeshSettings:
    start_width: float = 1.0
    end_width: float = 1.0
    width_falloff: float = 1.0
    cross_angle_degrees: float = 90.0
    uv_speed_scale: float = 1.0


@dataclass(frozen=True)
class CollisionSample:
    hit: bool = False
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
    faces: list[tuple[int, int, int]] = field(default_factory=list)
    uvs: list[Vector2] = field(default_factory=list)
    vertex_colors: list[float] = field(default_factory=list)


class CollisionProvider:
    def sample(self, start: Vector3, end: Vector3) -> CollisionSample:
        return CollisionSample(hit=False)
