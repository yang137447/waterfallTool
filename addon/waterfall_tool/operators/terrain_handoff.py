from __future__ import annotations

import bpy

from ..adapters.blender_terrain import (
    GENERATED_TAG_KEY,
    GENERATED_TERRAIN_COLLECTION_NAME,
    build_blueprint_from_scene,
    read_lip_overrides,
)
from ..terrain.blueprint import build_terrace_levels
from ..terrain.emitters import build_suggested_emitters, choose_handoff_emitter_name
from ..terrain.layout import build_gap_segments, build_lip_curves
from ..terrain.overrides import apply_lip_overrides

class WFT_OT_UseGeneratedTerrainForWaterfall(bpy.types.Operator):
    bl_idname = "wft.use_generated_terrain_for_waterfall"
    bl_label = "Use Terrain For Waterfall"

    def execute(self, context):
        settings = context.scene.wft_settings
        scene = context.scene
        generated_collection = next(
            (child for child in scene.collection.children if child.name == GENERATED_TERRAIN_COLLECTION_NAME),
            None,
        )
        if generated_collection is None:
            self.report({"ERROR"}, "Generate terrain before handoff")
            return {"CANCELLED"}

        tagged_objects = {obj.name: obj for obj in generated_collection.objects if obj.get(GENERATED_TAG_KEY, False)}
        terrain = tagged_objects.get("WFT_Terrain_MainTerrain")
        if terrain is None:
            self.report({"ERROR"}, "Generate terrain before handoff")
            return {"CANCELLED"}

        try:
            blueprint = build_blueprint_from_scene(settings)
            levels = build_terrace_levels(blueprint)
            lips = build_lip_curves(levels, blueprint)
            overrides = read_lip_overrides(settings.terrain_override_collection)
            lips = apply_lip_overrides(lips, overrides)
            gaps = build_gap_segments(lips, blueprint)
            emitters = build_suggested_emitters(lips, gaps)
            object_names = [f"WFT_Terrain_SuggestedEmitter_{index:02d}" for index in range(len(emitters))]
            chosen_name = choose_handoff_emitter_name(object_names, emitters)
        except Exception as exc:
            self.report({"ERROR"}, f"Could not choose terrain emitter: {exc}")
            return {"CANCELLED"}

        emitter = tagged_objects.get(chosen_name)
        if emitter is None:
            self.report({"ERROR"}, "Generated terrain emitter was not found for handoff")
            return {"CANCELLED"}

        settings.emitter_object = emitter
        settings.collider_object = terrain
        return {"FINISHED"}
