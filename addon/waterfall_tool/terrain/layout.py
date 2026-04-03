from __future__ import annotations

from .types import BlockerMass, GapSegment, LipCurveDraft, TerraceLevel, TerrainBlueprint


def build_lip_curves(levels: list[TerraceLevel], blueprint: TerrainBlueprint) -> list[LipCurveDraft]:
    if len(blueprint.axis_points) < 2:
        raise ValueError("TerrainBlueprint.axis_points must contain at least 2 entries to build lip curves")

    axis_start = blueprint.axis_points[0]
    axis_mid = blueprint.axis_points[len(blueprint.axis_points) // 2]
    axis_end = blueprint.axis_points[-1]
    roundness = max(0.1, min(1.0, blueprint.lip_roundness))
    first_end = 0.32 + 0.08 * roundness
    second_start = 0.45 + 0.05 * roundness
    # continuity_segments define normalized progress ranges where the lip should interpolate smoothly with neighboring surfaces.
    continuity = ((0.0, first_end), (second_start, 1.0))

    lips: list[LipCurveDraft] = []
    for level in levels:
        half_width = level.terrace_width * 0.5
        point_list = (
            (-half_width, axis_start[1], level.elevation + 0.18),
            (-half_width * 0.45, (axis_start[1] + axis_mid[1]) * 0.5, level.elevation + 0.05),
            (0.0, axis_mid[1], level.elevation - 0.12 * (level.level_index + 1)),
            (half_width * 0.4, (axis_mid[1] + axis_end[1]) * 0.5, level.elevation + 0.02),
            (half_width, axis_end[1], level.elevation + 0.15),
        )
        points = tuple(point_list)
        lips.append(
            LipCurveDraft(
                level_index=level.level_index,
                points=points,
                continuity_segments=continuity,
                overridden=False,
            )
        )
    return lips


def build_gap_segments(lips: list[LipCurveDraft], blueprint: TerrainBlueprint) -> list[GapSegment]:
    if len(lips) < 2:
        return []

    gap_freq = max(0.05, min(1.0, blueprint.gap_frequency))
    segments: list[GapSegment] = [
        GapSegment(level_index=1, start_ratio=0.32, end_ratio=0.45, depth_strength=0.65 * gap_freq, locked=False)
    ]
    if len(lips) > 2:
        segments.append(
            GapSegment(
                level_index=min(2, len(lips) - 1),
                start_ratio=0.58,
                end_ratio=0.72,
                depth_strength=0.5 * gap_freq,
                locked=False,
            )
        )
    return segments


def build_blocker_masses(
    levels: list[TerraceLevel],
    lips: list[LipCurveDraft],
    gaps: list[GapSegment],
    blueprint: TerrainBlueprint,
) -> list[BlockerMass]:
    if len(levels) < 2 or len(lips) < 2:
        return []
    if len(blueprint.axis_points) < 2:
        raise ValueError("TerrainBlueprint.axis_points must contain at least 2 entries to position blockers")
    if len(levels) != len(lips):
        raise ValueError("Blocker generation requires lips for each terrace level")
    if any(level.level_index != lip.level_index for level, lip in zip(levels, lips)):
        raise ValueError("Level indices must match between generated levels and lip curves")

    axis_mid_y = blueprint.axis_points[1][1]
    density = max(0.0, min(1.0, blueprint.blocker_density))
    density_scale = 1.0 + density * 0.4
    gap_count = len(gaps)
    base_mid_index = min(2, len(levels) - 1)
    mid_index = min(base_mid_index, len(lips) - 1)

    first_lip_x = lips[1].points[0][0]
    second_lip_x = lips[mid_index].points[-1][0]

    first_width = 1.4 * density_scale
    first_height = 1.1 + density * 0.2
    forward_offset = -0.55 - gap_count * 0.05

    return [
        BlockerMass(
            level_index=1,
            center=(first_lip_x, axis_mid_y, levels[1].elevation - 0.8),
            width=first_width,
            height=first_height,
            forward_offset=forward_offset,
            manual=False,
        ),
        BlockerMass(
            level_index=mid_index,
            center=(second_lip_x, axis_mid_y, levels[mid_index].elevation - 0.55),
            width=1.2 * density_scale,
            height=0.9 + density * 0.15,
            forward_offset=forward_offset - 0.07,
            manual=False,
        ),
    ]
