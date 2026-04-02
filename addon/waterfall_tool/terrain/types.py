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
