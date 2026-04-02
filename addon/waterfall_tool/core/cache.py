from __future__ import annotations

import json
from pathlib import Path

from .types import PathPoint


def save_cache(path: Path, paths: list[list[PathPoint]]) -> None:
    payload = [[point.__dict__ for point in path_points] for path_points in paths]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_cache(path: Path) -> list[list[PathPoint]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [
        [
            PathPoint(
                position=tuple(point["position"]),
                speed=point["speed"],
                breakup=point["breakup"],
                split_score=point["split_score"],
            )
            for point in path_points
        ]
        for path_points in payload
    ]
