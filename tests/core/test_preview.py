from waterfall_tool.core.preview import build_preview_paths
from waterfall_tool.core.types import CollisionSample, FlowSettings


class StubCollider:
    def sample(self, _position, _velocity):
        return CollisionSample(
            hit=True,
            normal=(0.0, 1.0, 0.0),
            tangent=(0.6, 0.0, -0.3),
            support=0.8,
            obstacle=0.2,
        )


def test_build_preview_paths_returns_one_path_per_emitter_point():
    settings = FlowSettings(
        time_step=0.1,
        gravity=9.8,
        attachment=0.7,
        split_sensitivity=0.3,
        breakup_rate=0.2,
    )
    emitter_points = [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0)]

    paths = build_preview_paths(emitter_points, StubCollider(), settings, steps=4)

    assert len(paths) == 2
    assert all(len(path) == 5 for path in paths)
    assert paths[0][-1].position[2] < 0.0
