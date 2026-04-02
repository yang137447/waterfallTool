from __future__ import annotations

from dataclasses import dataclass

from .types import PathPoint


@dataclass(frozen=True)
class RibbonMesh:
    vertices: list[tuple[float, float, float]]
    faces: list[tuple[int, int, int, int]]
    breakup_mask: list[float]
    flow_speed: list[float]


def build_ribbon_mesh(paths: list[list[PathPoint]], base_width: float) -> RibbonMesh:
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    breakup_mask: list[float] = []
    flow_speed: list[float] = []

    for path in paths:
        start_index = len(vertices)
        for point in path:
            left = (point.position[0] - base_width * 0.5, point.position[1], point.position[2])
            right = (point.position[0] + base_width * 0.5, point.position[1], point.position[2])
            vertices.extend([left, right])
            breakup_mask.extend([point.breakup, point.breakup])
            flow_speed.extend([point.speed, point.speed])

        for row in range(len(path) - 1):
            offset = start_index + row * 2
            faces.append((offset, offset + 1, offset + 3, offset + 2))

    return RibbonMesh(
        vertices=vertices,
        faces=faces,
        breakup_mask=breakup_mask,
        flow_speed=flow_speed,
    )
