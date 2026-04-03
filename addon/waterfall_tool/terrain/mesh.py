from __future__ import annotations

import math

from .types import BlockerMass, LipCurveDraft, TerraceLevel, TerrainMeshPayload


def _gap_spans(continuity_segments: tuple[tuple[float, float], ...]) -> list[tuple[float, float]]:
    ordered = sorted(continuity_segments)
    spans: list[tuple[float, float]] = []
    cursor = 0.0
    for start, end in ordered:
        if start > cursor:
            spans.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < 1.0:
        spans.append((cursor, 1.0))
    return spans


def _gap_influence(progress: float, continuity_segments: tuple[tuple[float, float], ...]) -> float:
    influence = 0.0
    for start, end in _gap_spans(continuity_segments):
        center = (start + end) * 0.5
        radius = max(0.08, (end - start) * 0.6)
        influence = max(influence, max(0.0, 1.0 - abs(progress - center) / radius))
    return influence


def _build_level_rows(
    level: TerraceLevel,
    lip: LipCurveDraft,
    blockers: list[BlockerMass],
) -> list[list[tuple[float, float, float]]]:
    lip_points = list(lip.points)
    axis_y = lip_points[0][1]
    drop_depth = max(0.55, level.drop_height_to_next * 0.85 + 0.2 * level.level_index)

    back_row: list[tuple[float, float, float]] = []
    upper_row: list[tuple[float, float, float]] = []
    lip_row: list[tuple[float, float, float]] = []
    drop_row: list[tuple[float, float, float]] = []

    for index, point in enumerate(lip_points):
        x, _y, z = point
        progress = index / max(1, len(lip_points) - 1)
        surface_base = max(z, level.elevation)
        width_wave = math.sin(progress * math.pi) * math.sin(progress * math.pi * 2.0 + level.level_index * 0.8)
        erosion = abs(math.sin(progress * math.pi * 3.0 + level.level_index * 0.9)) * math.sin(progress * math.pi)
        gap_carve = _gap_influence(progress, lip.continuity_segments)
        lateral_sweep = (progress - 0.5) * level.terrace_depth * 0.14
        terrace_y_offset = level.terrace_depth * 0.12 * width_wave - gap_carve * 0.18

        back_row.append(
            (
                x * 1.06,
                axis_y + level.terrace_depth * 0.95 + terrace_y_offset + lateral_sweep,
                surface_base + level.terrace_depth * (0.16 + level.basin_strength * 0.14) - gap_carve * 0.08,
            )
        )
        upper_row.append(
            (
                x * 1.02,
                axis_y + level.terrace_depth * 0.45 + terrace_y_offset * 0.75 + lateral_sweep * 0.5,
                surface_base
                + level.terrace_depth * (0.08 + level.basin_strength * 0.08)
                + erosion * 0.08
                - gap_carve * 0.14,
            )
        )
        lip_row.append((x, axis_y + terrace_y_offset * 0.45, z - erosion * 0.18 - gap_carve * 0.22))
        drop_row.append(
            (
                x * 0.94,
                axis_y - (1.15 + 0.22 * level.level_index) + terrace_y_offset * 0.3,
                z - drop_depth - gap_carve * 0.28,
            )
        )

    for blocker in blockers:
        for row_index, row in enumerate((back_row, upper_row, lip_row, drop_row)):
            shaped_row: list[tuple[float, float, float]] = []
            for point in row:
                x, y, z = point
                influence = math.exp(-(((x - blocker.center[0]) / max(0.65, blocker.width * 0.7)) ** 2))
                if influence < 0.05:
                    shaped_row.append(point)
                    continue

                forward_push = blocker.forward_offset * 0.4 * influence
                height_push = blocker.height * (0.34 - row_index * 0.06) * influence
                width_push = blocker.width * 0.08 * influence
                direction = -1.0 if x < blocker.center[0] else 1.0

                shaped_row.append(
                    (
                        x + direction * width_push,
                        y + forward_push,
                        z + height_push,
                    )
                )
            row[:] = shaped_row

    return [back_row, upper_row, lip_row, drop_row]


def _span_midpoint_has_continuity(
    start_ratio: float,
    end_ratio: float,
    continuity_segments: tuple[tuple[float, float], ...],
) -> bool:
    midpoint = (start_ratio + end_ratio) * 0.5
    return any(segment_start <= midpoint <= segment_end for segment_start, segment_end in continuity_segments)


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

    blockers_by_level: dict[int, list[BlockerMass]] = {}
    for blocker in blockers:
        blockers_by_level.setdefault(blocker.level_index, []).append(blocker)

    for level, lip in zip(levels, lips):
        if len(lip.points) < 3:
            raise ValueError("Lip curve points must include at least three vertices")
        rows = _build_level_rows(level, lip, blockers_by_level.get(level.level_index, []))
        row_width = len(rows[0])
        start = len(vertices)

        for row in rows:
            vertices.extend(row)
            level_ids.extend([level.level_index] * row_width)

        for row_index in range(len(rows) - 1):
            upper_start = start + row_index * row_width
            lower_start = start + (row_index + 1) * row_width
            for column_index in range(row_width - 1):
                start_ratio = column_index / (row_width - 1)
                end_ratio = (column_index + 1) / (row_width - 1)
                if not _span_midpoint_has_continuity(start_ratio, end_ratio, lip.continuity_segments):
                    continue
                faces.append(
                    (
                        upper_start + column_index,
                        upper_start + column_index + 1,
                        lower_start + column_index + 1,
                        lower_start + column_index,
                    )
                )

    return TerrainMeshPayload(vertices=vertices, faces=faces, level_ids=level_ids)
