from __future__ import annotations

try:
    import bpy
except ModuleNotFoundError:
    bpy = None


def _refresh_global_cutoff_guide(_self, _context) -> None:
    if bpy is None or _context is None:
        return
    from .adapters.blender_cutoff_guide import ensure_cutoff_guide

    ensure_cutoff_guide(_context.scene)

def _refresh_from_emitter(_self, _context) -> None:
    if bpy is None or _context is None:
        return
    owner = getattr(_self, "id_data", None)
    if owner is None:
        return

    props = getattr(owner, "waterfall_emitter", None)
    if not props or not getattr(props, "enabled", False) or not props.flow_curve_name:
        return

    from .operators.simulate import generate_or_resimulate_curve
    generate_or_resimulate_curve(owner, _context)


def _refresh_from_curve(_self, _context) -> None:
    if bpy is None or _context is None:
        return
    owner = getattr(_self, "id_data", None)
    if owner is None:
        return

    props = getattr(owner, "waterfall_curve", None)
    if not props or not props.emitter_name:
        return

    from .operators.preview import refresh_curve_preview
    refresh_curve_preview(owner, _context)


if bpy is not None:

    class WaterfallEmitterSettings(bpy.types.PropertyGroup):
        enabled: bpy.props.BoolProperty(name="Enabled", default=False)
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
        width_density: bpy.props.IntProperty(name="Width Density", default=1, min=1, update=_refresh_from_curve)
        longitudinal_step_length: bpy.props.FloatProperty(
            name="Longitudinal Step Length",
            default=0.5,
            min=0.001,
            update=_refresh_from_curve,
        )
        curvature_min_angle_degrees: bpy.props.FloatProperty(
            name="Curvature Min Angle",
            default=15.0,
            min=0.1,
            max=180.0,
            update=_refresh_from_curve,
        )
        start_width: bpy.props.FloatProperty(name="Start Width", default=1.0, min=0.001, update=_refresh_from_curve)
        end_width: bpy.props.FloatProperty(name="End Width", default=1.0, min=0.001, update=_refresh_from_curve)
        width_falloff: bpy.props.FloatProperty(name="Width Falloff", default=1.0, min=0.001, update=_refresh_from_curve)
        base_width: bpy.props.FloatProperty(name="Base Width", default=1.0, min=0.001, update=_refresh_from_curve)
        speed_expansion: bpy.props.FloatProperty(name="Speed Expansion", default=0.0, min=0.0, update=_refresh_from_curve)
        enable_cross_strip: bpy.props.BoolProperty(name="Enable Cross Strip", default=True, update=_refresh_from_curve, description="Enable the vertical cross strip")
        cross_angle: bpy.props.FloatProperty(name="Cross Angle", default=90.0, min=1.0, max=179.0, update=_refresh_from_curve)
        cross_width_scale: bpy.props.FloatProperty(name="Cross Width Scale", default=1.0, min=0.0, update=_refresh_from_curve)
        cross_ramp_length: bpy.props.FloatProperty(
            name="Cross Ramp Length",
            default=1.0,
            min=0.0,
            description="Distance from the lip where cross strip width ramps from thin to full",
            update=_refresh_from_curve,
        )
        uv_base_speed: bpy.props.FloatProperty(name="UV Base Speed", default=8.0, min=0.001, update=_refresh_from_curve)
        uv_speed_smoothing_length: bpy.props.FloatProperty(name="UV Speed Smoothing Length", default=0.0, min=0.0, update=_refresh_from_curve)
        emitter_name: bpy.props.StringProperty(name="Emitter")
        preview_mesh_name: bpy.props.StringProperty(name="Preview Mesh")
        baked_mesh_name: bpy.props.StringProperty(name="Baked Mesh")


    class WaterfallGlobalSettings(bpy.types.PropertyGroup):
        gravity: bpy.props.FloatProperty(name="Gravity", default=9.81, min=0.0)
        drag: bpy.props.FloatProperty(name="Drag", default=0.0, min=0.0)
        simulation_step_count: bpy.props.IntProperty(name="Simulation Steps", default=80, min=1)
        simulation_time_step: bpy.props.FloatProperty(name="Time Step", default=0.05, min=0.001)
        attach_strength: bpy.props.FloatProperty(name="Attach Strength", default=0.7, min=0.0, max=1.0)
        detach_threshold: bpy.props.FloatProperty(name="Detach Threshold", default=0.35, min=0.0, max=1.0)
        surface_offset: bpy.props.FloatProperty(name="Surface Offset", default=0.01, min=0.0, precision=4, description="Distance to keep away from collision surface to avoid mesh intersection")
        surface_flow_radius: bpy.props.FloatProperty(
            name="Surface Flow Radius",
            default=0.35,
            min=0.0,
            description="Neighbor probing radius for building a smoother support surface",
        )
        surface_flow_samples: bpy.props.IntProperty(
            name="Surface Flow Samples",
            default=8,
            min=4,
            max=32,
            description="Number of radial probes used to average local surface shape",
        )
        surface_flow_relaxation: bpy.props.FloatProperty(
            name="Surface Flow Relaxation",
            default=0.85,
            min=0.0,
            max=1.0,
            description="How strongly trajectory points relax toward the smoothed support surface",
        )
        surface_flow_inertia: bpy.props.FloatProperty(
            name="Surface Flow Inertia",
            default=0.7,
            min=0.0,
            max=1.0,
            description="How much attached flow direction keeps previous tangent momentum",
        )
        terminal_speed: bpy.props.FloatProperty(name="Terminal Speed", default=0.0, min=0.0)
        cutoff_height: bpy.props.FloatProperty(
            name="Cutoff Height",
            default=-1000000.0,
            update=_refresh_global_cutoff_guide,
        )
        show_cutoff_guide: bpy.props.BoolProperty(
            name="Show Cutoff Guide",
            default=True,
            update=_refresh_global_cutoff_guide,
        )
        cutoff_offset_x: bpy.props.FloatProperty(name="Cutoff Offset X", default=0.0, update=_refresh_global_cutoff_guide)
        cutoff_offset_y: bpy.props.FloatProperty(name="Cutoff Offset Y", default=0.0, update=_refresh_global_cutoff_guide)
        cutoff_size_x: bpy.props.FloatProperty(
            name="Cutoff Size X",
            default=10.0,
            min=0.001,
            update=_refresh_global_cutoff_guide,
        )
        cutoff_size_y: bpy.props.FloatProperty(
            name="Cutoff Size Y",
            default=10.0,
            min=0.001,
            update=_refresh_global_cutoff_guide,
        )
        ui_global_properties_open: bpy.props.BoolProperty(name="Global Properties Open", default=True)
        ui_global_simulation_open: bpy.props.BoolProperty(name="Global Simulation Open", default=True)
        ui_global_termination_open: bpy.props.BoolProperty(name="Global Termination Open", default=True)
        ui_global_cutoff_guide_open: bpy.props.BoolProperty(name="Global Cutoff Guide Open", default=False)
        ui_object_properties_open: bpy.props.BoolProperty(name="Object Properties Open", default=True)
        ui_object_emitter_open: bpy.props.BoolProperty(name="Object Emitter Open", default=True)
        ui_object_emission_open: bpy.props.BoolProperty(name="Object Emission Open", default=True)
        ui_object_mesh_preview_open: bpy.props.BoolProperty(name="Object Mesh Preview Open", default=True)
        ui_object_density_open: bpy.props.BoolProperty(name="Object Density Open", default=True)
        ui_object_shape_open: bpy.props.BoolProperty(name="Object Shape Open", default=False)
        ui_object_uv_open: bpy.props.BoolProperty(name="Object UV Open", default=False)
        ui_object_bake_open: bpy.props.BoolProperty(name="Object Bake Open", default=False)

else:

    class WaterfallEmitterSettings:
        pass


    class WaterfallCurveSettings:
        pass


    class WaterfallGlobalSettings:
        pass
