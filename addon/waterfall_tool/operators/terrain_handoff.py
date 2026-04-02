from __future__ import annotations

import bpy


class WFT_OT_UseGeneratedTerrainForWaterfall(bpy.types.Operator):
    bl_idname = "wft.use_generated_terrain_for_waterfall"
    bl_label = "Use Terrain For Waterfall"

    def execute(self, context):
        settings = context.scene.wft_settings
        emitter = bpy.data.objects.get("WFT_Terrain_SuggestedEmitter_00")
        terrain = bpy.data.objects.get("WFT_Terrain_MainTerrain")
        if emitter is None or terrain is None:
            self.report({"ERROR"}, "Generate terrain before handoff")
            return {"CANCELLED"}
        settings.emitter_object = emitter
        settings.collider_object = terrain
        return {"FINISHED"}

