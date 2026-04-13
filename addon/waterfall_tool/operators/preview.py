from __future__ import annotations

try:
    import bpy
except ModuleNotFoundError:
    bpy = None

from ..core.mesh_builder import build_x_card_mesh
from ..core.trajectory import simulate_guided_trajectory
from ..core.types import EmitterSettings, MeshSettings, TrajectoryPoint


def refresh_curve_preview(curve, context):
    from ..adapters.blender_curve import read_flow_curve_points
    from ..adapters.blender_mesh import create_or_update_mesh_object
    from ..adapters.blender_scene import BlenderVisibleMeshCollisionProvider

    props = curve.waterfall_curve
    if not props.preview_enabled:
        return None

    positions, speeds = read_flow_curve_points(curve)
    points = [TrajectoryPoint(position=position, velocity=(0.0, 0.0, -speed), speed=speed) for position, speed in zip(positions, speeds, strict=True)]

    if props.curve_mode == "PHYSICS_ASSISTED" and props.emitter_name:
        emitter = bpy.data.objects.get(props.emitter_name)
        if emitter is not None:
            emitter_props = emitter.waterfall_emitter
            emitter_settings = EmitterSettings(
                speed=emitter_props.speed,
                gravity=emitter_props.gravity,
                drag=emitter_props.drag,
                time_step=emitter_props.simulation_time_step,
                step_count=emitter_props.simulation_step_count,
                attach_strength=emitter_props.attach_strength,
                detach_threshold=emitter_props.detach_threshold,
            )
            collision_provider = BlenderVisibleMeshCollisionProvider(
                context,
                excluded_names={props.preview_mesh_name, props.baked_mesh_name, curve.name},
            )
            points = simulate_guided_trajectory(positions, speeds, emitter_settings, collision_provider)

    mesh_settings = MeshSettings(
        base_segment_density=props.base_segment_density,
        curvature_refine_strength=props.curvature_refine_strength,
        start_width=props.start_width,
        end_width=props.end_width,
        width_falloff=props.width_falloff,
        cross_angle_degrees=props.cross_angle,
        uv_speed_scale=props.uv_speed_scale,
    )
    preview_name = props.preview_mesh_name or f"{curve.name}_Preview"
    mesh = build_x_card_mesh(points, mesh_settings)
    preview = create_or_update_mesh_object(context, preview_name, mesh, generated=True)
    props.preview_mesh_name = preview.name
    return preview


if bpy is not None:

    def depsgraph_refresh(scene, depsgraph):
        context = bpy.context
        for update in depsgraph.updates:
            obj = getattr(update, "id", None)
            if getattr(obj, "type", None) == "CURVE" and obj.get("waterfall_flow_curve"):
                refresh_curve_preview(obj, context)


    class WATERFALL_OT_rebuild_preview(bpy.types.Operator):
        bl_idname = "waterfall.rebuild_preview"
        bl_label = "Rebuild Preview"
        bl_options = {"REGISTER", "UNDO"}

        def execute(self, context):
            curve = context.object
            if curve is None or curve.type != "CURVE":
                emitter = context.object
                curve = bpy.data.objects.get(emitter.waterfall_emitter.flow_curve_name) if emitter else None
            if curve is None or curve.type != "CURVE":
                self.report({"ERROR"}, "Select a flow curve or emitter")
                return {"CANCELLED"}
            refresh_curve_preview(curve, context)
            return {"FINISHED"}

else:

    def depsgraph_refresh(scene, depsgraph):
        return None


    class WATERFALL_OT_rebuild_preview:
        pass
