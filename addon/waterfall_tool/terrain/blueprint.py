from __future__ import annotations

from .types import TerraceLevel, TerrainBlueprint


def build_terrace_levels(blueprint: TerrainBlueprint) -> list[TerraceLevel]:
    level_drop = blueprint.total_drop / max(1, blueprint.level_count - 1)
    levels: list[TerraceLevel] = []
    for index in range(blueprint.level_count):
        elevation = blueprint.top_elevation - level_drop * index
        width_factor = 1.0 - blueprint.width_decay * index
        depth_factor = 1.0 - blueprint.depth_decay * index
        terrace_width = max(0.0, blueprint.base_width * width_factor)
        terrace_depth = max(0.0, blueprint.terrace_depth * depth_factor)
        drop_height_to_next = 0.0 if index == blueprint.level_count - 1 else level_drop
        basin_strength = 0.35 + 0.15 * index
        lip_profile_mode = "arc" if index == 0 else "mixed"
        levels.append(
            TerraceLevel(
                level_index=index,
                elevation=elevation,
                terrace_depth=terrace_depth,
                terrace_width=terrace_width,
                drop_height_to_next=drop_height_to_next,
                basin_strength=basin_strength,
                lip_profile_mode=lip_profile_mode,
            )
        )
    return levels
