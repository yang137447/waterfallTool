from waterfall_tool.core.preview import apply_control_influences
from waterfall_tool.core.types import FlowSettings


def test_apply_control_influences_raises_breakup_inside_break_region():
    settings = FlowSettings(
        time_step=0.1,
        gravity=9.8,
        attachment=0.7,
        split_sensitivity=0.3,
        breakup_rate=0.2,
    )
    influenced = apply_control_influences(
        breakup=0.1,
        split_score=0.0,
        position=(0.0, 0.0, 0.0),
        control_sample={"breakup_boost": 0.5, "split_boost": 0.2},
        settings=settings,
    )

    assert influenced["breakup"] == 0.6
    assert influenced["split_score"] == 0.06
