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
spline.points[0].co = (-4.0, 0.0, 4.0, 1.0)
spline.points[1].co = (0.0, 0.0, 2.5, 1.0)
spline.points[2].co = (4.0, 0.0, 4.0, 1.0)
axis = bpy.data.objects.new("TerrainAxis", curve_data)
bpy.context.scene.collection.objects.link(axis)

settings = bpy.context.scene.wft_settings
settings.terrain_axis_object = axis

result = bpy.ops.wft.generate_terrace_terrain()
assert result == {"FINISHED"}
assert bpy.data.objects.get("WFT_Terrain_MainTerrain") is not None
assert bpy.data.objects.get("WFT_Terrain_SuggestedEmitter_00") is not None
print("WFT terrain generate smoke test completed")

