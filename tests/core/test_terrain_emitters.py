import pytest

from waterfall_tool.terrain.emitters import (
    build_suggested_emitters,
    choose_handoff_emitter,
    choose_handoff_emitter_name,
)
from waterfall_tool.terrain.types import GapSegment, LipCurveDraft, SuggestedEmitter


def test_build_suggested_emitters_skips_gap_segments():
    lips = [
        LipCurveDraft(
            level_index=0,
            points=[(-4.0, 0.0, 4.0), (-2.0, 0.0, 3.8), (0.0, 0.0, 3.7), (2.0, 0.0, 3.9), (4.0, 0.0, 4.0)],
            continuity_segments=[(0.0, 0.3), (0.5, 1.0)],
            overridden=False,
        )
    ]
    gaps = [GapSegment(level_index=0, start_ratio=0.3, end_ratio=0.5, depth_strength=0.6, locked=False)]

    emitters = build_suggested_emitters(lips, gaps)

    assert len(emitters) == 2
    assert emitters[0].level_index == 0
    assert choose_handoff_emitter(emitters).level_index == 0
    assert all(emitter.points for emitter in emitters)


def test_choose_handoff_emitter_requires_emitters():
    with pytest.raises(ValueError, match="suggested emitters"):
        choose_handoff_emitter([])


def test_build_suggested_emitters_subtracts_gap_ranges():
    lip = LipCurveDraft(
        level_index=0,
        points=[(x, 0.0, 0.0) for x in range(6)],
        continuity_segments=[(0.0, 1.0)],
        overridden=False,
    )
    gaps = [GapSegment(level_index=0, start_ratio=0.4, end_ratio=0.6, depth_strength=0.5, locked=False)]

    emitters = build_suggested_emitters([lip], gaps)

    assert len(emitters) == 2
    strengths = [emitter.strength for emitter in emitters]
    assert strengths == pytest.approx([0.4, 0.4])
    assert emitters[0].points[-1][0] < emitters[1].points[0][0]


def test_choose_handoff_emitter_name_picks_strongest_enabled_emitter():
    emitters = [
        SuggestedEmitter(level_index=0, points=[(-2.0, 0.0, 4.0), (0.0, 0.0, 3.8)], strength=0.25, enabled=True),
        SuggestedEmitter(level_index=1, points=[(-1.0, 0.0, 1.0), (1.0, 0.0, 0.9)], strength=0.4, enabled=True),
    ]

    assert (
        choose_handoff_emitter_name(
            ["WFT_Terrain_SuggestedEmitter_00", "WFT_Terrain_SuggestedEmitter_01"],
            emitters,
        )
        == "WFT_Terrain_SuggestedEmitter_01"
    )
