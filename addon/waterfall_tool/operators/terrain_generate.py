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
        if axis_object is None:
            return False
        if getattr(axis_object, "type", None) != "CURVE":
            return False
        curve_data = getattr(axis_object, "data", None)
        splines = getattr(curve_data, "splines", None)
        if not splines or len(splines) < 1:
            return False
        spline = splines[0]
        spline_type = getattr(spline, "type", None)
        if spline_type == "BEZIER":
            bez = getattr(spline, "bezier_points", None)
            return bool(bez) and len(bez) >= 2
        if spline_type == "POLY":
            pts = getattr(spline, "points", None)
            return bool(pts) and len(pts) >= 2
        return False

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
