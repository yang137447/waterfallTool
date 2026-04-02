from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExportPlan:
    mesh_path: Path
    mask_path: Path


def build_export_plan(directory: Path, stem: str) -> ExportPlan:
    return ExportPlan(
        mesh_path=directory / f"{stem}.glb",
        mask_path=directory / f"{stem}_masks.json",
    )
