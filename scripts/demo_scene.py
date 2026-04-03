from __future__ import annotations

from pathlib import Path
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "addon"))

import bpy
from mathutils import Vector

import waterfall_tool
from waterfall_tool.demo.framing import compute_demo_camera_frame


CACHE_DIR = ROOT / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR = ROOT / "exports" / "demo"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def require_object(name: str) -> bpy.types.Object:
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f"Required object '{name}' not found. Scene generation likely failed.")
    return obj


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Z").to_euler()


def create_material(name: str, color: tuple[float, float, float, float], roughness: float = 0.45) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    return material


def world_bounds(obj: bpy.types.Object) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return (
        (min(corner.x for corner in corners), min(corner.y for corner in corners), min(corner.z for corner in corners)),
        (max(corner.x for corner in corners), max(corner.y for corner in corners), max(corner.z for corner in corners)),
    )


def combined_bounds(objects: list[bpy.types.Object]) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    mins = []
    maxs = []
    for obj in objects:
        min_corner, max_corner = world_bounds(obj)
        mins.append(min_corner)
        maxs.append(max_corner)

    return (
        (min(value[0] for value in mins), min(value[1] for value in mins), min(value[2] for value in mins)),
        (max(value[0] for value in maxs), max(value[1] for value in maxs), max(value[2] for value in maxs)),
    )


def main() -> None:
    clear_scene()
    waterfall_tool.register()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.eevee.taa_render_samples = 32
    scene.eevee.taa_samples = 16

    world = scene.world
    world.use_nodes = True
    background = world.node_tree.nodes["Background"]
    background.inputs["Color"].default_value = (0.88, 0.93, 0.98, 1.0)
    background.inputs["Strength"].default_value = 0.9

    # Terrace terrain axis (required by wft.generate_terrace_terrain poll).
    axis_curve = bpy.data.curves.new("DemoTerrainAxisCurve", type="CURVE")
    axis_curve.dimensions = "3D"
    axis_spline = axis_curve.splines.new("POLY")
    axis_points = [
        (-4.5, -2.2, 4.9),
        (0.0, 0.35, 4.7),
        (4.3, 2.6, 4.35),
    ]
    axis_spline.points.add(len(axis_points) - 1)
    for index, point in enumerate(axis_points):
        axis_spline.points[index].co = (*point, 1.0)

    axis = bpy.data.objects.new("DemoTerrainAxis", axis_curve)
    bpy.context.scene.collection.objects.link(axis)

    camera_data = bpy.data.cameras.new("DemoCamera")
    camera = bpy.data.objects.new("DemoCamera", camera_data)
    camera.location = (0.0, -8.5, 2.4)
    look_at(camera, Vector((0.0, 0.0, 1.8)))
    bpy.context.scene.collection.objects.link(camera)
    scene.camera = camera

    sun_data = bpy.data.lights.new("DemoSun", type="SUN")
    sun_data.energy = 2.5
    sun = bpy.data.objects.new("DemoSun", sun_data)
    sun.rotation_euler = (math.radians(50), math.radians(0), math.radians(25))
    bpy.context.scene.collection.objects.link(sun)

    split_guide = bpy.data.objects.new("DemoSplitGuide", None)
    breakup_region = bpy.data.objects.new("DemoBreakupRegion", None)
    bpy.context.scene.collection.objects.link(split_guide)
    bpy.context.scene.collection.objects.link(breakup_region)

    settings = scene.wft_settings
    settings.terrain_axis_object = axis
    settings.terrain_level_count = 3
    settings.terrain_total_drop = 6.0
    settings.terrain_base_width = 8.0
    settings.terrain_depth = 2.8

    settings.preview_steps = 36
    settings.particle_count = 8
    settings.cache_path = str(CACHE_DIR / "demo_preview.json")
    settings.sheet_width = 0.75
    settings.export_directory = str(EXPORT_DIR)
    settings.export_stem = "demo_waterfall"
    settings.split_guide_object = split_guide
    settings.breakup_region_object = breakup_region

    result = bpy.ops.wft.generate_terrace_terrain()
    if result != {"FINISHED"}:
        raise RuntimeError(f"wft.generate_terrace_terrain failed: {result}")

    result = bpy.ops.wft.use_generated_terrain_for_waterfall()
    if result != {"FINISHED"}:
        raise RuntimeError(f"wft.use_generated_terrain_for_waterfall failed: {result}")

    terrain = require_object("WFT_Terrain_MainTerrain")
    terrain.data.materials.append(create_material("CliffMat", (0.18, 0.20, 0.23, 1.0), roughness=0.8))

    result = bpy.ops.wft.generate_preview()
    if result != {"FINISHED"}:
        raise RuntimeError(f"wft.generate_preview failed: {result}")
    preview = require_object("WFT_PreviewPaths")
    preview.data.bevel_depth = 0.03
    preview.data.bevel_resolution = 3
    preview.data.materials.append(create_material("PreviewMat", (0.12, 0.55, 1.0, 1.0), roughness=0.2))

    result = bpy.ops.wft.bake_preview()
    if result != {"FINISHED"}:
        raise RuntimeError(f"wft.bake_preview failed: {result}")

    result = bpy.ops.wft.rebuild_waterfall()
    if result != {"FINISHED"}:
        raise RuntimeError(f"wft.rebuild_waterfall failed: {result}")

    ribbon = require_object("WFT_MainSheet")
    ribbon.location.y = -0.06
    ribbon.data.materials.append(create_material("RibbonMat", (0.25, 0.74, 0.97, 1.0), roughness=0.15))

    bounds_min, bounds_max = combined_bounds([terrain, ribbon, preview])
    frame = compute_demo_camera_frame(bounds_min, bounds_max)
    camera.location = frame.location
    look_at(camera, Vector(frame.target))

    # Background renders have no screen; guard for UI usage.
    screen = getattr(bpy.context, "screen", None)
    if screen is not None:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.shading.type = "MATERIAL"

    print("Waterfall demo scene loaded.")


if __name__ == "__main__":
    main()
