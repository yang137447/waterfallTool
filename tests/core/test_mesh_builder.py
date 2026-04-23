import pytest

from waterfall_tool.core.mesh_builder import build_x_card_mesh
from waterfall_tool.core.types import MeshSettings, TrajectoryPoint
from waterfall_tool.core.vector_math import length


def point(position, speed=1.0):
    return TrajectoryPoint(position=position, velocity=(0.0, 0.0, -speed), speed=speed)


def attached_point(position, surface_normal, speed=1.0):
    return TrajectoryPoint(
        position=position,
        velocity=(0.0, 0.0, -speed),
        speed=speed,
        attached=True,
        surface_normal=surface_normal,
    )


def test_mesh_has_two_card_strips_with_quad_faces():
    settings = MeshSettings(start_width=2.0, end_width=2.0, cross_angle_degrees=90.0, longitudinal_step_length=1.0)
    mesh = build_x_card_mesh(
        [point((0.0, 0.0, 0.0), 1.0), point((0.0, 0.0, -1.0), 2.0), point((0.0, 0.0, -2.0), 3.0)],
        settings,
    )
    assert len(mesh.vertices) == 12
    assert len(mesh.faces) == 4
    assert len(mesh.uv0) == 4


def test_cross_width_scale_affects_only_second_strip():
    settings = MeshSettings(base_width=2.0, start_width=1.0, end_width=1.0, cross_width_scale=0.5, cross_angle_degrees=90.0, longitudinal_step_length=1.0)
    mesh = build_x_card_mesh(
        [point((0.0, 0.0, 0.0)), point((0.0, 0.0, -1.0))],
        settings,
    )

    # First strip is the primary waterfall strip.
    main_strip_left = mesh.vertices[0]
    main_strip_right = mesh.vertices[1]
    main_width = length((main_strip_right[0] - main_strip_left[0], main_strip_right[1] - main_strip_left[1], main_strip_right[2] - main_strip_left[2]))

    # Second strip is the optional cross strip.
    cross_strip_left = mesh.vertices[4]
    cross_strip_right = mesh.vertices[5]
    cross_width = length((cross_strip_right[0] - cross_strip_left[0], cross_strip_right[1] - cross_strip_left[1], cross_strip_right[2] - cross_strip_left[2]))

    assert main_width == pytest.approx(2.0)
    assert cross_width == pytest.approx(1.0)


def test_disabling_cross_strip_keeps_primary_surface_normal_strip():
    settings = MeshSettings(
        start_width=2.0,
        end_width=2.0,
        enable_cross_strip=False,
        cross_angle_degrees=90.0,
        longitudinal_step_length=1.0,
    )
    mesh = build_x_card_mesh(
        [
            attached_point((0.0, 0.0, 0.0), surface_normal=(1.0, 0.0, 0.0)),
            attached_point((0.0, 0.0, -1.0), surface_normal=(1.0, 0.0, 0.0)),
        ],
        settings,
    )

    strip_axis = (
        mesh.vertices[1][0] - mesh.vertices[0][0],
        mesh.vertices[1][1] - mesh.vertices[0][1],
        mesh.vertices[1][2] - mesh.vertices[0][2],
    )
    assert abs(strip_axis[0]) == pytest.approx(2.0)
    assert strip_axis[1] == pytest.approx(0.0)
    assert strip_axis[2] == pytest.approx(0.0)


def test_width_density_adds_horizontal_subdivisions():
    settings = MeshSettings(width_density=3, start_width=2.0, end_width=2.0, cross_angle_degrees=90.0, longitudinal_step_length=1.0)
    mesh = build_x_card_mesh(
        [point((0.0, 0.0, 0.0), 1.0), point((0.0, 0.0, -1.0), 2.0), point((0.0, 0.0, -2.0), 3.0)],
        settings,
    )

    assert len(mesh.vertices) == 24
    assert len(mesh.faces) == 12
    assert len(mesh.uv0) == 12


def test_width_changes_along_curve():
    settings = MeshSettings(start_width=2.0, end_width=1.0, width_falloff=1.0, cross_angle_degrees=90.0, longitudinal_step_length=2.0)
    mesh = build_x_card_mesh([point((0.0, 0.0, 0.0)), point((0.0, 0.0, -2.0))], settings)
    start_left = mesh.vertices[0]
    start_right = mesh.vertices[1]
    end_left = mesh.vertices[2]
    end_right = mesh.vertices[3]
    start_width = abs(start_right[0] - start_left[0]) + abs(start_right[1] - start_left[1])
    end_width = abs(end_right[0] - end_left[0]) + abs(end_right[1] - end_left[1])
    assert end_width < start_width


def test_detours_do_not_change_base_width():
    settings = MeshSettings(
        base_width=1.0,
        start_width=1.0,
        end_width=1.0,
        cross_angle_degrees=90.0,
        longitudinal_step_length=10.0,
    )
    straight = build_x_card_mesh([point((0.0, 0.0, 0.0)), point((0.0, 0.0, -2.0))], settings)
    detoured = build_x_card_mesh(
        [
            point((0.0, 0.0, 0.0)),
            point((1.5, 0.0, -1.0)),
            point((0.0, 0.0, -2.0)),
        ],
        settings,
    )

    straight_width = length(
        (
            straight.vertices[1][0] - straight.vertices[0][0],
            straight.vertices[1][1] - straight.vertices[0][1],
            straight.vertices[1][2] - straight.vertices[0][2],
        )
    )
    detoured_width = length(
        (
            detoured.vertices[1][0] - detoured.vertices[0][0],
            detoured.vertices[1][1] - detoured.vertices[0][1],
            detoured.vertices[1][2] - detoured.vertices[0][2],
        )
    )

    assert detoured_width == pytest.approx(straight_width)


def test_speed_stretches_single_uv_against_base_speed():
    settings = MeshSettings(start_width=1.0, end_width=1.0, uv_base_speed=2.0, longitudinal_step_length=1.0)
    mesh = build_x_card_mesh([point((0.0, 0.0, 0.0), 1.0), point((0.0, 0.0, -1.0), 3.0)], settings)
    uv_values = [uv for face in mesh.uv0 for uv in face]
    assert min(value[1] for value in uv_values) == 0.0
    assert max(value[1] for value in uv_values) == 1.0


def test_uv_stretch_uses_collapsed_sample_speed_range_stably():
    settings = MeshSettings(start_width=1.0, end_width=1.0, uv_base_speed=2.0, longitudinal_step_length=1.0)
    mesh = build_x_card_mesh(
        [point((0.0, 0.0, 0.0), 100.0), point((0.0, 0.0, 0.0), 1.0), point((0.0, 0.0, -1.0), 3.0)],
        settings,
    )
    uv_values = [uv for face in mesh.uv0 for uv in face]
    assert min(value[1] for value in uv_values) == 0.0
    assert max(value[1] for value in uv_values) == 1.0


def test_faster_segment_produces_smaller_uv_v_span_than_base_speed():
    settings = MeshSettings(start_width=1.0, end_width=1.0, uv_base_speed=2.0, longitudinal_step_length=1.0)
    slow_mesh = build_x_card_mesh([point((0.0, 0.0, 0.0), 1.0), point((0.0, 0.0, -1.0), 1.0)], settings)
    fast_mesh = build_x_card_mesh([point((0.0, 0.0, 0.0), 4.0), point((0.0, 0.0, -1.0), 4.0)], settings)

    slow_span = slow_mesh.uv0[0][2][1] - slow_mesh.uv0[0][0][1]
    fast_span = fast_mesh.uv0[0][2][1] - fast_mesh.uv0[0][0][1]

    assert slow_span > fast_span


def test_uv_speed_smoothing_length_makes_v_span_change_gradual():
    base = MeshSettings(
        start_width=1.0,
        end_width=1.0,
        uv_base_speed=2.0,
        width_density=1,
        longitudinal_step_length=1.0,
    )
    no_smoothing = build_x_card_mesh(
        [
            point((0.0, 0.0, 0.0), 0.1),
            point((0.0, 0.0, -1.0), 0.1),
            point((0.0, 0.0, -2.0), 10.0),
            point((0.0, 0.0, -3.0), 10.0),
        ],
        base,
    )
    smoothing = build_x_card_mesh(
        [
            point((0.0, 0.0, 0.0), 0.1),
            point((0.0, 0.0, -1.0), 0.1),
            point((0.0, 0.0, -2.0), 10.0),
            point((0.0, 0.0, -3.0), 10.0),
        ],
        MeshSettings(**{**base.__dict__, "uv_speed_smoothing_length": 0.5}),
    )

    no_smooth_first = no_smoothing.uv0[0][2][1] - no_smoothing.uv0[0][0][1]
    no_smooth_second = no_smoothing.uv0[1][2][1] - no_smoothing.uv0[1][0][1]
    smooth_first = smoothing.uv0[0][2][1] - smoothing.uv0[0][0][1]
    smooth_second = smoothing.uv0[1][2][1] - smoothing.uv0[1][0][1]

    assert no_smooth_first > no_smooth_second
    assert smooth_first > smooth_second
    assert smooth_second > no_smooth_second


def test_uv_is_consistent_across_longitudinal_step_length_when_no_smoothing():
    points = [
        point((0.0, 0.0, 0.0), 1.0),
        point((0.0, 0.0, -0.5), 1.0),
        point((0.0, 0.0, -1.0), 1.0),
        point((0.0, 0.0, -1.5), 1.0),
        point((0.0, 0.0, -2.0), 1.0),
    ]
    coarse = build_x_card_mesh(
        points,
        MeshSettings(
            start_width=1.0,
            end_width=1.0,
            uv_base_speed=2.0,
            longitudinal_step_length=1.0,
            curvature_min_angle_degrees=60.0,
            uv_speed_smoothing_length=0.0,
        ),
    )
    dense = build_x_card_mesh(
        points,
        MeshSettings(
            start_width=1.0,
            end_width=1.0,
            uv_base_speed=2.0,
            longitudinal_step_length=0.25,
            curvature_min_angle_degrees=60.0,
            uv_speed_smoothing_length=0.0,
        ),
    )

    assert coarse.uv0[-1][2][1] == pytest.approx(dense.uv0[-1][2][1])


def test_align_end_to_cutoff_plane_flattens_last_row_to_cutoff_height():
    settings = MeshSettings(
        start_width=1.0,
        end_width=1.0,
        longitudinal_step_length=1.0,
        cutoff_height=0.0,
        align_end_to_cutoff_plane=True,
    )
    mesh = build_x_card_mesh([point((0.0, 0.0, 1.0), 1.0), point((1.0, 0.0, -1.0), 1.0)], settings)

    used = {index for face in mesh.faces for index in face}
    assert used
    used_z = [mesh.vertices[index][2] for index in used]
    assert min(used_z) == pytest.approx(0.0)
    assert all(z >= -1.0e-8 for z in used_z)


def test_cutoff_plane_clips_faces_below_height_even_when_centerline_stays_above():
    settings = MeshSettings(
        base_width=1.0,
        start_width=1.0,
        end_width=1.0,
        width_density=1,
        longitudinal_step_length=1.0,
        cutoff_height=0.0,
        align_end_to_cutoff_plane=True,
    )
    mesh = build_x_card_mesh([point((0.0, 0.0, 0.2), 1.0), point((1.0, 0.0, 0.2), 1.0)], settings)

    used = {index for face in mesh.faces for index in face}
    assert used
    assert all(mesh.vertices[index][2] >= -1.0e-8 for index in used)
    assert all(len(face) in (3, 4) for face in mesh.faces)
    assert len(mesh.faces) == len(mesh.uv0)
    assert all(len(face) == len(face_uvs) for face, face_uvs in zip(mesh.faces, mesh.uv0, strict=True))
    assert len(mesh.vertices) > 8


def test_cutoff_plane_extension_forces_intersection_when_trajectory_never_reaches_plane():
    settings = MeshSettings(
        base_width=1.0,
        start_width=1.0,
        end_width=1.0,
        width_density=1,
        longitudinal_step_length=1.0,
        cutoff_height=0.0,
        align_end_to_cutoff_plane=True,
    )
    mesh = build_x_card_mesh([point((0.0, 0.0, 1.0), 1.0), point((1.0, 0.0, 1.0), 1.0)], settings)
    used = {index for face in mesh.faces for index in face}
    used_z = [mesh.vertices[index][2] for index in used]
    assert min(used_z) == pytest.approx(0.0)


def test_cutoff_plane_clipping_removes_unreferenced_vertices_below_plane():
    settings = MeshSettings(
        base_width=1.0,
        start_width=1.0,
        end_width=1.0,
        width_density=1,
        longitudinal_step_length=1.0,
        cutoff_height=0.0,
        align_end_to_cutoff_plane=True,
    )
    mesh = build_x_card_mesh([point((0.0, 0.0, 1.0), 1.0), point((1.0, 0.0, 1.0), 1.0)], settings)
    used = {index for face in mesh.faces for index in face}

    assert used == set(range(len(mesh.vertices)))
    assert all(vertex[2] >= -1.0e-8 for vertex in mesh.vertices)


def test_smaller_longitudinal_step_length_increases_face_count():
    points = [
        point((0.0, 0.0, 0.0), 1.0),
        point((0.5, 1.0, -0.4), 1.2),
        point((1.0, -1.0, -0.8), 1.4),
        point((1.5, 1.2, -1.2), 1.6),
        point((2.0, 0.0, -1.6), 1.8),
    ]
    coarse = build_x_card_mesh(
        points,
        MeshSettings(
            longitudinal_step_length=1.0,
            curvature_min_angle_degrees=20.0,
        ),
    )
    dense = build_x_card_mesh(
        points,
        MeshSettings(
            longitudinal_step_length=0.25,
            curvature_min_angle_degrees=20.0,
        ),
    )

    assert len(dense.faces) > len(coarse.faces)


def test_smaller_curvature_min_angle_increases_face_count_on_bends():
    points = [
        point((0.0, 0.0, 0.0), 1.0),
        point((0.5, 1.0, -0.4), 1.2),
        point((1.0, -1.0, -0.8), 1.4),
        point((1.5, 1.2, -1.2), 1.6),
        point((2.0, 0.0, -1.6), 1.8),
    ]
    coarse = build_x_card_mesh(
        points,
        MeshSettings(
            longitudinal_step_length=0.75,
            curvature_min_angle_degrees=60.0,
        ),
    )
    refined = build_x_card_mesh(
        points,
        MeshSettings(
            longitudinal_step_length=0.75,
            curvature_min_angle_degrees=10.0,
        ),
    )

    assert len(refined.faces) > len(coarse.faces)
