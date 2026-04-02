from __future__ import annotations

import bpy


class WFT_PT_MainPanel(bpy.types.Panel):
    bl_label = "Waterfall Tool"
    bl_idname = "WFT_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Waterfall"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.wft_settings
        layout.prop(settings, "emitter_object")
        layout.prop(settings, "collider_object")
        layout.prop(settings, "preview_steps")
        layout.prop(settings, "particle_count")
        layout.prop(settings, "cache_path")
        layout.prop(settings, "sheet_width")
        layout.prop(settings, "export_directory")
        layout.prop(settings, "export_stem")
        layout.operator("wft.generate_preview")
        layout.operator("wft.bake_preview")
        layout.operator("wft.rebuild_waterfall")
        layout.operator("wft.export_waterfall")
