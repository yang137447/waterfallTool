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
    return getattr(obj, "type", None) == "EMPTY"


def _is_flow_curve_object(obj) -> bool:
    getter = getattr(obj, "get", None)
    return getattr(obj, "type", None) == "CURVE" and callable(getter) and bool(getter("waterfall_flow_curve"))


def _is_preview_mesh_object(obj) -> bool:
    getter = getattr(obj, "get", None)
    return getattr(obj, "type", None) == "MESH" and callable(getter) and bool(getter("waterfall_generated"))


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
    if is_preview_mesh_empty(mesh):
        set_preview_hidden(curve, _scene_objects(), hidden=True)
        return None
    preview = create_or_update_mesh_object(context, preview_name, mesh, generated=True, parent=curve)
    props.preview_mesh_name = preview.name
    visible = props.preview_enabled if force_visible is None else bool(force_visible)
    _set_object_hidden(preview, not visible)
    return preview


if bpy is not None:

    def depsgraph_refresh(scene, depsgraph):
        context = bpy.context
        for update in depsgraph.updates:
            obj = getattr(update, "id", None)
            if getattr(obj, "type", None) == "CURVE" and obj.get("waterfall_flow_curve"):
                refresh_curve_preview(obj, context)
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
