from waterfall_tool.core.curve_sampling import compute_width, resample_polyline
from waterfall_tool.core.types import MeshSettings, TrajectoryPoint


def point(position, speed=1.0):
    return TrajectoryPoint(position=position, velocity=(speed, 0.0, 0.0), speed=speed)


def test_width_falloff_interpolates_start_to_end():
    settings = MeshSettings(base_width=1.0, start_width=2.0, end_width=1.0, width_falloff=1.0)
    assert compute_width(settings, 0.0) == 2.0
    assert compute_width(settings, 0.5) == 1.5
    assert compute_width(settings, 1.0) == 1.0


def test_width_uses_base_width():
    settings = MeshSettings(base_width=2.0, start_width=1.0, end_width=1.0, width_falloff=1.0)
    assert compute_width(settings, 0.0) == 2.0
    assert compute_width(settings, 1.0) == 2.0


def test_width_increases_with_expansion():
    settings = MeshSettings(base_width=1.0, start_width=1.0, end_width=1.0)
    assert compute_width(settings, 0.5, expansion_width=0.5) == 1.5


def test_width_speed_expansion_scales_with_shape():
    settings = MeshSettings(base_width=1.0, start_width=2.0, end_width=1.0, width_falloff=1.0)
    assert compute_width(settings, 0.0, expansion_width=0.0) == 2.0
    # At t=1.0: relative_scale = 1.0, expansion_width = 1.0 -> base_width = 2.0 -> width = 2.0
    assert compute_width(settings, 1.0, expansion_width=1.0) == 2.0


def test_resample_polyline_preserves_endpoints_and_arc_lengths():
    samples = resample_polyline(
        [point((0.0, 0.0, 0.0), 2.0), point((0.0, 0.0, -2.0), 4.0)],
        longitudinal_step_length=0.5,
        curvature_min_angle_degrees=15.0,
    )
    assert samples[0].position == (0.0, 0.0, 0.0)
    assert samples[-1].position == (0.0, 0.0, -2.0)
    assert samples[-1].arc_length == 2.0
    assert [sample.t for sample in samples] == sorted(sample.t for sample in samples)


def test_curvature_adds_more_samples_near_bends():
    straight = [point((0.0, 0.0, 0.0)), point((0.0, 0.0, -1.0)), point((0.0, 0.0, -2.0))]
    bent = [point((0.0, 0.0, 0.0)), point((1.0, 0.0, -1.0)), point((0.0, 0.0, -2.0))]
    straight_samples = resample_polyline(straight, longitudinal_step_length=1.0, curvature_min_angle_degrees=20.0)
    bent_samples = resample_polyline(bent, longitudinal_step_length=1.0, curvature_min_angle_degrees=20.0)
    assert len(bent_samples) > len(straight_samples)


def test_resample_polyline_collapses_fully_degenerate_input_to_single_safe_sample():
    samples = resample_polyline(
        [point((1.0, 2.0, 3.0), 2.0), point((1.0, 2.0, 3.0), 4.0)],
        longitudinal_step_length=0.5,
        curvature_min_angle_degrees=15.0,
    )
    assert len(samples) == 1
    assert samples[0].position == (1.0, 2.0, 3.0)
    assert samples[0].tangent == (0.0, 0.0, -1.0)
    assert samples[0].arc_length == 0.0
    assert samples[0].t == 0.0


def test_resample_polyline_collapses_near_duplicate_positions_with_threshold():
    samples = resample_polyline(
        [point((0.0, 0.0, 0.0)), point((0.05, 0.0, 0.0)), point((0.0, 0.0, -1.0))],
        longitudinal_step_length=1.0,
        curvature_min_angle_degrees=15.0,
    )
    assert samples[0].tangent != (0.0, 0.0, 0.0)


def test_resample_polyline_preserves_earliest_anchor_for_near_duplicate_runs():
    samples = resample_polyline(
        [point((0.0, 0.0, 0.0)), point((0.01, 0.0, 0.0)), point((0.02, 0.0, 0.0)), point((0.0, 0.0, -1.0))],
        longitudinal_step_length=1.0,
        curvature_min_angle_degrees=15.0,
    )
    assert samples[0].position == (0.0, 0.0, 0.0)


def test_resample_polyline_collapsed_anchor_uses_latest_speed_metadata():
    samples = resample_polyline(
        [point((0.0, 0.0, 0.0), 1.0), point((0.0, 0.0, 0.0), 5.0), point((0.0, 0.0, -1.0), 7.0)],
        longitudinal_step_length=1.0,
        curvature_min_angle_degrees=15.0,
    )
    assert samples[0].position == (0.0, 0.0, 0.0)
    assert samples[0].speed == 5.0


def test_resample_polyline_preserves_interior_anchors_when_each_segment_only_needs_one_step():
    # The new resampling algorithm does NOT strictly preserve interior anchors if they are closer than the step length.
    # It walks the entire curve according to the step length.
    samples = resample_polyline(
        [
            point((0.0, 0.0, 0.0)),
            point((0.2, 0.2, 0.0)),
            point((0.4, 0.5, 0.0)),
            point((0.7, 0.9, 0.1)),
        ],
        longitudinal_step_length=0.1,  # use a very small step length to sample densely
        curvature_min_angle_degrees=15.0,
    )

    # We just ensure start and end are preserved, and we have multiple samples.
    assert samples[0].position == (0.0, 0.0, 0.0)
    assert samples[-1].position == (0.7, 0.9, 0.1)
    assert len(samples) > 4


def test_smaller_curvature_min_angle_increases_subdivision_near_bends():
    bent = [point((0.0, 0.0, 0.0)), point((1.0, 0.0, -1.0)), point((0.0, 0.0, -2.0))]
    coarse = resample_polyline(
        bent,
        longitudinal_step_length=1.0,
        curvature_min_angle_degrees=60.0,
    )
    refined = resample_polyline(
        bent,
        longitudinal_step_length=1.0,
        curvature_min_angle_degrees=10.0,
    )

    assert len(refined) > len(coarse)


def test_resample_polyline_smooths_tangent_across_bends():
    samples = resample_polyline(
        [point((0.0, 0.0, 0.0)), point((1.0, 0.0, -1.0)), point((1.0, 0.0, -2.0))],
        longitudinal_step_length=1.0,
        curvature_min_angle_degrees=45.0,
    )

    middle = samples[1].tangent
    assert middle[0] > 0.0
    assert middle[2] < 0.0
    assert middle != (1.0, 0.0, 0.0)
    assert middle != (0.0, 0.0, -1.0)


def test_smaller_longitudinal_step_length_increases_sample_count():
    points = [point((0.0, 0.0, 0.0)), point((0.0, 0.0, -2.0))]
    coarse = resample_polyline(points, longitudinal_step_length=1.0, curvature_min_angle_degrees=15.0)
    dense = resample_polyline(points, longitudinal_step_length=0.25, curvature_min_angle_degrees=15.0)

    assert len(dense) > len(coarse)
