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


def test_resample_polyline_collapses_near_duplicate_positions_with_epsilon_threshold():
    samples = resample_polyline(
        [point((0.0, 0.0, 0.0)), point((1.0e-12, 0.0, 0.0)), point((0.0, 0.0, -1.0))],
        base_segment_density=1.0,
        curvature_refine_strength=0.0,
    )
    assert samples[0].tangent != (0.0, 0.0, 0.0)


def test_resample_polyline_preserves_earliest_anchor_for_near_duplicate_runs():
    samples = resample_polyline(
        [point((0.0, 0.0, 0.0)), point((9.0e-9, 0.0, 0.0)), point((1.8e-8, 0.0, 0.0)), point((0.0, 0.0, -1.0))],
        base_segment_density=1.0,
        curvature_refine_strength=0.0,
    )
    assert samples[0].position == (0.0, 0.0, 0.0)


def test_resample_polyline_collapsed_anchor_uses_latest_speed_metadata():
    samples = resample_polyline(
        [point((0.0, 0.0, 0.0), 1.0), point((1.0e-12, 0.0, 0.0), 5.0), point((0.0, 0.0, -1.0), 7.0)],
        base_segment_density=1.0,
        curvature_refine_strength=0.0,
    )
    assert samples[0].position == (0.0, 0.0, 0.0)
    assert samples[0].speed == 5.0


def test_resample_polyline_preserves_interior_anchors_when_each_segment_only_needs_one_step():
    samples = resample_polyline(
        [
            point((0.0, 0.0, 0.0)),
            point((0.2, 0.2, 0.0)),
            point((0.4, 0.5, 0.0)),
            point((0.7, 0.9, 0.1)),
        ],
        base_segment_density=1.0,
        curvature_refine_strength=0.0,
    )

    assert [sample.position for sample in samples] == [
        (0.0, 0.0, 0.0),
        (0.2, 0.2, 0.0),
        (0.4, 0.5, 0.0),
        (0.7, 0.9, 0.1),
    ]


def test_curvature_density_max_multiplier_limits_extra_subdivision():
    bent = [point((0.0, 0.0, 0.0)), point((1.0, 0.0, -1.0)), point((0.0, 0.0, -2.0))]
    uncapped = resample_polyline(
        bent,
        base_segment_density=1.0,
        curvature_refine_strength=6.0,
        curvature_density_max_multiplier=10.0,
    )
    capped = resample_polyline(
        bent,
        base_segment_density=1.0,
        curvature_refine_strength=6.0,
        curvature_density_max_multiplier=1.2,
    )

    assert len(capped) < len(uncapped)


def test_curvature_density_max_multiplier_equal_one_disables_curvature_boost():
    bent = [point((0.0, 0.0, 0.0)), point((1.0, 0.0, -1.0)), point((0.0, 0.0, -2.0))]
    base_only = resample_polyline(
        bent,
        base_segment_density=1.0,
        curvature_refine_strength=0.0,
        curvature_density_max_multiplier=10.0,
    )
    clamped = resample_polyline(
        bent,
        base_segment_density=1.0,
        curvature_refine_strength=6.0,
        curvature_density_max_multiplier=1.0,
    )

    assert len(clamped) == len(base_only)
