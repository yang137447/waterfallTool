from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Vec3 = tuple[float, float, float]
LipProfileMode = Literal["arc", "mixed"]


@dataclass(frozen=True)
class TerrainBlueprint:
    axis_points: tuple[Vec3, ...]
    level_count: int
    top_elevation: float
    total_drop: float
    base_width: float
    terrace_depth: float
    width_decay: float
    depth_decay: float
    lip_roundness: float
    gap_frequency: float
    blocker_density: float
    seed: int

    def __post_init__(self) -> None:
        cleaned_axis = tuple(tuple(point) for point in self.axis_points)
        object.__setattr__(self, "axis_points", cleaned_axis)


@dataclass(frozen=True)
class TerraceLevel:
    level_index: int
    elevation: float
    terrace_depth: float
    terrace_width: float
    drop_height_to_next: float
    basin_strength: float
    lip_profile_mode: LipProfileMode


@dataclass(frozen=True)
class LipCurveDraft:
    level_index: int
    points: tuple[Vec3, ...]
    continuity_segments: tuple[tuple[float, float], ...]
    overridden: bool


@dataclass(frozen=True)
class GapSegment:
    level_index: int
    start_ratio: float
    end_ratio: float
    depth_strength: float
    locked: bool


@dataclass(frozen=True)
class BlockerMass:
    level_index: int
    center: Vec3
    width: float
    height: float
    forward_offset: float
    manual: bool


@dataclass(frozen=True)
class TerrainMeshPayload:
    vertices: list[Vec3]
    faces: list[tuple[int, int, int, int]]
    level_ids: list[int]


@dataclass(frozen=True)
class SuggestedEmitter:
    level_index: int
    points: list[Vec3]
    strength: float
    enabled: bool
