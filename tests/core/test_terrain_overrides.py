from waterfall_tool.terrain.overrides import apply_lip_overrides
from waterfall_tool.terrain.types import LipCurveDraft


def test_apply_lip_overrides_replaces_only_targeted_level():
    auto_lips = [
        LipCurveDraft(
            level_index=0,
            points=((-3.0, 0.0, 4.0), (0.0, 0.0, 3.8), (3.0, 0.0, 4.0)),
            continuity_segments=((0.0, 1.0),),
            overridden=False,
        ),
        LipCurveDraft(
            level_index=1,
            points=((-2.5, 0.0, 1.0), (0.0, 0.0, 0.8), (2.5, 0.0, 1.0)),
            continuity_segments=((0.0, 1.0),),
            overridden=False,
        ),
    ]
    overrides = {
        1: LipCurveDraft(
            level_index=1,
            points=((-2.0, 0.0, 1.3), (0.0, 0.0, 0.7), (2.0, 0.0, 1.3)),
            continuity_segments=((0.0, 1.0),),
            overridden=True,
        )
    }

    merged = apply_lip_overrides(auto_lips, overrides)

    assert len(merged) == len(auto_lips)
    assert merged[0].points == auto_lips[0].points
    assert merged[0].overridden is False
    assert merged[1] is overrides[1]
    assert merged[1].overridden is True
    assert merged[1].points[0] == (-2.0, 0.0, 1.3)
