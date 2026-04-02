CLASSES: tuple[type, ...] = ()


def register() -> None:
    try:
        import bpy
    except ModuleNotFoundError:
        return

    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    try:
        import bpy
    except ModuleNotFoundError:
        return

    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
