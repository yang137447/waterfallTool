from waterfall_tool.core.curve_sampling import compute_width, resample_polyline
from waterfall_tool.core.types import MeshSettings, TrajectoryPoint


def point(position, speed=1.0):
    return TrajectoryPoint(position=position, velocity=(speed, 0.0, 0.0), speed=speed)


def test_width_falloff_interpolates_start_to_end():
    settings = MeshSettings(start_width=2.0, end_width=1.0, width_falloff=1.0)
    assert compute_width(settings, 0.0) == 2.0
    assert compute_width(settings, 1.0) == 1.0
    assert compute_width(settings, 0.5) == 1.5


def test_resample_polyline_preserves_endpoints_and_arc_lengths():
    samples = resample_polyline(
        [point((0.0, 0.0, 0.0), 2.0), point((0.0, 0.0, -2.0), 4.0)],
        base_segment_density=2.0,
        curvature_refine_strength=0.0,
    )
    assert samples[0].position == (0.0, 0.0, 0.0)
    assert samples[-1].position == (0.0, 0.0, -2.0)
    assert samples[-1].arc_length == 2.0
    assert [sample.t for sample in samples] == sorted(sample.t for sample in samples)


def test_curvature_adds_more_samples_near_bends():
    straight = [point((0.0, 0.0, 0.0)), point((0.0, 0.0, -1.0)), point((0.0, 0.0, -2.0))]
    bent = [point((0.0, 0.0, 0.0)), point((1.0, 0.0, -1.0)), point((0.0, 0.0, -2.0))]
    straight_samples = resample_polyline(straight, base_segment_density=1.0, curvature_refine_strength=2.0)
    bent_samples = resample_polyline(bent, base_segment_density=1.0, curvature_refine_strength=2.0)
    assert len(bent_samples) > len(straight_samples)


def test_resample_polyline_collapses_fully_degenerate_input_to_single_safe_sample():
    samples = resample_polyline(
        [point((1.0, 2.0, 3.0), 2.0), point((1.0, 2.0, 3.0), 4.0)],
        base_segment_density=2.0,
        curvature_refine_strength=1.0,
    )
    assert len(samples) == 1
    assert samples[0].position == (1.0, 2.0, 3.0)
    assert samples[0].tangent == (0.0, 0.0, -1.0)
    assert samples[0].arc_length == 0.0
    assert samples[0].t == 0.0
