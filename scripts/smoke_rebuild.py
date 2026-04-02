from pathlib import Path
import json
import sys
import tempfile

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "addon"))

import waterfall_tool

waterfall_tool.register()

cache_dir = tempfile.mkdtemp(prefix="wft_rebuild_")
cache_path = f"{cache_dir}/preview.json"
with open(cache_path, "w", encoding="utf-8") as handle:
    json.dump(
        [[
            {"position": [0.0, 0.0, 2.0], "speed": 1.0, "breakup": 0.0, "split_score": 0.0},
            {"position": [0.0, 0.0, 1.0], "speed": 1.2, "breakup": 0.2, "split_score": 0.1},
        ]],
        handle,
    )

settings = bpy.context.scene.wft_settings
settings.cache_path = cache_path
settings.sheet_width = 0.5

result = bpy.ops.wft.rebuild_waterfall()
assert result == {"FINISHED"}
assert bpy.data.objects.get("WFT_MainSheet") is not None
print("WFT rebuild smoke test completed")
