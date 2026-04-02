from __future__ import annotations

import json
from pathlib import Path

import bpy

from ..core.export_plan import build_export_plan


class WFT_OT_ExportWaterfall(bpy.types.Operator):
    bl_idname = "wft.export_waterfall"
    bl_label = "Export Waterfall"

    def execute(self, context):
        settings = context.scene.wft_settings
        plan = build_export_plan(Path(settings.export_directory), settings.export_stem)
        plan.mesh_path.parent.mkdir(parents=True, exist_ok=True)

        bpy.ops.export_scene.gltf(
            filepath=str(plan.mesh_path),
            use_selection=False,
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
