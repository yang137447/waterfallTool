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
    split_guide_object: bpy.props.PointerProperty(name="Split Guide", type=bpy.types.Object)
    breakup_region_object: bpy.props.PointerProperty(name="Breakup Region", type=bpy.types.Object)

    terrain_axis_object: bpy.props.PointerProperty(name="Terrain Axis", type=bpy.types.Object)
    terrain_level_count: bpy.props.IntProperty(name="Terrain Levels", default=3, min=2, max=4)
    terrain_total_drop: bpy.props.FloatProperty(name="Terrain Total Drop", default=6.0, min=2.0, max=20.0)
    terrain_base_width: bpy.props.FloatProperty(name="Terrain Base Width", default=8.0, min=2.0, max=30.0)
    terrain_depth: bpy.props.FloatProperty(name="Terrain Depth", default=2.8, min=0.5, max=10.0)
