from __future__ import annotations

from pathlib import Path

import bpy

from ..adapters.blender_scene import BlenderCollider, sample_emitter_points
from ..core.cache import save_cache
from ..core.preview import build_preview_paths
from ..core.types import FlowSettings, PathPoint


class WFT_OT_BakePreview(bpy.types.Operator):
    bl_idname = "wft.bake_preview"
    bl_label = "Bake Preview"

    def execute(self, context):
        settings = context.scene.wft_settings
        emitter_points = sample_emitter_points(settings.emitter_object, settings.particle_count)
        collider = BlenderCollider(settings.collider_object)
        flow_settings = FlowSettings(
            time_step=0.025,
            gravity=9.8,
            attachment=0.7,
            split_sensitivity=0.35,
            breakup_rate=0.2,
        )
        states = build_preview_paths(emitter_points, collider, flow_settings, settings.preview_steps * 2)
        cache_paths = [
            [
                PathPoint(
                    position=state.position,
                    speed=abs(state.velocity[2]),
                    breakup=state.breakup,
                    split_score=state.split_score,
                )
                for state in path
            ]
            for path in states
        ]
        save_cache(Path(settings.cache_path), cache_paths)
        return {"FINISHED"}
