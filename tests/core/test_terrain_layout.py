from waterfall_tool.terrain.blueprint import build_terrace_levels
from waterfall_tool.terrain.layout import build_blocker_masses, build_gap_segments, build_lip_curves
from waterfall_tool.terrain.types import TerrainBlueprint


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
