from __future__ import annotations

import bpy

from ..adapters.blender_debug import ensure_preview_curves
from ..adapters.blender_scene import BlenderCollider, sample_control_influences, sample_emitter_points
from ..core.preview import build_preview_paths
from ..core.types import FlowSettings


class WFT_OT_GeneratePreview(bpy.types.Operator):
    bl_idname = "wft.generate_preview"
    bl_label = "Generate Preview"

    def execute(self, context):
        settings = context.scene.wft_settings
        emitter_points = sample_emitter_points(settings.emitter_object, settings.particle_count)
        collider = BlenderCollider(settings.collider_object)
        flow_settings = FlowSettings(
            time_step=0.05,
            gravity=9.8,
            attachment=0.7,
            split_sensitivity=0.35,
            breakup_rate=0.2,
        )
        control_sampler = lambda position: sample_control_influences(
            position,
            settings.split_guide_object,
            settings.breakup_region_object,
        )
        paths = build_preview_paths(
            emitter_points,
            collider,
            flow_settings,
            settings.preview_steps,
            control_sampler=control_sampler,
        )
        ensure_preview_curves(context, paths)
        return {"FINISHED"}
