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
    if not getattr(spline, "points", None) or len(spline.points) < 2:
        raise ValueError("Terrain axis spline must have at least 2 points")

    return [tuple(axis_object.matrix_world @ mathutils.Vector(point.co[:3])) for point in spline.points]


def _cleanup_existing_terrain_outputs() -> None:
    # Remove prior outputs so repeated generation is stable and does not create .001 duplicates.
    for obj in list(bpy.data.objects):
        if not obj.name.startswith("WFT_Terrain_"):
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
            # Data may already be gone; ignore.
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
    _cleanup_existing_terrain_outputs()
    blueprint = build_blueprint_from_scene(settings)
    levels = build_terrace_levels(blueprint)
    lips = build_lip_curves(levels, blueprint)
    gaps = build_gap_segments(lips, blueprint)
    blockers = build_blocker_masses(levels, lips, gaps, blueprint)
    mesh_payload = build_main_terrain_mesh(levels, lips, blockers)
    emitters = build_suggested_emitters(lips, gaps)

    mesh = bpy.data.meshes.new("WFT_Terrain_MainTerrainMesh")
    mesh.from_pydata(mesh_payload.vertices, [], mesh_payload.faces)
    mesh.update()
    terrain_object = bpy.data.objects.new("WFT_Terrain_MainTerrain", mesh)
    context.scene.collection.objects.link(terrain_object)

    for index, emitter in enumerate(emitters):
        curve_data = bpy.data.curves.new(f"WFT_Terrain_SuggestedEmitterCurve_{index:02d}", type="CURVE")
        curve_data.dimensions = "3D"
        spline = curve_data.splines.new("POLY")
        spline.points.add(len(emitter.points) - 1)
        for point_index, point in enumerate(emitter.points):
            spline.points[point_index].co = (*point, 1.0)
        emitter_object = bpy.data.objects.new(f"WFT_Terrain_SuggestedEmitter_{index:02d}", curve_data)
        context.scene.collection.objects.link(emitter_object)
