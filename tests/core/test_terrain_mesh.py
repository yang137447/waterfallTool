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

    assert len(mesh.vertices) == 18
    assert len(mesh.faces) == 6
    assert mesh.level_ids.count(0) > 0
    assert len(mesh.level_ids) == len(mesh.vertices)
    face_indices = [index for face in mesh.faces for index in face]
    assert max(face_indices) < len(mesh.vertices)


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
