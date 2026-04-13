from __future__ import annotations

try:
    import bpy
    import mathutils
except ModuleNotFoundError:
    bpy = None
    mathutils = None

from ..core.trajectory import simulate_trajectory
from ..core.types import EmitterSettings


def _direction_from_axis(obj, axis: str):
    vectors = {
        "NEG_Z": (0.0, 0.0, -1.0),
        "POS_Y": (0.0, 1.0, 0.0),
        "NEG_Y": (0.0, -1.0, 0.0),
    }
    local = vectors.get(axis, (0.0, 0.0, -1.0))
    world = obj.matrix_world.to_3x3() @ mathutils.Vector(local)
    return tuple(world.normalized())


if bpy is not None:

    class WATERFALL_OT_simulate_curve(bpy.types.Operator):
        bl_idname = "waterfall.simulate_curve"
        bl_label = "Generate / Re-simulate Curve"
        bl_options = {"REGISTER", "UNDO"}

        def execute(self, context):
            from ..adapters.blender_curve import create_or_update_flow_curve
            from ..adapters.blender_scene import BlenderVisibleMeshCollisionProvider

            emitter = context.object
            if emitter is None:
                self.report({"ERROR"}, "Select an emitter empty")
                return {"CANCELLED"}

            props = emitter.waterfall_emitter
            settings = EmitterSettings(
                speed=props.speed,
                gravity=props.gravity,
                drag=props.drag,
                time_step=props.simulation_time_step,
                step_count=props.simulation_step_count,
                attach_strength=props.attach_strength,
                detach_threshold=props.detach_threshold,
            )
            curve_name = props.flow_curve_name or f"{emitter.name}_FlowCurve"
            collision_provider = BlenderVisibleMeshCollisionProvider(context, excluded_names={curve_name})
            points = simulate_trajectory(
                tuple(emitter.matrix_world.translation),
                _direction_from_axis(emitter, props.direction_axis),
                settings,
                collision_provider,
            )
            curve = create_or_update_flow_curve(context, curve_name, points)
            props.flow_curve_name = curve.name
            curve.waterfall_curve.emitter_name = emitter.name
            bpy.ops.waterfall.rebuild_preview()
            return {"FINISHED"}

else:

    class WATERFALL_OT_simulate_curve:
        pass
