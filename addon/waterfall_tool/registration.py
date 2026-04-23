from __future__ import annotations

CLASS_NAMES = (
    "WaterfallEmitterSettings",
    "WaterfallCurveSettings",
    "WaterfallGlobalSettings",
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
    from .properties import WaterfallCurveSettings, WaterfallEmitterSettings, WaterfallGlobalSettings

    return [
        WaterfallEmitterSettings,
        WaterfallCurveSettings,
        WaterfallGlobalSettings,
        WATERFALL_OT_simulate_curve,
        WATERFALL_OT_rebuild_preview,
        WATERFALL_OT_bake_mesh,
        WATERFALL_PT_curve_card_panel,
    ]


def register() -> None:
    import bpy

    from .adapters.blender_cutoff_guide import ensure_cutoff_guide
    from .operators.preview import depsgraph_refresh

    classes = _classes()
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.waterfall_emitter = bpy.props.PointerProperty(type=classes[0])
    bpy.types.Object.waterfall_curve = bpy.props.PointerProperty(type=classes[1])
    bpy.types.Scene.waterfall_global = bpy.props.PointerProperty(type=classes[2])
    def _init_scenes():
        for scene in bpy.data.scenes:
            ensure_cutoff_guide(scene)
        return None
    
    bpy.app.timers.register(_init_scenes, first_interval=0.1)
    
    if depsgraph_refresh not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(depsgraph_refresh)


def unregister() -> None:
    import bpy

    from .operators.preview import depsgraph_refresh

    if depsgraph_refresh in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(depsgraph_refresh)
    if hasattr(bpy.types.Scene, "waterfall_global"):
        del bpy.types.Scene.waterfall_global
    if hasattr(bpy.types.Object, "waterfall_curve"):
        del bpy.types.Object.waterfall_curve
    if hasattr(bpy.types.Object, "waterfall_emitter"):
        del bpy.types.Object.waterfall_emitter
    for cls in reversed(_classes()):
        bpy.utils.unregister_class(cls)
