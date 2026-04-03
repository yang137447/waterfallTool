from waterfall_tool.core.emitter_sampling import sample_polyline_evenly


def test_sample_polyline_evenly_distributes_points_by_distance():
    points = ((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (2.0, 2.0, 0.0))

    sampled = sample_polyline_evenly(points, 5)

    assert sampled == [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (2.0, 0.0, 0.0),
        (2.0, 1.0, 0.0),
        (2.0, 2.0, 0.0),
    ]


def test_sample_polyline_evenly_handles_short_or_empty_input():
    assert sample_polyline_evenly((), 8) == []
    assert sample_polyline_evenly(((1.0, 2.0, 3.0),), 3) == [(1.0, 2.0, 3.0)] * 3
