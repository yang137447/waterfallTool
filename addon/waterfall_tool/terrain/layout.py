from __future__ import annotations

from .types import BlockerMass, GapSegment, LipCurveDraft, TerraceLevel, TerrainBlueprint


def build_lip_curves(levels: list[TerraceLevel], blueprint: TerrainBlueprint) -> list[LipCurveDraft]:
    axis_mid = blueprint.axis_points[1]
    lips: list[LipCurveDraft] = []
    for level in levels:
        half_width = level.terrace_width * 0.5
        points = [
            (-half_width, 0.0, level.elevation + 0.18),
            (-half_width * 0.45, 0.0, level.elevation + 0.05),
            (0.0, 0.0, level.elevation - 0.12 * (level.level_index + 1)),
            (half_width * 0.4, 0.0, level.elevation + 0.02),
            (half_width, 0.0, level.elevation + 0.15),
        ]
        points = [(point[0], axis_mid[1], point[2]) for point in points]
        lips.append(
            LipCurveDraft(
                level_index=level.level_index,
                points=points,
                continuity_segments=[(0.0, 0.32), (0.45, 1.0)],
                overridden=False,
            )
        )
    return lips


def build_gap_segments(lips: list[LipCurveDraft], blueprint: TerrainBlueprint) -> list[GapSegment]:
    if len(lips) < 2:
        return []
    return [
        GapSegment(level_index=1, start_ratio=0.32, end_ratio=0.45, depth_strength=0.65, locked=False),
        GapSegment(level_index=min(2, len(lips) - 1), start_ratio=0.58, end_ratio=0.72, depth_strength=0.5, locked=False),
    ]


def build_blocker_masses(
    levels: list[TerraceLevel],
    lips: list[LipCurveDraft],
    gaps: list[GapSegment],
    blueprint: TerrainBlueprint,
) -> list[BlockerMass]:
    _ = lips
    _ = gaps
    if len(levels) < 2:
        return []
    mid_index = min(2, len(levels) - 1)
    return [
        BlockerMass(
            level_index=1,
            center=(-1.45, -0.55, levels[1].elevation - 0.8),
            width=1.4,
            height=1.1,
            forward_offset=-0.55,
            manual=False,
        ),
        BlockerMass(
            level_index=mid_index,
            center=(1.75, -0.62, levels[mid_index].elevation - 0.55),
            width=1.2,
            height=0.9,
            forward_offset=-0.62,
            manual=False,
        ),
    ]
