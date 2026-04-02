from waterfall_tool.terrain.blueprint import build_terrace_levels
from waterfall_tool.terrain.types import TerrainBlueprint


def test_build_terrace_levels_returns_three_ordered_levels():
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

    assert [round(level.elevation, 2) for level in levels] == [4.0, 1.0, -2.0]
    assert [round(level.terrace_width, 2) for level in levels] == [8.0, 7.2, 6.4]
    assert levels[1].drop_height_to_next == 3.0
