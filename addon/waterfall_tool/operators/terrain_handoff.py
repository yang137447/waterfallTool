from __future__ import annotations

import bpy

from ..adapters.blender_terrain import (
    GENERATED_TAG_KEY,
    GENERATED_TERRAIN_COLLECTION_NAME,
)
from ..terrain.emitters import choose_handoff_emitter_name
from ..terrain.types import SuggestedEmitter

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

        emitter_objects = [
            obj
            for obj in tagged_objects.values()
            if obj.name.startswith("WFT_Terrain_SuggestedEmitter_") and obj.type == "CURVE"
        ]
        if not emitter_objects:
            self.report({"ERROR"}, "Generate terrain before handoff")
            return {"CANCELLED"}

        emitters: list[SuggestedEmitter] = []
        object_names: list[str] = []
        try:
            for obj in sorted(emitter_objects, key=lambda item: int(item.get("wft_emitter_index", -1))):
                emitters.append(
                    SuggestedEmitter(
                        level_index=int(obj["wft_level_index"]),
                        # Handoff chooser only needs strength + level ordering; points are not used.
                        points=[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)],
                        strength=float(obj["wft_strength"]),
                        enabled=True,
                    )
                )
                object_names.append(obj.name)
        except Exception:
            self.report({"ERROR"}, "Generated terrain is missing emitter metadata. Re-generate terrain.")
            return {"CANCELLED"}

        try:
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
