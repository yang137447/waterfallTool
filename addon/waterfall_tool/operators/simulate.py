from __future__ import annotations

try:
    import bpy
    import mathutils
except ModuleNotFoundError:
    bpy = None
    mathutils = None

from ..core.trajectory import simulate_trajectory
from ..core.types import EmitterSettings
from ..operators.preview import resolve_emitter_curve_targets


def _direction_from_axis(obj, axis: str):
    vectors = {
        "NEG_Z": (0.0, 0.0, -1.0),
        "POS_Y": (0.0, 1.0, 0.0),
        "NEG_Y": (0.0, -1.0, 0.0),
    }
    local = vectors.get(axis, (0.0, 0.0, -1.0))
    # matrix_world 包含位移和缩放，需要剥离出来只保留旋转，或者用 to_quaternion()
    # to_3x3() 包含缩放，虽然 normalized 可以处理，但是如果是 0 缩放或者负缩放会出问题
    # 这里直接使用 to_quaternion() @ Vector 来保证是一个纯方向
    world = obj.matrix_world.to_quaternion() @ mathutils.Vector(local)
    return tuple(world.normalized())


def generate_or_resimulate_curve(emitter, context):
    from ..adapters.blender_curve import create_or_update_flow_curve
    from ..adapters.blender_scene import BlenderVisibleMeshCollisionProvider
    from ..operators.preview import refresh_curve_preview

    if emitter is None or getattr(emitter, "waterfall_emitter", None) is None:
        return None

    props = emitter.waterfall_emitter
    if not getattr(props, "enabled", False):
        return None
    scene = getattr(context, "scene", None)
    global_settings = getattr(scene, "waterfall_global", None)
    settings = EmitterSettings(
        speed=props.speed,
        gravity=getattr(global_settings, "gravity", 9.81),
        drag=getattr(global_settings, "drag", 0.0),
        time_step=getattr(global_settings, "simulation_time_step", 0.05),
        step_count=getattr(global_settings, "simulation_step_count", 80),
        attach_strength=getattr(global_settings, "attach_strength", 0.7),
        detach_threshold=getattr(global_settings, "detach_threshold", 0.35),
        surface_offset=getattr(global_settings, "surface_offset", 0.01),
        terminal_speed=getattr(global_settings, "terminal_speed", 0.0),
        cutoff_height=getattr(global_settings, "cutoff_height", float("-inf")),
    )
    curve_name = props.flow_curve_name or f"{emitter.name}_FlowCurve"
    collision_provider = BlenderVisibleMeshCollisionProvider(context, excluded_names={curve_name})
    points = simulate_trajectory(
        tuple(emitter.matrix_world.translation),
        _direction_from_axis(emitter, props.direction_axis),
        settings,
        collision_provider,
    )
    curve = create_or_update_flow_curve(context, curve_name, points, parent=emitter)
    props.flow_curve_name = curve.name
    curve.waterfall_curve.emitter_name = emitter.name
    refresh_curve_preview(curve, context)
    return curve


if bpy is not None:

    class WATERFALL_OT_simulate_curve(bpy.types.Operator):
        bl_idname = "waterfall.simulate_curve"
        bl_label = "Generate / Re-simulate Curve"
        bl_options = {"REGISTER", "UNDO"}

        def execute(self, context):
            emitter, _curve = resolve_emitter_curve_targets(context.object, bpy.data.objects)
            if emitter is None or getattr(emitter, "waterfall_emitter", None) is None:
                self.report({"ERROR"}, "Select an emitter empty")
                return {"CANCELLED"}

            generate_or_resimulate_curve(emitter, context)
            return {"FINISHED"}

else:

    class WATERFALL_OT_simulate_curve:
        pass
