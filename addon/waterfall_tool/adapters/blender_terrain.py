from __future__ import annotations

import bpy
import mathutils

from ..terrain.blueprint import build_terrace_levels
from ..terrain.emitters import build_suggested_emitters
from ..terrain.layout import build_blocker_masses, build_gap_segments, build_lip_curves
from ..terrain.mesh import build_main_terrain_mesh
from ..terrain.types import TerrainBlueprint

DEFAULT_WIDTH_DECAY = 0.1
DEFAULT_DEPTH_DECAY = 0.12
DEFAULT_LIP_ROUNDNESS = 0.4
DEFAULT_GAP_FREQUENCY = 0.25
DEFAULT_BLOCKER_DENSITY = 0.3
DEFAULT_SEED = 7

GENERATED_TERRAIN_COLLECTION_NAME = "WFT_Terrain_Generated"
TEMP_COLLECTION_NAME = "WFT_Terrain_Generated__temp"
GENERATED_TAG_KEY = "wft_generated_terrain"


def read_axis_points(axis_object: bpy.types.Object) -> list[tuple[float, float, float]]:
    if axis_object is None:
        raise ValueError("Terrain axis object is not set")
    if axis_object.type != "CURVE":
        raise ValueError(f"Terrain axis object must be a Curve, got: {axis_object.type}")
    if axis_object.data is None or not getattr(axis_object.data, "splines", None):
        raise ValueError("Terrain axis curve has no splines")
    if len(axis_object.data.splines) < 1:
        raise ValueError("Terrain axis curve must have at least one spline")

    spline = axis_object.data.splines[0]
    spline_type = getattr(spline, "type", None)
    if spline_type == "BEZIER":
        if not getattr(spline, "bezier_points", None) or len(spline.bezier_points) < 2:
            raise ValueError("Terrain axis Bezier spline must have at least 2 bezier points")
        points = [mathutils.Vector(point.co[:3]) for point in spline.bezier_points]
    elif spline_type in {"POLY", "NURBS"}:
        if not getattr(spline, "points", None) or len(spline.points) < 2:
            raise ValueError(f"Terrain axis {spline_type} spline must have at least 2 points")
        points = [mathutils.Vector(point.co[:3]) for point in spline.points]
    else:
        raise ValueError(f"Unsupported terrain axis spline type: {spline_type!r} (use Poly, Nurbs, or Bezier)")

    return [tuple(axis_object.matrix_world @ point) for point in points]


def _ensure_collection(scene: bpy.types.Scene, name: str) -> bpy.types.Collection:
    existing = bpy.data.collections.get(name)
    if existing is None:
        existing = bpy.data.collections.new(name)
    if existing.name not in {child.name for child in scene.collection.children}:
        scene.collection.children.link(existing)
    return existing


def _remove_collection_if_present(scene: bpy.types.Scene, name: str) -> None:
    col = bpy.data.collections.get(name)
    if col is None:
        return
    for child in list(scene.collection.children):
        if child == col:
            scene.collection.children.unlink(col)
            break
    bpy.data.collections.remove(col)


def _cleanup_generated_collection_outputs(collection: bpy.types.Collection) -> None:
    # Only remove outputs that were created/tagged by this generator inside the dedicated collection.
    for obj in list(collection.objects):
        if not obj.get(GENERATED_TAG_KEY, False):
            continue

        data = getattr(obj, "data", None)
        bpy.data.objects.remove(obj, do_unlink=True)
        if data is None:
            continue
        try:
            if hasattr(data, "users") and data.users == 0:
                if isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)
                elif isinstance(data, bpy.types.Curve):
                    bpy.data.curves.remove(data)
        except ReferenceError:
            pass


def build_blueprint_from_scene(settings) -> TerrainBlueprint:
    axis_points = read_axis_points(settings.terrain_axis_object)
    top_elevation = max(point[2] for point in axis_points)
    return TerrainBlueprint(
        axis_points=axis_points,
        level_count=settings.terrain_level_count,
        top_elevation=top_elevation,
        total_drop=settings.terrain_total_drop,
        base_width=settings.terrain_base_width,
        terrace_depth=settings.terrain_depth,
        width_decay=DEFAULT_WIDTH_DECAY,
        depth_decay=DEFAULT_DEPTH_DECAY,
        lip_roundness=DEFAULT_LIP_ROUNDNESS,
        gap_frequency=DEFAULT_GAP_FREQUENCY,
        blocker_density=DEFAULT_BLOCKER_DENSITY,
        seed=DEFAULT_SEED,
    )


def create_terrain_objects(context: bpy.types.Context, settings) -> None:
    # Build and validate first (pure Python pipeline + axis validation). Only replace outputs if
    # replacement objects are created successfully.
    blueprint = build_blueprint_from_scene(settings)
    levels = build_terrace_levels(blueprint)
    lips = build_lip_curves(levels, blueprint)
    gaps = build_gap_segments(lips, blueprint)
    blockers = build_blocker_masses(levels, lips, gaps, blueprint)
    mesh_payload = build_main_terrain_mesh(levels, lips, blockers)
    emitters = build_suggested_emitters(lips, gaps)

    scene = context.scene
    generated_collection = _ensure_collection(scene, GENERATED_TERRAIN_COLLECTION_NAME)

    # Clean up any prior temp collection up front (safe: it's not part of approved outputs).
    _remove_collection_if_present(scene, TEMP_COLLECTION_NAME)
    temp_collection = _ensure_collection(scene, TEMP_COLLECTION_NAME)

    mesh = bpy.data.meshes.new("WFT_Terrain__TMP_MainTerrainMesh")
    mesh.from_pydata(mesh_payload.vertices, [], mesh_payload.faces)
    mesh.update()
    terrain_object = bpy.data.objects.new("WFT_Terrain__TMP_MainTerrain", mesh)
    terrain_object[GENERATED_TAG_KEY] = True
    temp_collection.objects.link(terrain_object)

    for index, emitter in enumerate(emitters):
        curve_data = bpy.data.curves.new(f"WFT_Terrain__TMP_SuggestedEmitterCurve_{index:02d}", type="CURVE")
        curve_data.dimensions = "3D"
        spline = curve_data.splines.new("POLY")
        spline.points.add(len(emitter.points) - 1)
        for point_index, point in enumerate(emitter.points):
            spline.points[point_index].co = (*point, 1.0)
        emitter_object = bpy.data.objects.new(f"WFT_Terrain__TMP_SuggestedEmitter_{index:02d}", curve_data)
        emitter_object[GENERATED_TAG_KEY] = True
        temp_collection.objects.link(emitter_object)

    # Replace outputs: only now do we remove prior generated outputs and promote temp outputs.
    _cleanup_generated_collection_outputs(generated_collection)

    for obj in list(temp_collection.objects):
        # Move to the generated collection and rename to stable final names.
        generated_collection.objects.link(obj)
        temp_collection.objects.unlink(obj)
        if obj.name == "WFT_Terrain__TMP_MainTerrain":
            obj.name = "WFT_Terrain_MainTerrain"
            if obj.data is not None:
                obj.data.name = "WFT_Terrain_MainTerrainMesh"
        elif obj.name.startswith("WFT_Terrain__TMP_SuggestedEmitter_"):
            obj.name = obj.name.replace("WFT_Terrain__TMP_SuggestedEmitter_", "WFT_Terrain_SuggestedEmitter_")
            if obj.data is not None:
                obj.data.name = obj.data.name.replace(
                    "WFT_Terrain__TMP_SuggestedEmitterCurve_",
                    "WFT_Terrain_SuggestedEmitterCurve_",
                )

    _remove_collection_if_present(scene, TEMP_COLLECTION_NAME)
