from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "addon"))

import bpy  # noqa: E402
import waterfall_tool  # noqa: E402

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

assert bpy.ops.wft.generate_terrace_terrain() == {"FINISHED"}
assert bpy.ops.wft.use_generated_terrain_for_waterfall() == {"FINISHED"}
assert bpy.ops.wft.generate_preview() == {"FINISHED"}
assert bpy.data.objects.get("WFT_PreviewPaths") is not None
print("WFT terrain handoff smoke test completed")

