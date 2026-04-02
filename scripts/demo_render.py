from __future__ import annotations

from pathlib import Path
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "addon"))

import bpy
from mathutils import Vector

import waterfall_tool


OUTPUT_DIR = ROOT / "exports" / "demo"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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


def create_demo_scene():
    clear_scene()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.film_transparent = False

    world = scene.world
    world.use_nodes = True
    background = world.node_tree.nodes["Background"]
    background.inputs["Color"].default_value = (0.88, 0.93, 0.98, 1.0)
    background.inputs["Strength"].default_value = 0.9

    cliff_mesh = bpy.data.meshes.new("DemoCliffMesh")
    cliff_mesh.from_pydata(
        [
            (-4.5, 0.0, 5.0),
            (4.5, 0.0, 5.0),
            (4.5, 0.0, -4.0),
            (-4.5, 0.0, -4.0),
        ],
        [],
        [(0, 1, 2, 3)],
    )
    cliff = bpy.data.objects.new("DemoCliff", cliff_mesh)
    cliff.data.materials.append(create_material("CliffMat", (0.18, 0.20, 0.23, 1.0), roughness=0.8))
    bpy.context.scene.collection.objects.link(cliff)

    curve_data = bpy.data.curves.new("DemoEmitterCurve", type="CURVE")
    curve_data.dimensions = "3D"
    spline = curve_data.splines.new("POLY")
    emitter_points = [
        (-3.5, 0.05, 4.3),
        (-2.5, 0.05, 4.15),
        (-1.5, 0.05, 4.0),
        (-0.5, 0.05, 4.1),
        (0.5, 0.05, 4.2),
        (1.5, 0.05, 4.05),
        (2.5, 0.05, 4.15),
        (3.5, 0.05, 4.0),
    ]
    spline.points.add(len(emitter_points) - 1)
    for index, point in enumerate(emitter_points):
        spline.points[index].co = (*point, 1.0)

    emitter = bpy.data.objects.new("DemoEmitter", curve_data)
    bpy.context.scene.collection.objects.link(emitter)

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

    return emitter, cliff


def render_image(path: Path) -> None:
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    emitter, cliff = create_demo_scene()
    waterfall_tool.register()

    settings = bpy.context.scene.wft_settings
    settings.emitter_object = emitter
    settings.collider_object = cliff
    settings.preview_steps = 36
    settings.particle_count = 8
    settings.cache_path = str(OUTPUT_DIR / "demo_cache.json")
    settings.sheet_width = 0.75
    settings.export_directory = str(OUTPUT_DIR)
    settings.export_stem = "demo_waterfall"

    split_guide = bpy.data.objects.new("DemoSplitGuide", None)
    breakup_region = bpy.data.objects.new("DemoBreakupRegion", None)
    bpy.context.scene.collection.objects.link(split_guide)
    bpy.context.scene.collection.objects.link(breakup_region)
    settings.split_guide_object = split_guide
    settings.breakup_region_object = breakup_region

    result = bpy.ops.wft.generate_preview()
    assert result == {"FINISHED"}
    preview = bpy.data.objects["WFT_PreviewPaths"]
    preview.data.bevel_depth = 0.03
    preview.data.bevel_resolution = 3
    preview.data.materials.append(create_material("PreviewMat", (0.12, 0.55, 1.0, 1.0), roughness=0.2))

    render_image(OUTPUT_DIR / "preview.png")

    result = bpy.ops.wft.bake_preview()
    assert result == {"FINISHED"}
    result = bpy.ops.wft.rebuild_waterfall()
    assert result == {"FINISHED"}

    if "WFT_PreviewPaths" in bpy.data.objects:
        bpy.data.objects["WFT_PreviewPaths"].hide_render = True
        bpy.data.objects["WFT_PreviewPaths"].hide_viewport = True

    ribbon = bpy.data.objects["WFT_MainSheet"]
    ribbon.data.materials.append(create_material("RibbonMat", (0.25, 0.74, 0.97, 1.0), roughness=0.15))
    ribbon.location.y = -0.06

    render_image(OUTPUT_DIR / "rebuild.png")

    bpy.ops.wft.export_waterfall()

    print(f"Preview image: {OUTPUT_DIR / 'preview.png'}")
    print(f"Rebuild image: {OUTPUT_DIR / 'rebuild.png'}")
    print(f"Export GLB: {OUTPUT_DIR / 'demo_waterfall.glb'}")


if __name__ == "__main__":
    main()
