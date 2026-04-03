from __future__ import annotations

from .types import BlockerMass, LipCurveDraft, TerraceLevel, TerrainMeshPayload


def _build_level_rows(
    level: TerraceLevel,
    lip: LipCurveDraft,
) -> list[list[tuple[float, float, float]]]:
    lip_points = list(lip.points)
    axis_y = lip_points[0][1]
    drop_depth = max(0.55, level.drop_height_to_next * 0.85 + 0.2 * level.level_index)

    back_row: list[tuple[float, float, float]] = []
    upper_row: list[tuple[float, float, float]] = []
    lip_row: list[tuple[float, float, float]] = []
    drop_row: list[tuple[float, float, float]] = []

    for point in lip_points:
        x, _y, z = point
        surface_base = max(z, level.elevation)
        back_row.append(
            (
                x * 1.06,
                axis_y + level.terrace_depth * 0.95,
                surface_base + level.terrace_depth * (0.16 + level.basin_strength * 0.14),
            )
        )
        upper_row.append(
            (
                x * 1.02,
                axis_y + level.terrace_depth * 0.45,
                surface_base + level.terrace_depth * (0.08 + level.basin_strength * 0.08),
            )
        )
        lip_row.append((x, axis_y, z))
        drop_row.append((x * 0.94, axis_y - (1.15 + 0.22 * level.level_index), z - drop_depth))

    return [back_row, upper_row, lip_row, drop_row]


def build_main_terrain_mesh(
    levels: list[TerraceLevel],
    lips: list[LipCurveDraft],
    blockers: list[BlockerMass],
) -> TerrainMeshPayload:
    # Blockers are tracked here for future cutout/terrain shaping but not consumed yet.
    _ = blockers
    if len(levels) != len(lips):
        raise ValueError("levels and lips lists must have the same length")
    if any(level.level_index != lip.level_index for level, lip in zip(levels, lips)):
        raise ValueError("Level index mismatch between levels and lips")
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    level_ids: list[int] = []

    for level, lip in zip(levels, lips):
        if len(lip.points) < 3:
            raise ValueError("Lip curve points must include at least three vertices")
        rows = _build_level_rows(level, lip)
        row_width = len(rows[0])
        start = len(vertices)

        for row in rows:
            vertices.extend(row)
            level_ids.extend([level.level_index] * row_width)

        for row_index in range(len(rows) - 1):
            upper_start = start + row_index * row_width
            lower_start = start + (row_index + 1) * row_width
            for column_index in range(row_width - 1):
                faces.append(
                    (
                        upper_start + column_index,
                        upper_start + column_index + 1,
                        lower_start + column_index + 1,
                        lower_start + column_index,
                    )
                )

    return TerrainMeshPayload(vertices=vertices, faces=faces, level_ids=level_ids)
