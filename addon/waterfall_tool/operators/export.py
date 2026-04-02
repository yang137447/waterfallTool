from __future__ import annotations

import json
from pathlib import Path

import bpy

from ..core.export_plan import build_export_plan, resolve_export_object_names


class WFT_OT_ExportWaterfall(bpy.types.Operator):
    bl_idname = "wft.export_waterfall"
    bl_label = "Export Waterfall"

    def execute(self, context):
        settings = context.scene.wft_settings
        plan = build_export_plan(Path(settings.export_directory), settings.export_stem)
        plan.mesh_path.parent.mkdir(parents=True, exist_ok=True)
        target_names = resolve_export_object_names([obj.name for obj in context.scene.objects])

        bpy.ops.object.select_all(action="DESELECT")
        active_object = None
        for name in target_names:
            obj = context.scene.objects.get(name)
            if obj is not None:
                obj.select_set(True)
                if active_object is None:
                    active_object = obj

        if active_object is None:
            self.report({"ERROR"}, "No waterfall export objects found")
            return {"CANCELLED"}

        context.view_layer.objects.active = active_object

        bpy.ops.export_scene.gltf(
            filepath=str(plan.mesh_path),
            use_selection=True,
            export_format="GLB",
        )
        plan.mask_path.write_text(
            json.dumps(
                {"vertex_color_channels": ["foam", "breakup", "impact", "edge"]},
                indent=2,
            ),
            encoding="utf-8",
        )
        return {"FINISHED"}
