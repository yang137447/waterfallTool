from waterfall_tool.core.mesh_builder import build_x_card_mesh
from waterfall_tool.core.types import MeshSettings, TrajectoryPoint


def point(position, speed=1.0):
    return TrajectoryPoint(position=position, velocity=(0.0, 0.0, -speed), speed=speed)


def test_mesh_has_two_card_strips_with_quad_faces():
    settings = MeshSettings(start_width=2.0, end_width=2.0, cross_angle_degrees=90.0)
    mesh = build_x_card_mesh(
        [point((0.0, 0.0, 0.0), 1.0), point((0.0, 0.0, -1.0), 2.0), point((0.0, 0.0, -2.0), 3.0)],
        settings,
    )
    assert len(mesh.vertices) == 12
    assert len(mesh.faces) == 4
    assert len(mesh.uv0) == 4
    assert len(mesh.uv1) == 4


def test_width_changes_along_curve():
    settings = MeshSettings(start_width=2.0, end_width=1.0, width_falloff=1.0, cross_angle_degrees=90.0)
    mesh = build_x_card_mesh([point((0.0, 0.0, 0.0)), point((0.0, 0.0, -2.0))], settings)
    start_left = mesh.vertices[0]
    start_right = mesh.vertices[1]
    end_left = mesh.vertices[2]
    end_right = mesh.vertices[3]
    start_width = abs(start_right[0] - start_left[0]) + abs(start_right[1] - start_left[1])
    end_width = abs(end_right[0] - end_left[0]) + abs(end_right[1] - end_left[1])
    assert end_width < start_width


def test_speed_is_packed_into_uv1():
    settings = MeshSettings(start_width=1.0, end_width=1.0, uv_speed_scale=1.0)
    mesh = build_x_card_mesh([point((0.0, 0.0, 0.0), 1.0), point((0.0, 0.0, -1.0), 3.0)], settings)
    uv1_values = [uv for face in mesh.uv1 for uv in face]
    assert min(value[1] for value in uv1_values) == 0.0
    assert max(value[1] for value in uv1_values) == 1.0


def test_speed_normalization_uses_collapsed_samples():
    settings = MeshSettings(start_width=1.0, end_width=1.0, uv_speed_scale=1.0)
    mesh = build_x_card_mesh(
        [point((0.0, 0.0, 0.0), 100.0), point((0.0, 0.0, 0.0), 1.0), point((0.0, 0.0, -1.0), 3.0)],
        settings,
    )
    uv1_values = [uv for face in mesh.uv1 for uv in face]
    assert min(value[1] for value in uv1_values) == 0.0
    assert max(value[1] for value in uv1_values) == 1.0


def test_max_segment_count_hard_caps_generated_faces():
    points = [
        point((0.0, 0.0, 0.0), 1.0),
        point((0.5, 1.0, -0.4), 1.2),
        point((1.0, -1.0, -0.8), 1.4),
        point((1.5, 1.2, -1.2), 1.6),
        point((2.0, 0.0, -1.6), 1.8),
    ]
    uncapped = build_x_card_mesh(
        points,
        MeshSettings(
            base_segment_density=1.0,
            curvature_refine_strength=6.0,
            curvature_density_max_multiplier=8.0,
            max_segment_count=0,
        ),
    )
    capped = build_x_card_mesh(
        points,
        MeshSettings(
            base_segment_density=1.0,
            curvature_refine_strength=6.0,
            curvature_density_max_multiplier=8.0,
            max_segment_count=4,
        ),
    )

    assert len(capped.faces) < len(uncapped.faces)
    assert len(capped.faces) == 8


def test_target_face_count_controls_rebuild_face_budget():
    points = [
        point((0.0, 0.0, 0.0), 1.0),
        point((0.5, 1.0, -0.4), 1.2),
        point((1.0, -1.0, -0.8), 1.4),
        point((1.5, 1.2, -1.2), 1.6),
        point((2.0, 0.0, -1.6), 1.8),
    ]
    mesh = build_x_card_mesh(
        points,
        MeshSettings(
            base_segment_density=1.0,
            curvature_refine_strength=6.0,
            curvature_density_max_multiplier=8.0,
            target_face_count=10,
            max_segment_count=0,
        ),
    )

    assert len(mesh.faces) == 10


def test_target_face_count_rounds_up_to_even_face_total_for_dual_strip_mesh():
    points = [
        point((0.0, 0.0, 0.0), 1.0),
        point((0.5, 1.0, -0.4), 1.2),
        point((1.0, -1.0, -0.8), 1.4),
        point((1.5, 1.2, -1.2), 1.6),
        point((2.0, 0.0, -1.6), 1.8),
    ]
    mesh = build_x_card_mesh(
        points,
        MeshSettings(
            base_segment_density=1.0,
            curvature_refine_strength=6.0,
            curvature_density_max_multiplier=8.0,
            target_face_count=9,
            max_segment_count=0,
        ),
    )

    assert len(mesh.faces) == 10


def test_max_segment_count_still_clamps_when_target_face_count_is_higher():
    points = [
        point((0.0, 0.0, 0.0), 1.0),
        point((0.5, 1.0, -0.4), 1.2),
        point((1.0, -1.0, -0.8), 1.4),
        point((1.5, 1.2, -1.2), 1.6),
        point((2.0, 0.0, -1.6), 1.8),
    ]
    mesh = build_x_card_mesh(
        points,
        MeshSettings(
            base_segment_density=1.0,
            curvature_refine_strength=6.0,
            curvature_density_max_multiplier=8.0,
            target_face_count=20,
            max_segment_count=3,
        ),
    )

    assert len(mesh.faces) == 6
