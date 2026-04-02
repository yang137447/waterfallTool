from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "addon"))

import bpy  # noqa: E402
import waterfall_tool  # noqa: E402

waterfall_tool.register()

from waterfall_tool.adapters.blender_terrain import (  # noqa: E402
    GENERATED_TAG_KEY,
    GENERATED_TERRAIN_COLLECTION_NAME,
    build_blueprint_from_scene,
    read_lip_overrides,
)
from waterfall_tool.terrain.blueprint import build_terrace_levels  # noqa: E402
from waterfall_tool.terrain.emitters import build_suggested_emitters, choose_handoff_emitter_name  # noqa: E402
from waterfall_tool.terrain.layout import build_gap_segments, build_lip_curves  # noqa: E402
from waterfall_tool.terrain.overrides import apply_lip_overrides  # noqa: E402

curve_data = bpy.data.curves.new("TerrainAxis", type="CURVE")
curve_data.dimensions = "3D"
spline = curve_data.splines.new("POLY")
spline.points.add(2)
spline.points[0].co = (-4.0, 0.0, 4.0, 1.0)
spline.points[1].co = (0.0, 0.0, 2.5, 1.0)
spline.points[2].co = (4.0, 0.0, 4.0, 1.0)
axis = bpy.data.objects.new("TerrainAxis", curve_data)
bpy.context.scene.collection.objects.link(axis)

settings = bpy.context.scene.wft_settings
settings.terrain_axis_object = axis

assert bpy.ops.wft.generate_terrace_terrain() == {"FINISHED"}

generated_collection = bpy.data.collections.get(GENERATED_TERRAIN_COLLECTION_NAME)
generated_collection = next(
    (child for child in bpy.context.scene.collection.children if child.name == GENERATED_TERRAIN_COLLECTION_NAME),
    generated_collection,
)
assert generated_collection is not None
tagged_objects = {obj.name: obj for obj in generated_collection.objects if obj.get(GENERATED_TAG_KEY, False)}
expected_terrain = tagged_objects.get("WFT_Terrain_MainTerrain")
assert expected_terrain is not None

blueprint = build_blueprint_from_scene(settings)
levels = build_terrace_levels(blueprint)
lips = build_lip_curves(levels, blueprint)
overrides = read_lip_overrides(settings.terrain_override_collection)
lips = apply_lip_overrides(lips, overrides)
gaps = build_gap_segments(lips, blueprint)
emitters = build_suggested_emitters(lips, gaps)
object_names = [f"WFT_Terrain_SuggestedEmitter_{index:02d}" for index in range(len(emitters))]
expected_emitter_name = choose_handoff_emitter_name(object_names, emitters)
expected_emitter = tagged_objects.get(expected_emitter_name)
assert expected_emitter is not None

assert bpy.ops.wft.use_generated_terrain_for_waterfall() == {"FINISHED"}
assert settings.emitter_object == expected_emitter
assert settings.collider_object == expected_terrain
assert bpy.ops.wft.generate_preview() == {"FINISHED"}
assert bpy.data.objects.get("WFT_PreviewPaths") is not None
print("WFT terrain handoff smoke test completed")
