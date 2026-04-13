from __future__ import annotations

CLASS_NAMES = (
    "WaterfallEmitterSettings",
    "WaterfallCurveSettings",
    "WATERFALL_OT_simulate_curve",
    "WATERFALL_OT_rebuild_preview",
    "WATERFALL_OT_bake_mesh",
    "WATERFALL_PT_curve_card_panel",
)


def _classes() -> list[type]:
    from .operators.bake import WATERFALL_OT_bake_mesh
    from .operators.preview import WATERFALL_OT_rebuild_preview
    from .operators.simulate import WATERFALL_OT_simulate_curve
    from .panel import WATERFALL_PT_curve_card_panel
    from .properties import WaterfallCurveSettings, WaterfallEmitterSettings

    return [
        WaterfallEmitterSettings,
        WaterfallCurveSettings,
        WATERFALL_OT_simulate_curve,
        WATERFALL_OT_rebuild_preview,
        WATERFALL_OT_bake_mesh,
        WATERFALL_PT_curve_card_panel,
    ]


def register() -> None:
    import bpy

    classes = _classes()
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.waterfall_emitter = bpy.props.PointerProperty(type=classes[0])
    bpy.types.Object.waterfall_curve = bpy.props.PointerProperty(type=classes[1])


def unregister() -> None:
    import bpy

    if hasattr(bpy.types.Object, "waterfall_curve"):
        del bpy.types.Object.waterfall_curve
    if hasattr(bpy.types.Object, "waterfall_emitter"):
        del bpy.types.Object.waterfall_emitter
    for cls in reversed(_classes()):
        bpy.utils.unregister_class(cls)
