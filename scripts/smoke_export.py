from pathlib import Path
import sys
import tempfile

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "addon"))

import waterfall_tool

waterfall_tool.register()

mesh = bpy.data.meshes.new("ExportMesh")
mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 0, -1), (1, 0, -1)], [], [(0, 1, 3, 2)])
obj = bpy.data.objects.new("ExportMesh", mesh)
bpy.context.scene.collection.objects.link(obj)

settings = bpy.context.scene.wft_settings
settings.export_directory = tempfile.mkdtemp(prefix="wft_export_")
settings.export_stem = "waterfall_test"

result = bpy.ops.wft.export_waterfall()
assert result == {"FINISHED"}
assert Path(settings.export_directory, "waterfall_test.glb").exists()
assert Path(settings.export_directory, "waterfall_test_masks.json").exists()
print("WFT export smoke test completed")
