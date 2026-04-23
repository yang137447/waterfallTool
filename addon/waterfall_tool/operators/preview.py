from __future__ import annotations

try:
    import bpy
except ModuleNotFoundError:
    bpy = None

from ..core.mesh_builder import build_x_card_mesh
from ..core.trajectory import simulate_guided_trajectory
from ..core.types import EmitterSettings, MeshSettings, TrajectoryPoint


def apply_persistent_handler(handler, bpy_module):
    persistent = getattr(getattr(getattr(bpy_module, "app", None), "handlers", None), "persistent", None)
    if callable(persistent):
        return persistent(handler)
    return handler


def _lookup_object(data_objects, name: str):
    if not name:
        return None
    getter = getattr(data_objects, "get", None)
    if getter is None:
        return None
    return getter(name)


def _is_emitter_object(obj) -> bool:
    emitter_props = getattr(obj, "waterfall_emitter", None)
    return getattr(obj, "type", None) == "EMPTY" and bool(getattr(emitter_props, "enabled", False))


def _is_flow_curve_object(obj) -> bool:
    getter = getattr(obj, "get", None)
    return getattr(obj, "type", None) == "CURVE" and callable(getter) and bool(getter("waterfall_flow_curve"))


def _is_preview_mesh_object(obj) -> bool:
    getter = getattr(obj, "get", None)
    return getattr(obj, "type", None) == "MESH" and callable(getter) and bool(getter("waterfall_generated"))


def resolve_preview_parent(curve, data_objects):
    curve_props = getattr(curve, "waterfall_curve", None)
    emitter = _lookup_object(data_objects, getattr(curve_props, "emitter_name", ""))
    if _is_emitter_object(emitter):
        return emitter
    return curve


def resolve_emitter_curve_targets(selected_obj, data_objects):
    if selected_obj is None:
        return (None, None)

    is_flow_curve = _is_flow_curve_object(selected_obj)
    if is_flow_curve:
        curve = selected_obj
        curve_props = getattr(curve, "waterfall_curve", None)
        emitter = _lookup_object(data_objects, getattr(curve_props, "emitter_name", ""))
        if not _is_emitter_object(emitter):
            emitter = None
        return (emitter, curve)

    if not _is_emitter_object(selected_obj):
        return (None, None)

    emitter = selected_obj
    emitter_props = getattr(emitter, "waterfall_emitter", None)
    curve = _lookup_object(data_objects, getattr(emitter_props, "flow_curve_name", ""))
    if not _is_flow_curve_object(curve):
        curve = None
    return (emitter, curve)


def _set_object_hidden(obj, hidden: bool) -> None:
    hide_set = getattr(obj, "hide_set", None)
    if callable(hide_set):
        hide_set(hidden)
    if hasattr(obj, "hide_viewport"):
        obj.hide_viewport = hidden
    if hasattr(obj, "hide_render"):
        obj.hide_render = hidden


def set_preview_hidden(curve, data_objects, hidden: bool):
    props = getattr(curve, "waterfall_curve", None)
    preview = _lookup_object(data_objects, getattr(props, "preview_mesh_name", ""))
    if not _is_preview_mesh_object(preview):
        return None
    _set_object_hidden(preview, hidden)
    return preview


def is_preview_mesh_empty(mesh) -> bool:
    vertices = getattr(mesh, "vertices", ())
    faces = getattr(mesh, "faces", ())
    return not vertices or not faces


def _scene_objects():
    return getattr(getattr(bpy, "data", None), "objects", None)


def should_refresh_curve_from_update(update) -> bool:
    obj = getattr(update, "id", None)
    return _is_flow_curve_object(obj) and bool(getattr(update, "is_updated_geometry", False))


def _iter_data_objects(data_objects):
    if data_objects is None:
        return ()
    values = getattr(data_objects, "values", None)
    if callable(values):
        return values()
    return data_objects


def resolve_curves_from_update(update, data_objects) -> list:
    if not bool(getattr(update, "is_updated_geometry", False)):
        return []

    obj = getattr(update, "id", None)
    if _is_flow_curve_object(obj):
        return [obj]

    if obj is None:
        return []

    result = []
    for candidate in _iter_data_objects(data_objects):
        if _is_flow_curve_object(candidate) and getattr(candidate, "data", None) is obj:
            result.append(candidate)
    return result


def _should_build_preview_mesh(preview_enabled: bool, allow_when_preview_disabled: bool) -> bool:
    return preview_enabled or allow_when_preview_disabled


def refresh_curve_preview(curve, context, *, allow_when_preview_disabled: bool = False, force_visible: bool | None = None):
    from ..adapters.blender_curve import read_flow_curve_points
    from ..adapters.blender_mesh import create_or_update_mesh_object
    from ..adapters.blender_scene import BlenderVisibleMeshCollisionProvider

    props = curve.waterfall_curve
    if not _should_build_preview_mesh(props.preview_enabled, allow_when_preview_disabled):
        set_preview_hidden(curve, _scene_objects(), hidden=True)
        return None

    positions, speeds = read_flow_curve_points(curve)
    points = [TrajectoryPoint(position=position, velocity=(0.0, 0.0, -speed), speed=speed) for position, speed in zip(positions, speeds, strict=True)]

    if props.curve_mode == "PHYSICS_ASSISTED" and props.emitter_name:
        emitter = bpy.data.objects.get(props.emitter_name)
        if emitter is not None:
            emitter_props = emitter.waterfall_emitter
            scene = getattr(context, "scene", None)
            global_settings = getattr(scene, "waterfall_global", None)
            emitter_settings = EmitterSettings(
                speed=emitter_props.speed,
                gravity=getattr(global_settings, "gravity", 9.81),
                drag=getattr(global_settings, "drag", 0.0),
                time_step=getattr(global_settings, "simulation_time_step", 0.05),
                step_count=getattr(global_settings, "simulation_step_count", 80),
                attach_strength=getattr(global_settings, "attach_strength", 0.7),
                detach_threshold=getattr(global_settings, "detach_threshold", 0.35),
                surface_offset=getattr(global_settings, "surface_offset", 0.01),
                surface_flow_radius=getattr(global_settings, "surface_flow_radius", 0.35),
                surface_flow_samples=getattr(global_settings, "surface_flow_samples", 8),
                surface_flow_relaxation=getattr(global_settings, "surface_flow_relaxation", 0.85),
                surface_flow_inertia=getattr(global_settings, "surface_flow_inertia", 0.7),
            )
            collision_provider = BlenderVisibleMeshCollisionProvider(
                context,
                excluded_names={props.preview_mesh_name, props.baked_mesh_name, curve.name},
            )
            points = simulate_guided_trajectory(positions, speeds, emitter_settings, collision_provider)

    scene = getattr(context, "scene", None)
    global_settings = getattr(scene, "waterfall_global", None)
    mesh_settings = MeshSettings(
        width_density=props.width_density,
        longitudinal_step_length=props.longitudinal_step_length,
        curvature_min_angle_degrees=props.curvature_min_angle_degrees,
        base_width=getattr(props, "base_width", 1.0),
        start_width=props.start_width,
        end_width=props.end_width,
        width_falloff=props.width_falloff,
        speed_expansion=getattr(props, "speed_expansion", 0.0),
        enable_cross_strip=getattr(props, "enable_cross_strip", True),
        cross_angle_degrees=props.cross_angle,
        cross_width_scale=getattr(props, "cross_width_scale", 1.0),
        cross_ramp_length=getattr(props, "cross_ramp_length", 0.0),
        uv_base_speed=props.uv_base_speed,
        uv_speed_smoothing_length=getattr(props, "uv_speed_smoothing_length", 0.0),
        cutoff_height=getattr(global_settings, "cutoff_height", None) if global_settings is not None else None,
        align_end_to_cutoff_plane=True,
    )
    preview_name = props.preview_mesh_name or f"{curve.name}_Preview"
    mesh = build_x_card_mesh(points, mesh_settings)
    if is_preview_mesh_empty(mesh):
        set_preview_hidden(curve, _scene_objects(), hidden=True)
        return None
    preview_parent = resolve_preview_parent(curve, _scene_objects())
    preview = create_or_update_mesh_object(context, preview_name, mesh, generated=True, parent=preview_parent)
    props.preview_mesh_name = preview.name
    visible = props.preview_enabled if force_visible is None else bool(force_visible)
    _set_object_hidden(preview, not visible)
    return preview


if bpy is not None:
    _deferred_emitters = []
    _deferred_curves = []
    _is_timer_registered = False
    _is_processing_deferred_updates = False

    def _process_deferred_updates():
        global _is_timer_registered, _is_processing_deferred_updates
        _is_timer_registered = False
        if _is_processing_deferred_updates:
            return None
        _is_processing_deferred_updates = True
        
        context = bpy.context
        from .simulate import generate_or_resimulate_curve
        
        # Keep a local copy and clear globals to allow new updates to queue
        emitter_names = list(_deferred_emitters)
        curve_names = list(_deferred_curves)
        _deferred_emitters.clear()
        _deferred_curves.clear()
        
        processed_curves = set()

        try:
            for emitter_name in emitter_names:
                emitter = bpy.data.objects.get(emitter_name)
                if emitter is None:
                    continue
                curve = generate_or_resimulate_curve(emitter, context)
                if curve is not None:
                    processed_curves.add(curve.name)

            for curve_name in curve_names:
                if curve_name in processed_curves:
                    continue
                curve = bpy.data.objects.get(curve_name)
                if curve is None or not _is_flow_curve_object(curve):
                    continue
                refresh_curve_preview(curve, context)
                processed_curves.add(curve.name)
        finally:
            _is_processing_deferred_updates = False

        return None # Don't run again

    def depsgraph_refresh(scene, depsgraph):
        global _is_timer_registered
        if _is_processing_deferred_updates:
            return
        
        has_new_updates = False
        
        for update in depsgraph.updates:
            obj = getattr(update, "id", None)
            
            if getattr(update, "is_updated_geometry", False) and getattr(obj, "name", "").endswith("_Preview"):
                continue

            if _is_emitter_object(obj) and getattr(update, "is_updated_transform", False):
                 # 只有当它是真正被设置为 waterfall_emitter 并且已经有相关绑定时才进行更新，防止普通空物体触发更新
                 emitter_props = getattr(obj, "waterfall_emitter", None)
                 if emitter_props and getattr(emitter_props, "flow_curve_name", ""):
                     if obj.name not in _deferred_emitters:
                         _deferred_emitters.append(obj.name)
                         has_new_updates = True
                 
            for curve in resolve_curves_from_update(update, _scene_objects()):
                if curve.name not in _deferred_curves:
                    _deferred_curves.append(curve.name)
                    has_new_updates = True
                
        if has_new_updates and not _is_timer_registered:
            bpy.app.timers.register(_process_deferred_updates, first_interval=0.01)
            _is_timer_registered = True
            
    depsgraph_refresh = apply_persistent_handler(depsgraph_refresh, bpy)


    class WATERFALL_OT_rebuild_preview(bpy.types.Operator):
        bl_idname = "waterfall.rebuild_preview"
        bl_label = "Rebuild Preview"
        bl_options = {"REGISTER", "UNDO"}

        def execute(self, context):
            _emitter, curve = resolve_emitter_curve_targets(context.object, bpy.data.objects)
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
