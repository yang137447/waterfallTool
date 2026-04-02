from __future__ import annotations

import bpy


class WFT_Settings(bpy.types.PropertyGroup):
    emitter_object: bpy.props.PointerProperty(name="Emitter Curve", type=bpy.types.Object)
    collider_object: bpy.props.PointerProperty(name="Collider Mesh", type=bpy.types.Object)
    preview_steps: bpy.props.IntProperty(name="Preview Steps", default=24, min=2, max=256)
    particle_count: bpy.props.IntProperty(name="Particle Count", default=24, min=2, max=512)
    cache_path: bpy.props.StringProperty(
        name="Cache Path",
        default="D:/YYBWorkSpace/GitHub/waterfallTool/cache/preview.json",
        subtype="FILE_PATH",
    )
    sheet_width: bpy.props.FloatProperty(name="Sheet Width", default=0.5, min=0.05, max=10.0)
    export_directory: bpy.props.StringProperty(
        name="Export Directory",
        default="D:/YYBWorkSpace/GitHub/waterfallTool/exports",
        subtype="DIR_PATH",
    )
    export_stem: bpy.props.StringProperty(name="Export Stem", default="waterfall")
