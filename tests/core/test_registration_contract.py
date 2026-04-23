from waterfall_tool.registration import CLASS_NAMES


def test_registration_class_names_are_stable():
    assert CLASS_NAMES == (
        "WaterfallEmitterSettings",
        "WaterfallCurveSettings",
        "WaterfallGlobalSettings",
        "WATERFALL_OT_simulate_curve",
        "WATERFALL_OT_simulate_all_emitters",
        "WATERFALL_OT_rebuild_preview",
        "WATERFALL_OT_bake_mesh",
        "WATERFALL_PT_curve_card_panel",
    )
