from __future__ import annotations

from pathlib import Path

import bpy

from ..adapters.blender_nodes import ensure_waterfall_node_group
from ..core.cache import load_cache
from ..core.rebuild import build_ribbon_mesh


class WFT_OT_RebuildWaterfall(bpy.types.Operator):
    bl_idname = "wft.rebuild_waterfall"
    bl_label = "Rebuild Waterfall"

    def execute(self, context):
        settings = context.scene.wft_settings
        cached_paths = load_cache(Path(settings.cache_path))
        ribbon = build_ribbon_mesh(cached_paths, base_width=settings.sheet_width)

        existing = bpy.data.objects.get("WFT_MainSheet")
        if existing is not None:
            bpy.data.objects.remove(existing, do_unlink=True)

        mesh = bpy.data.meshes.new("WFT_MainSheetMesh")
        mesh.from_pydata(ribbon.vertices, [], ribbon.faces)
        mesh.update()

        obj = bpy.data.objects.new("WFT_MainSheet", mesh)
        context.scene.collection.objects.link(obj)

        modifier = obj.modifiers.new(name="WFT_RibbonSheet", type="NODES")
        modifier.node_group = ensure_waterfall_node_group()
        return {"FINISHED"}
