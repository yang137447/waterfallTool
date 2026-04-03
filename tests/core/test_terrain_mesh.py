import pytest

from waterfall_tool.terrain.blueprint import build_terrace_levels
from waterfall_tool.terrain.layout import build_blocker_masses, build_gap_segments, build_lip_curves
from waterfall_tool.terrain.mesh import build_main_terrain_mesh
from waterfall_tool.terrain.types import LipCurveDraft, TerraceLevel, TerrainBlueprint


def test_build_main_terrain_mesh_creates_faces_and_level_ids():
    blueprint = TerrainBlueprint(
        axis_points=[(-4.0, 0.0, 4.0), (0.0, 0.0, 2.5), (4.0, 0.0, 4.0)],
        level_count=3,
        top_elevation=4.0,
        total_drop=6.0,
        base_width=8.0,
        terrace_depth=2.8,
        width_decay=0.1,
        depth_decay=0.12,
        lip_roundness=0.4,
        gap_frequency=0.25,
        blocker_density=0.3,
        seed=7,
    )
    levels = build_terrace_levels(blueprint)
    lips = build_lip_curves(levels, blueprint)
    gaps = build_gap_segments(lips, blueprint)
    blockers = build_blocker_masses(levels, lips, gaps, blueprint)

    mesh = build_main_terrain_mesh(levels, lips, blockers)

    # Each level should contribute a small terrace grid, not just two fan quads.
    assert len(mesh.vertices) == 60
    # The terrace keeps a full grid of vertices while omitting some faces where lip gaps cut through.
    assert len(mesh.faces) == 27
    assert mesh.level_ids.count(0) > 0
    assert len(mesh.level_ids) == len(mesh.vertices)
    face_indices = [index for face in mesh.faces for index in face]
    assert max(face_indices) < len(mesh.vertices)
    ys = [vertex[1] for vertex in mesh.vertices]
    assert max(ys) > 2.0
    assert min(ys) < -1.0


def test_build_main_terrain_mesh_preserves_full_lip_sampling_per_level():
    blueprint = TerrainBlueprint(
        axis_points=[(-4.0, 0.0, 4.0), (0.0, 0.0, 2.5), (4.0, 0.0, 4.0)],
        level_count=2,
        top_elevation=4.0,
        total_drop=3.0,
        base_width=8.0,
        terrace_depth=2.8,
        width_decay=0.1,
        depth_decay=0.12,
        lip_roundness=0.4,
        gap_frequency=0.25,
        blocker_density=0.3,
        seed=7,
    )
    levels = build_terrace_levels(blueprint)
    lips = build_lip_curves(levels, blueprint)
    blockers = build_blocker_masses(levels, lips, build_gap_segments(lips, blueprint), blueprint)

    mesh = build_main_terrain_mesh(levels, lips, blockers)

    row_width = len(lips[0].points)
    rows_per_level = len(mesh.vertices) // len(levels) // row_width
    assert rows_per_level == 4


def test_build_main_terrain_mesh_uses_gap_segments_to_remove_terrace_faces():
    blueprint = TerrainBlueprint(
        axis_points=[(-4.0, 0.0, 4.0), (0.0, 0.0, 2.5), (4.0, 0.0, 4.0)],
        level_count=3,
        top_elevation=4.0,
        total_drop=6.0,
        base_width=8.0,
        terrace_depth=2.8,
        width_decay=0.1,
        depth_decay=0.12,
        lip_roundness=0.4,
        gap_frequency=0.25,
        blocker_density=0.3,
        seed=7,
    )
    levels = build_terrace_levels(blueprint)
    lips = build_lip_curves(levels, blueprint)
    gaps = build_gap_segments(lips, blueprint)
    blockers = build_blocker_masses(levels, lips, gaps, blueprint)

    mesh = build_main_terrain_mesh(levels, lips, blockers)

    # Gaps should remove some terrace quads instead of filling every strip.
    assert len(mesh.faces) == 27


def test_build_main_terrain_mesh_uses_blockers_to_shape_surface_profile():
    blueprint = TerrainBlueprint(
        axis_points=[(-4.0, 0.0, 4.0), (0.0, 0.0, 2.5), (4.0, 0.0, 4.0)],
        level_count=3,
        top_elevation=4.0,
        total_drop=6.0,
        base_width=8.0,
        terrace_depth=2.8,
        width_decay=0.1,
        depth_decay=0.12,
        lip_roundness=0.4,
        gap_frequency=0.25,
        blocker_density=0.3,
        seed=7,
    )
    levels = build_terrace_levels(blueprint)
    lips = build_lip_curves(levels, blueprint)
    gaps = build_gap_segments(lips, blueprint)
    blockers = build_blocker_masses(levels, lips, gaps, blueprint)

    flat_mesh = build_main_terrain_mesh(levels, lips, [])
    shaped_mesh = build_main_terrain_mesh(levels, lips, blockers)

    # Blockers should locally raise/push parts of the terrain surface.
    z_deltas = [shaped[2] - flat[2] for shaped, flat in zip(shaped_mesh.vertices, flat_mesh.vertices)]
    assert max(z_deltas) > 0.15


def test_build_main_terrain_mesh_adds_surface_undulation_across_width():
    blueprint = TerrainBlueprint(
        axis_points=[(-4.0, 0.0, 4.0), (0.0, 0.0, 2.5), (4.0, 0.0, 4.0)],
        level_count=3,
        top_elevation=4.0,
        total_drop=6.0,
        base_width=8.0,
        terrace_depth=2.8,
        width_decay=0.1,
        depth_decay=0.12,
        lip_roundness=0.4,
        gap_frequency=0.25,
        blocker_density=0.0,
        seed=7,
    )
    levels = build_terrace_levels(blueprint)
    lips = build_lip_curves(levels, blueprint)

    mesh = build_main_terrain_mesh(levels, lips, [])

    row_width = len(lips[0].points)
    upper_row = mesh.vertices[row_width : row_width * 2]
    y_values = [vertex[1] for vertex in upper_row]
    assert max(y_values) - min(y_values) > 0.12


def test_build_main_terrain_mesh_carves_notch_where_lip_has_gap():
    blueprint = TerrainBlueprint(
        axis_points=[(-4.0, 0.0, 4.0), (0.0, 0.0, 2.5), (4.0, 0.0, 4.0)],
        level_count=3,
        top_elevation=4.0,
        total_drop=6.0,
        base_width=8.0,
        terrace_depth=2.8,
        width_decay=0.1,
        depth_decay=0.12,
        lip_roundness=0.4,
        gap_frequency=0.25,
        blocker_density=0.0,
        seed=7,
    )
    levels = build_terrace_levels(blueprint)
    lips = build_lip_curves(levels, blueprint)
    gaps = build_gap_segments(lips, blueprint)
    blockers = build_blocker_masses(levels, lips, gaps, blueprint)

    mesh = build_main_terrain_mesh(levels, lips, blockers)

    row_width = len(lips[0].points)
    level_index = 1
    level_start = level_index * row_width * 4
    lip_row = mesh.vertices[level_start + row_width * 2 : level_start + row_width * 3]
    notch_depth = lip_row[2][2]
    shoulder_depth = max(lip_row[1][2], lip_row[3][2])
    assert shoulder_depth - notch_depth > 0.18


def test_build_main_terrain_mesh_requires_matching_levels_and_lips():
    levels = [TerraceLevel(level_index=0, elevation=0.0, terrace_depth=1.0, terrace_width=1.0, drop_height_to_next=0.5, basin_strength=0.5, lip_profile_mode="arc")]
    lips = [
        LipCurveDraft(
            level_index=0,
            points=[(0.0, 0.0, 1.0), (1.0, 0.0, 1.0), (2.0, 0.0, 1.0)],
            continuity_segments=[(0.0, 0.5)],
            overridden=False,
        ),
        LipCurveDraft(
            level_index=1,
            points=[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)],
            continuity_segments=[(0.5, 1.0)],
            overridden=False,
        ),
    ]

    with pytest.raises(ValueError, match="levels and lips"):
        build_main_terrain_mesh(levels, lips, [])


def test_build_main_terrain_mesh_requires_three_lip_points():
    levels = [
        TerraceLevel(
            level_index=0,
            elevation=0.0,
            terrace_depth=1.0,
            terrace_width=1.0,
            drop_height_to_next=0.5,
            basin_strength=0.5,
            lip_profile_mode="arc",
        )
    ]
    lips = [
        LipCurveDraft(
            level_index=0,
            points=[(0.0, 0.0, 1.0), (1.0, 0.0, 1.0)],
            continuity_segments=[(0.0, 1.0)],
            overridden=False,
        )
    ]

    with pytest.raises(ValueError, match="Lip curve points"):
        build_main_terrain_mesh(levels, lips, [])


def test_build_main_terrain_mesh_requires_matching_level_indices():
    levels = [
        TerraceLevel(
            level_index=0,
            elevation=0.0,
            terrace_depth=1.0,
            terrace_width=1.0,
            drop_height_to_next=0.5,
            basin_strength=0.5,
            lip_profile_mode="arc",
        ),
        TerraceLevel(
            level_index=1,
            elevation=-1.0,
            terrace_depth=1.0,
            terrace_width=1.0,
            drop_height_to_next=0.0,
            basin_strength=0.6,
            lip_profile_mode="mixed",
        ),
    ]
    lips = [
        LipCurveDraft(
            level_index=0,
            points=[(0.0, 0.0, 1.0), (1.0, 0.0, 1.0), (2.0, 0.0, 1.0)],
            continuity_segments=[(0.0, 0.5)],
            overridden=False,
        ),
        LipCurveDraft(
            level_index=4,
            points=[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)],
            continuity_segments=[(0.5, 1.0)],
            overridden=False,
        ),
    ]

    with pytest.raises(ValueError, match="Level index mismatch"):
        build_main_terrain_mesh(levels, lips, [])
