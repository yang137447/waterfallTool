from __future__ import annotations

from .types import BlockerMass, LipCurveDraft, TerraceLevel, TerrainMeshPayload


def build_main_terrain_mesh(
    levels: list[TerraceLevel],
    lips: list[LipCurveDraft],
    blockers: list[BlockerMass],
) -> TerrainMeshPayload:
    _ = blockers
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    level_ids: list[int] = []
    for level, lip in zip(levels, lips):
        back_left = (lip.points[0][0], 2.0 + level.level_index * 0.45, level.elevation + level.terrace_depth)
        back_right = (lip.points[-1][0], 2.0 + level.level_index * 0.45, level.elevation + level.terrace_depth)
        lip_left = lip.points[0]
        lip_mid = lip.points[2]
        lip_right = lip.points[-1]
        lower_mid = (lip_mid[0], -1.0 - level.level_index * 0.25, level.elevation - level.drop_height_to_next)
        vertices.extend([back_left, lip_left, lip_mid, lip_right, back_right, lower_mid])
        start = len(vertices) - 6
        faces.extend(
            [
                (start, start + 1, start + 2, start + 5),
                (start + 2, start + 3, start + 4, start + 5),
            ]
        )
        level_ids.extend([level.level_index] * 6)
    return TerrainMeshPayload(vertices=vertices, faces=faces, level_ids=level_ids)
