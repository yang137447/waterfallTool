from pathlib import Path

from waterfall_tool.core.export_plan import build_export_plan


def test_build_export_plan_creates_mesh_and_mask_targets():
    plan = build_export_plan(Path("exports"), "waterfall_a")

    assert plan.mesh_path == Path("exports/waterfall_a.glb")
    assert plan.mask_path == Path("exports/waterfall_a_masks.json")
