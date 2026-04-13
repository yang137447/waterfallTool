from __future__ import annotations

from typing import Any

from .properties import WaterfallCurveSettings, WaterfallEmitterSettings

CLASS_NAMES = (
    "WaterfallEmitterSettings",
    "WaterfallCurveSettings",
    "WATERFALL_OT_simulate_curve",
    "WATERFALL_OT_rebuild_preview",
    "WATERFALL_OT_bake_mesh",
    "WATERFALL_PT_curve_card_panel",
)


def _placeholder_class(name: str) -> type[Any]:
    return type(name, (), {})


def _classes() -> tuple[type[Any], ...]:
    try:
        from .operators.bake import WATERFALL_OT_bake_mesh
    except ModuleNotFoundError:
        WATERFALL_OT_bake_mesh = _placeholder_class("WATERFALL_OT_bake_mesh")

    try:
        from .operators.preview import WATERFALL_OT_rebuild_preview
    except ModuleNotFoundError:
        WATERFALL_OT_rebuild_preview = _placeholder_class("WATERFALL_OT_rebuild_preview")

    try:
        from .operators.simulate import WATERFALL_OT_simulate_curve
    except ModuleNotFoundError:
        WATERFALL_OT_simulate_curve = _placeholder_class("WATERFALL_OT_simulate_curve")

    try:
        from .panel import WATERFALL_PT_curve_card_panel
    except ModuleNotFoundError:
        WATERFALL_PT_curve_card_panel = _placeholder_class("WATERFALL_PT_curve_card_panel")

    return (
        WaterfallEmitterSettings,
        WaterfallCurveSettings,
        WATERFALL_OT_simulate_curve,
        WATERFALL_OT_rebuild_preview,
        WATERFALL_OT_bake_mesh,
        WATERFALL_PT_curve_card_panel,
    )


def register() -> None:
    try:
        import bpy
    except ModuleNotFoundError:
        return

    for cls in _classes():
        bpy.utils.register_class(cls)

    bpy.types.Scene.waterfall_emitter_settings = bpy.props.PointerProperty(
        type=WaterfallEmitterSettings
    )
    bpy.types.Scene.waterfall_curve_settings = bpy.props.PointerProperty(
        type=WaterfallCurveSettings
    )


def unregister() -> None:
    try:
        import bpy
    except ModuleNotFoundError:
        return

    if hasattr(bpy.types.Scene, "waterfall_curve_settings"):
        del bpy.types.Scene.waterfall_curve_settings
    if hasattr(bpy.types.Scene, "waterfall_emitter_settings"):
        del bpy.types.Scene.waterfall_emitter_settings

    for cls in reversed(_classes()):
        bpy.utils.unregister_class(cls)
