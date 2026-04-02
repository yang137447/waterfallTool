from pathlib import Path
import sys

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "addon"))

import waterfall_tool

waterfall_tool.register()

curve_data = bpy.data.curves.new("Emitter", type="CURVE")
curve_data.dimensions = "3D"
spline = curve_data.splines.new("POLY")
spline.points.add(1)
spline.points[0].co = (0.0, 0.0, 2.0, 1.0)
spline.points[1].co = (2.0, 0.0, 2.0, 1.0)
emitter = bpy.data.objects.new("Emitter", curve_data)
bpy.context.scene.collection.objects.link(emitter)

mesh = bpy.data.meshes.new("Cliff")
mesh.from_pydata([(0, 1, 2), (0, -1, 2), (0, -1, -3), (0, 1, -3)], [], [(0, 1, 2, 3)])
cliff = bpy.data.objects.new("Cliff", mesh)
bpy.context.scene.collection.objects.link(cliff)

settings = bpy.context.scene.wft_settings
settings.emitter_object = emitter
settings.collider_object = cliff

result = bpy.ops.wft.generate_preview()
assert result == {"FINISHED"}
assert bpy.data.objects.get("WFT_PreviewPaths") is not None
print("WFT preview smoke test completed")
