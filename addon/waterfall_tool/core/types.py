from __future__ import annotations

from dataclasses import dataclass

from .vector_math import Vec3


@dataclass(frozen=True)
class FlowSettings:
    time_step: float
    gravity: float
    attachment: float
    split_sensitivity: float
    breakup_rate: float


@dataclass(frozen=True)
class CollisionSample:
    hit: bool
    normal: Vec3
    tangent: Vec3
    support: float
    obstacle: float


@dataclass(frozen=True)
class ParticleState:
    position: Vec3
    velocity: Vec3
    water: float
    attached: bool
    split_score: float
    breakup: float


@dataclass(frozen=True)
class PathPoint:
    position: Vec3
    speed: float
    breakup: float
    split_score: float
