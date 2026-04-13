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
    assert len(mesh.vertices) == 8
    assert len(mesh.faces) == 2
    assert len(mesh.uv0) == 2
    assert len(mesh.uv1) == 2


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
