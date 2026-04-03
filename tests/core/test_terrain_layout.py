import pytest

from pytest import approx

from waterfall_tool.terrain.blueprint import build_terrace_levels
from waterfall_tool.terrain.layout import build_blocker_masses, build_gap_segments, build_lip_curves
from waterfall_tool.terrain.types import LipCurveDraft, TerrainBlueprint


def test_layout_generation_creates_lips_gaps_and_blockers():
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

    assert len(lips) == 3
    assert [lip.level_index for lip in lips] == [0, 1, 2]
    assert len(gaps) == 2
    assert gaps[0].level_index == 1
    assert len(blockers) == 2
    assert isinstance(lips[0].points, tuple)
    gap_freq = max(0.05, min(1.0, blueprint.gap_frequency))
    assert gaps[0].depth_strength == approx(0.65 * gap_freq)
    assert len(gaps) == len({gap.level_index for gap in gaps})
    density_scale = 1 + blueprint.blocker_density * 0.4
    expected_width = 1.4 * density_scale
    expected_height = 1.1 + blueprint.blocker_density * 0.2
    expected_forward = -0.55 - len(gaps) * 0.05
    assert blockers[0].width == approx(expected_width)
    assert blockers[0].height == approx(expected_height)
    assert blockers[0].forward_offset == approx(expected_forward)
    assert blockers[0].center[0] == approx(lips[1].points[0][0])


def test_build_lip_curves_follows_axis_path_instead_of_single_midpoint():
    blueprint = TerrainBlueprint(
        axis_points=[(-4.0, -1.0, 4.0), (0.0, 0.0, 2.5), (4.0, 1.5, 4.0)],
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

    left_y = lips[0].points[0][1]
    mid_y = lips[0].points[len(lips[0].points) // 2][1]
    right_y = lips[0].points[-1][1]

    assert left_y < mid_y < right_y


def test_gap_segments_produces_single_gap_for_two_levels():
    blueprint = TerrainBlueprint(
        axis_points=[(-4.0, 0.0, 4.0), (0.0, 0.0, 2.5), (4.0, 0.0, 4.0)],
        level_count=2,
        top_elevation=4.0,
        total_drop=3.0,
        base_width=6.0,
        terrace_depth=2.5,
        width_decay=0.05,
        depth_decay=0.05,
        lip_roundness=0.3,
        gap_frequency=0.4,
        blocker_density=0.2,
        seed=9,
    )
    levels = build_terrace_levels(blueprint)
    lips = build_lip_curves(levels, blueprint)
    gaps = build_gap_segments(lips, blueprint)

    assert len(lips) == 2
    assert len(gaps) == 1
    assert gaps[0].level_index == 1


def test_blocker_masses_requires_matching_lip_levels():
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
    continuity = lips[1].continuity_segments
    points = lips[1].points
    mismatched_lips = [lips[0], LipCurveDraft(level_index=99, points=points, continuity_segments=continuity, overridden=False), lips[2]]
    gaps = build_gap_segments(lips, blueprint)

    with pytest.raises(ValueError):
        build_blocker_masses(levels, mismatched_lips, gaps, blueprint)
