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

CURVE_STYLE_FIELDS = (
    "curve_mode",
    "preview_enabled",
    "width_density",
    "longitudinal_step_length",
    "curvature_min_angle_degrees",
    "start_width",
    "end_width",
    "width_falloff",
    "base_width",
    "speed_expansion",
    "enable_cross_strip",
    "cross_angle",
    "cross_width_scale",
    "cross_ramp_length",
    "uv_base_speed",
    "uv_speed_smoothing_length",
)


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


def _is_flow_curve_owned_by_emitter(curve_obj, emitter_name: str) -> bool:
    if curve_obj is None:
        return False
    if getattr(curve_obj, "type", None) != "CURVE":
        return False
    getter = getattr(curve_obj, "get", None)
    if not callable(getter) or not getter("waterfall_flow_curve"):
        return False
    curve_props = getattr(curve_obj, "waterfall_curve", None)
    if curve_props is None:
        return False
    owner_name = getattr(curve_props, "emitter_name", "")
    return owner_name == emitter_name


def _pick_unique_curve_name(base_name: str, data_objects) -> str:
    if getattr(data_objects, "get", None) is None:
        return base_name
    if data_objects.get(base_name) is None:
        return base_name
    suffix = 1
    while True:
        candidate = f"{base_name}.{suffix:03d}"
        if data_objects.get(candidate) is None:
            return candidate
        suffix += 1


def _resolve_curve_name_for_emitter(emitter, data_objects) -> str:
    emitter_name = getattr(emitter, "name", "")
    emitter_props = getattr(emitter, "waterfall_emitter", None)
    requested_name = getattr(emitter_props, "flow_curve_name", "") if emitter_props is not None else ""

    if requested_name:
        existing = data_objects.get(requested_name) if getattr(data_objects, "get", None) else None
        if existing is None:
            return requested_name
        if _is_flow_curve_owned_by_emitter(existing, emitter_name):
            return requested_name

    base_name = f"{emitter_name}_FlowCurve"
    existing_base = data_objects.get(base_name) if getattr(data_objects, "get", None) else None
    if existing_base is None or _is_flow_curve_owned_by_emitter(existing_base, emitter_name):
        return base_name
    return _pick_unique_curve_name(base_name, data_objects)


def _resolve_source_curve_template(emitter, data_objects):
    emitter_name = getattr(emitter, "name", "")
    emitter_props = getattr(emitter, "waterfall_emitter", None)
    requested_name = getattr(emitter_props, "flow_curve_name", "") if emitter_props is not None else ""
    if not requested_name:
        return None
    existing = data_objects.get(requested_name) if getattr(data_objects, "get", None) else None
    if existing is None:
        return None
    if _is_flow_curve_owned_by_emitter(existing, emitter_name):
        return None
    return existing


def _copy_curve_style_from_template(source_curve, target_curve) -> None:
    source_props = getattr(source_curve, "waterfall_curve", None)
    target_props = getattr(target_curve, "waterfall_curve", None)
    if source_props is None or target_props is None:
        return
    for field_name in CURVE_STYLE_FIELDS:
        if hasattr(source_props, field_name) and hasattr(target_props, field_name):
            setattr(target_props, field_name, getattr(source_props, field_name))


def _resolve_preview_mesh_object(curve_obj, data_objects):
    curve_props = getattr(curve_obj, "waterfall_curve", None)
    preview_name = getattr(curve_props, "preview_mesh_name", "") if curve_props is not None else ""
    if not preview_name:
        return None
    preview_obj = data_objects.get(preview_name) if getattr(data_objects, "get", None) else None
    if preview_obj is None or getattr(preview_obj, "type", None) != "MESH":
        return None
    return preview_obj


def _copy_preview_materials(source_preview, target_preview) -> None:
    source_mesh = getattr(source_preview, "data", None)
    target_mesh = getattr(target_preview, "data", None)
    source_materials = getattr(source_mesh, "materials", None)
    target_materials = getattr(target_mesh, "materials", None)
    if source_materials is None or target_materials is None:
        return
    target_materials.clear()
    for material in source_materials:
        target_materials.append(material)


def generate_or_resimulate_curve(emitter, context):
    from ..adapters.blender_curve import create_or_update_flow_curve
    from ..adapters.blender_scene import BlenderVisibleMeshCollisionProvider
    from ..operators.preview import refresh_curve_preview

    if emitter is None or getattr(emitter, "waterfall_emitter", None) is None:
        return None

    props = emitter.waterfall_emitter
    if not getattr(props, "enabled", False):
        return None
    source_curve_template = _resolve_source_curve_template(emitter, bpy.data.objects)
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
        surface_flow_radius=getattr(global_settings, "surface_flow_radius", 0.35),
        surface_flow_samples=getattr(global_settings, "surface_flow_samples", 8),
        surface_flow_relaxation=getattr(global_settings, "surface_flow_relaxation", 0.85),
        surface_flow_inertia=getattr(global_settings, "surface_flow_inertia", 0.7),
    )
    curve_name = _resolve_curve_name_for_emitter(emitter, bpy.data.objects)
    collision_provider = BlenderVisibleMeshCollisionProvider(context, excluded_names={curve_name})
    points = simulate_trajectory(
        tuple(emitter.matrix_world.translation),
        _direction_from_axis(emitter, props.direction_axis),
        settings,
        collision_provider,
    )
    curve = create_or_update_flow_curve(context, curve_name, points, parent=emitter)
    props.flow_curve_name = curve.name
    if source_curve_template is not None:
        _copy_curve_style_from_template(source_curve_template, curve)
    curve.waterfall_curve.emitter_name = emitter.name
    preview = refresh_curve_preview(curve, context)
    if source_curve_template is not None and preview is not None:
        source_preview = _resolve_preview_mesh_object(source_curve_template, bpy.data.objects)
        if source_preview is not None:
            _copy_preview_materials(source_preview, preview)
    return curve


def iter_enabled_emitters(data_objects):
    values = getattr(data_objects, "values", None)
    iterable = values() if callable(values) else data_objects
    for obj in iterable:
        if getattr(obj, "type", None) != "EMPTY":
            continue
        emitter_props = getattr(obj, "waterfall_emitter", None)
        if not emitter_props or not getattr(emitter_props, "enabled", False):
            continue
        yield obj


def generate_all_enabled_emitters(context, data_objects) -> int:
    count = 0
    for emitter in iter_enabled_emitters(data_objects):
        if generate_or_resimulate_curve(emitter, context) is not None:
            count += 1
    return count


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


    class WATERFALL_OT_simulate_all_emitters(bpy.types.Operator):
        bl_idname = "waterfall.simulate_all_emitters"
        bl_label = "Generate All Emitters"
        bl_options = {"REGISTER", "UNDO"}

        def execute(self, context):
            generated_count = generate_all_enabled_emitters(context, bpy.data.objects)
            if generated_count <= 0:
                self.report({"WARNING"}, "No enabled emitter found")
                return {"CANCELLED"}
            self.report({"INFO"}, f"Generated {generated_count} emitter curves")
            return {"FINISHED"}

else:

    class WATERFALL_OT_simulate_curve:
        pass


    class WATERFALL_OT_simulate_all_emitters:
        pass
