from pathlib import Path

from waterfall_tool.core.export_plan import build_export_plan, resolve_export_object_names


def test_build_export_plan_creates_mesh_and_mask_targets():
    plan = build_export_plan(Path("exports"), "waterfall_a")

    assert plan.mesh_path == Path("exports/waterfall_a.glb")
    assert plan.mask_path == Path("exports/waterfall_a_masks.json")


def test_resolve_export_object_names_excludes_preview_helpers():
    names = [
        "WFT_MainSheet",
        "WFT_SplitStrands",
        "WFT_ImpactRegion",
        "WFT_PreviewPaths",
        "Cliff",
    ]

    assert resolve_export_object_names(names) == [
        "WFT_MainSheet",
        "WFT_SplitStrands",
        "WFT_ImpactRegion",
    ]
