from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "addon"))

import bpy
import waterfall_tool

waterfall_tool.register()

curve_data = bpy.data.curves.new("TerrainAxis", type="CURVE")
curve_data.dimensions = "3D"
spline = curve_data.splines.new("POLY")
spline.points.add(2)
# Use a top elevation that's not the default/hardcoded value so the test
# catches regressions where top_elevation is not derived from axis points.
spline.points[0].co = (-4.0, 0.0, 9.0, 1.0)
spline.points[1].co = (0.0, 0.0, 7.5, 1.0)
spline.points[2].co = (4.0, 0.0, 9.0, 1.0)
axis = bpy.data.objects.new("TerrainAxis", curve_data)
bpy.context.scene.collection.objects.link(axis)

settings = bpy.context.scene.wft_settings
settings.terrain_axis_object = axis

result = bpy.ops.wft.generate_terrace_terrain()
assert result == {"FINISHED"}
assert bpy.data.objects.get("WFT_Terrain_MainTerrain") is not None
assert bpy.data.objects.get("WFT_Terrain_SuggestedEmitter_00") is not None

# Repeated generation should not accumulate .001 duplicates.
result = bpy.ops.wft.generate_terrace_terrain()
assert result == {"FINISHED"}
assert bpy.data.objects.get("WFT_Terrain_MainTerrain.001") is None
assert bpy.data.objects.get("WFT_Terrain_SuggestedEmitter_00.001") is None

# Simple geometry invariant: terrain mesh should reflect the axis top elevation (~9.0).
terrain = bpy.data.objects.get("WFT_Terrain_MainTerrain")
assert terrain is not None
assert terrain.type == "MESH"
max_z = max(v.co.z for v in terrain.data.vertices)
assert max_z > 8.0
print("WFT terrain generate smoke test completed")
