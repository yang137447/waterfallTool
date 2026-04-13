from __future__ import annotations

try:
    import bpy
except ModuleNotFoundError:
    bpy = None


def _safe_operator_call(operator_id: str) -> None:
    if bpy is None:
        return
    try:
        namespace, name = operator_id.split(".")
        getattr(getattr(bpy.ops, namespace), name)()
    except RuntimeError:
        return


def _refresh_from_emitter(_self, _context) -> None:
    _safe_operator_call("waterfall.simulate_curve")


def _refresh_from_curve(_self, _context) -> None:
    _safe_operator_call("waterfall.rebuild_preview")


if bpy is not None:

    class WaterfallEmitterSettings(bpy.types.PropertyGroup):
        speed: bpy.props.FloatProperty(name="Speed", default=8.0, min=0.0, update=_refresh_from_emitter)
        direction_axis: bpy.props.EnumProperty(
            name="Direction Axis",
            items=[
                ("NEG_Z", "-Z", "Use local -Z as initial velocity direction"),
                ("POS_Y", "+Y", "Use local +Y as initial velocity direction"),
                ("NEG_Y", "-Y", "Use local -Y as initial velocity direction"),
            ],
            default="NEG_Z",
            update=_refresh_from_emitter,
        )
        gravity: bpy.props.FloatProperty(name="Gravity", default=9.81, min=0.0, update=_refresh_from_emitter)
        drag: bpy.props.FloatProperty(name="Drag", default=0.0, min=0.0, update=_refresh_from_emitter)
        simulation_step_count: bpy.props.IntProperty(name="Simulation Steps", default=80, min=1, update=_refresh_from_emitter)
        simulation_time_step: bpy.props.FloatProperty(name="Time Step", default=0.05, min=0.001, update=_refresh_from_emitter)
        attach_strength: bpy.props.FloatProperty(name="Attach Strength", default=0.7, min=0.0, max=1.0, update=_refresh_from_emitter)
        detach_threshold: bpy.props.FloatProperty(name="Detach Threshold", default=0.35, min=0.0, max=1.0, update=_refresh_from_emitter)
        preview_enabled: bpy.props.BoolProperty(name="Preview Enabled", default=True, update=_refresh_from_emitter)
        flow_curve_name: bpy.props.StringProperty(name="Flow Curve")


    class WaterfallCurveSettings(bpy.types.PropertyGroup):
        curve_mode: bpy.props.EnumProperty(
            name="Curve Mode",
            items=[
                ("MANUAL_SHAPE", "Manual Shape", "Use the edited curve directly"),
                ("PHYSICS_ASSISTED", "Physics Assisted", "Re-apply collision correction from edited points"),
            ],
            default="MANUAL_SHAPE",
            update=_refresh_from_curve,
        )
        preview_enabled: bpy.props.BoolProperty(name="Preview Enabled", default=True, update=_refresh_from_curve)
        base_segment_density: bpy.props.FloatProperty(name="Base Segment Density", default=1.0, min=0.1, update=_refresh_from_curve)
        curvature_refine_strength: bpy.props.FloatProperty(name="Curvature Refine Strength", default=1.0, min=0.0, update=_refresh_from_curve)
        start_width: bpy.props.FloatProperty(name="Start Width", default=1.0, min=0.0, update=_refresh_from_curve)
        end_width: bpy.props.FloatProperty(name="End Width", default=1.0, min=0.0, update=_refresh_from_curve)
        width_falloff: bpy.props.FloatProperty(name="Width Falloff", default=1.0, min=0.001, update=_refresh_from_curve)
        cross_angle: bpy.props.FloatProperty(name="Cross Angle", default=90.0, min=1.0, max=179.0, update=_refresh_from_curve)
        uv_speed_scale: bpy.props.FloatProperty(name="UV Speed Scale", default=1.0, min=0.0, update=_refresh_from_curve)
        emitter_name: bpy.props.StringProperty(name="Emitter")
        preview_mesh_name: bpy.props.StringProperty(name="Preview Mesh")
        baked_mesh_name: bpy.props.StringProperty(name="Baked Mesh")

else:

    class WaterfallEmitterSettings:
        pass


    class WaterfallCurveSettings:
        pass
