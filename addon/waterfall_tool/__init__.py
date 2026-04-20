from __future__ import annotations

bl_info = {
    "name": "Waterfall Curve Card Tool",
    "author": "waterfallTool",
    "version": (0, 1, 1),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Waterfall",
    "description": "Simulate editable waterfall flow curves and generate X-card strip meshes.",
    "category": "Object",
}


def register() -> None:
    from .registration import register

    register()


def unregister() -> None:
    from .registration import unregister

    unregister()
