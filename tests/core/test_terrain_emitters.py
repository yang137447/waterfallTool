from waterfall_tool.terrain.emitters import build_suggested_emitters, choose_handoff_emitter
from waterfall_tool.terrain.types import GapSegment, LipCurveDraft


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
