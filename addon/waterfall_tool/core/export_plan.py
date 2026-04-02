from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExportPlan:
    mesh_path: Path
    mask_path: Path


EXPORT_OBJECT_NAMES = (
    "WFT_MainSheet",
    "WFT_SplitStrands",
    "WFT_ImpactRegion",
)


def build_export_plan(directory: Path, stem: str) -> ExportPlan:
    return ExportPlan(
        mesh_path=directory / f"{stem}.glb",
        mask_path=directory / f"{stem}_masks.json",
    )


def resolve_export_object_names(object_names: list[str]) -> list[str]:
    return [name for name in object_names if name in EXPORT_OBJECT_NAMES]
