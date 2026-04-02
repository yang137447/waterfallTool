from __future__ import annotations

import bpy
import mathutils

from ..terrain.blueprint import build_terrace_levels
from ..terrain.emitters import build_suggested_emitters
from ..terrain.layout import build_blocker_masses, build_gap_segments, build_lip_curves
from ..terrain.mesh import build_main_terrain_mesh
from ..terrain.types import TerrainBlueprint


def read_axis_points(axis_object: bpy.types.Object) -> list[tuple[float, float, float]]:
    spline = axis_object.data.splines[0]
    return [tuple(axis_object.matrix_world @ mathutils.Vector(point.co[:3])) for point in spline.points]


def build_blueprint_from_scene(settings) -> TerrainBlueprint:
    return TerrainBlueprint(
        axis_points=read_axis_points(settings.terrain_axis_object),
        level_count=settings.terrain_level_count,
        top_elevation=4.0,
        total_drop=settings.terrain_total_drop,
        base_width=settings.terrain_base_width,
        terrace_depth=settings.terrain_depth,
        width_decay=0.1,
        depth_decay=0.12,
        lip_roundness=0.4,
        gap_frequency=0.25,
        blocker_density=0.3,
        seed=7,
    )


def create_terrain_objects(context: bpy.types.Context, settings) -> None:
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

