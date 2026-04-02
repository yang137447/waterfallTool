from __future__ import annotations

import bpy

from ..adapters.blender_terrain import create_terrain_objects


class WFT_OT_GenerateTerraceTerrain(bpy.types.Operator):
    bl_idname = "wft.generate_terrace_terrain"
    bl_label = "Generate Terrace Terrain"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        scene = getattr(context, "scene", None)
        settings = getattr(scene, "wft_settings", None) if scene is not None else None
        axis_object = getattr(settings, "terrain_axis_object", None) if settings is not None else None
        return axis_object is not None

    def execute(self, context):
        settings = context.scene.wft_settings
        if settings.terrain_axis_object is None:
            self.report({"ERROR"}, "Terrain axis object is not set")
            return {"CANCELLED"}

        try:
            create_terrain_objects(context, settings)
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Terrain generation failed: {exc}")
            return {"CANCELLED"}

        return {"FINISHED"}
