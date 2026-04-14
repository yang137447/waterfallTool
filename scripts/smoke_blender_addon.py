from __future__ import annotations

import importlib
import sys
from pathlib import Path

import bpy

REPO_ROOT = Path(__file__).resolve().parents[1]
ADDON_ROOT = REPO_ROOT / "addon"
if str(ADDON_ROOT) not in sys.path:
    sys.path.insert(0, str(ADDON_ROOT))

import waterfall_tool

importlib.reload(waterfall_tool)
waterfall_tool.register()

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

emitter = bpy.data.objects.new("SmokeEmitter", None)
bpy.context.collection.objects.link(emitter)
bpy.context.view_layer.objects.active = emitter
emitter.select_set(True)
emitter.waterfall_emitter.speed = 6.0
emitter.waterfall_emitter.simulation_step_count = 12
bpy.ops.waterfall.simulate_curve()

curve = bpy.data.objects.get(emitter.waterfall_emitter.flow_curve_name)
assert curve is not None
assert curve.type == "CURVE"

bpy.context.view_layer.objects.active = curve
curve.select_set(True)
curve.waterfall_curve.start_width = 1.0
curve.waterfall_curve.end_width = 0.5
curve.waterfall_curve.curve_mode = "PHYSICS_ASSISTED"
bpy.ops.waterfall.rebuild_preview()

preview = bpy.data.objects.get(curve.waterfall_curve.preview_mesh_name)
assert preview is not None
assert preview.type == "MESH"
assert "UV0" in preview.data.uv_layers
assert "UV1_Speed" in preview.data.uv_layers

bpy.ops.waterfall.bake_mesh()
baked = bpy.data.objects.get(curve.waterfall_curve.baked_mesh_name)
assert baked is not None
assert baked.type == "MESH"
assert curve.waterfall_curve.preview_enabled is False

waterfall_tool.unregister()
print("waterfall smoke passed")
