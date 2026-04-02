from __future__ import annotations

from dataclasses import dataclass

Vec3 = tuple[float, float, float]


@dataclass(frozen=True)
class TerrainBlueprint:
    axis_points: list[Vec3]
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


@dataclass(frozen=True)
class TerraceLevel:
    level_index: int
    elevation: float
    terrace_depth: float
    terrace_width: float
    drop_height_to_next: float
    basin_strength: float
    lip_profile_mode: str
