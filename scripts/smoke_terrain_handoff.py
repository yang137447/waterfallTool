from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "addon"))

import bpy  # noqa: E402
import waterfall_tool  # noqa: E402

waterfall_tool.register()

from waterfall_tool.adapters.blender_terrain import GENERATED_TAG_KEY, GENERATED_TERRAIN_COLLECTION_NAME  # noqa: E402
from waterfall_tool.terrain.emitters import choose_handoff_emitter_name  # noqa: E402
from waterfall_tool.terrain.types import SuggestedEmitter  # noqa: E402

import mathutils  # noqa: E402

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
stack = [bpy.context.scene.collection]
while stack and (generated_collection is None or generated_collection.name != GENERATED_TERRAIN_COLLECTION_NAME):
    collection = stack.pop()
    if collection.name == GENERATED_TERRAIN_COLLECTION_NAME:
        generated_collection = collection
        break
    stack.extend(list(collection.children))
assert generated_collection is not None
tagged_objects = {obj.name: obj for obj in generated_collection.objects if obj.get(GENERATED_TAG_KEY, False)}
expected_terrain = tagged_objects.get("WFT_Terrain_MainTerrain")
assert expected_terrain is not None

emitter_objects = [
    obj
    for obj in tagged_objects.values()
    if obj.name.startswith("WFT_Terrain_SuggestedEmitter_") and obj.type == "CURVE"
]
assert emitter_objects, "Expected at least one generated emitter object"

# Validate the new metadata path: generator should persist selection-relevant fields on objects.
emitters: list[SuggestedEmitter] = []
object_names: list[str] = []
for obj in sorted(emitter_objects, key=lambda item: int(item.get("wft_emitter_index", -1))):
    assert "wft_strength" in obj, "Missing emitter strength metadata"
    assert "wft_level_index" in obj, "Missing emitter level_index metadata"

    points = []
    spline = obj.data.splines[0]
    if spline.type == "BEZIER":
        raw_points = getattr(spline, "bezier_points", None) or []
        for point in raw_points:
            points.append(tuple(obj.matrix_world @ mathutils.Vector(point.co[:3])))
    else:
        raw_points = getattr(spline, "points", None) or []
        for point in raw_points:
            points.append(tuple(obj.matrix_world @ mathutils.Vector(point.co[:3])))
    assert len(points) >= 2, f"Expected >=2 points for {obj.name}, got {len(points)}"

    emitters.append(
        SuggestedEmitter(
            level_index=int(obj["wft_level_index"]),
            points=points,
            strength=float(obj["wft_strength"]),
            enabled=True,
        )
    )
    object_names.append(obj.name)

expected_emitter_name = choose_handoff_emitter_name(object_names, emitters)
expected_emitter = tagged_objects.get(expected_emitter_name)
assert expected_emitter is not None

assert bpy.ops.wft.use_generated_terrain_for_waterfall() == {"FINISHED"}
assert settings.emitter_object == expected_emitter
assert settings.collider_object == expected_terrain
assert bpy.ops.wft.generate_preview() == {"FINISHED"}
assert bpy.data.objects.get("WFT_PreviewPaths") is not None
print("WFT terrain handoff smoke test completed")
