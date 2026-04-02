from waterfall_tool.core.rebuild import build_ribbon_mesh
from waterfall_tool.core.types import PathPoint


def test_build_ribbon_mesh_creates_quad_strip_and_attributes():
    paths = [[
        PathPoint(position=(0.0, 0.0, 2.0), speed=1.0, breakup=0.0, split_score=0.0),
        PathPoint(position=(0.0, 0.0, 1.0), speed=1.4, breakup=0.2, split_score=0.1),
        PathPoint(position=(0.0, 0.0, 0.0), speed=1.8, breakup=0.4, split_score=0.2),
    ]]

    mesh = build_ribbon_mesh(paths, base_width=0.5)

    assert len(mesh.vertices) == 6
    assert len(mesh.faces) == 2
    assert mesh.breakup_mask[-1] == 0.4
