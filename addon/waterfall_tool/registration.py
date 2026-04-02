CLASSES: tuple[type, ...] = ()


def _load_blender_classes() -> tuple[type, ...]:
    from .operators.bake import WFT_OT_BakePreview
    from .operators.preview import WFT_OT_GeneratePreview
    from .panel import WFT_PT_MainPanel
    from .properties import WFT_Settings

    return (
        WFT_Settings,
        WFT_OT_GeneratePreview,
        WFT_OT_BakePreview,
        WFT_PT_MainPanel,
    )


def register() -> None:
    try:
        import bpy
    except ModuleNotFoundError:
        return

    global CLASSES
    CLASSES = _load_blender_classes()

    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.wft_settings = bpy.props.PointerProperty(type=CLASSES[0])


def unregister() -> None:
    try:
        import bpy
    except ModuleNotFoundError:
        return

    if hasattr(bpy.types.Scene, "wft_settings"):
        del bpy.types.Scene.wft_settings

    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
