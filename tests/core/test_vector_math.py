from waterfall_tool.core.vector_math import add, cross, dot, length, normalize, project_on_plane, scale, sub
from waterfall_tool.core.types import CollisionSample, EmitterSettings, MeshData, MeshSettings


def test_vector_operations_are_tuple_based():
    assert add((1.0, 2.0, 3.0), (4.0, 5.0, 6.0)) == (5.0, 7.0, 9.0)
    assert sub((4.0, 5.0, 6.0), (1.0, 2.0, 3.0)) == (3.0, 3.0, 3.0)
    assert scale((1.0, -2.0, 3.0), 2.0) == (2.0, -4.0, 6.0)
    assert dot((1.0, 2.0, 3.0), (3.0, 2.0, 1.0)) == 10.0
    assert cross((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)) == (0.0, 0.0, 1.0)


def test_normalize_handles_zero_length_vectors():
    assert normalize((0.0, 0.0, 0.0)) == (0.0, 0.0, 0.0)
    assert normalize((0.0, 3.0, 4.0)) == (0.0, 0.6, 0.8)
    assert length((0.0, 3.0, 4.0)) == 5.0


def test_project_on_plane_removes_normal_component():
    assert project_on_plane((1.0, 2.0, 3.0), (0.0, 0.0, 1.0)) == (1.0, 2.0, 0.0)


def test_core_type_defaults_match_contract():
    emitter = EmitterSettings()
    assert emitter.speed == 8.0
    assert emitter.gravity == 9.81
    assert emitter.drag == 0.0
    assert emitter.time_step == 0.05
    assert emitter.step_count == 80
    assert emitter.attach_strength == 0.7
    assert emitter.detach_threshold == 0.35

    mesh = MeshSettings()
    assert mesh.base_segment_density == 1.0
    assert mesh.curvature_refine_strength == 1.0
    assert mesh.start_width == 1.0
    assert mesh.end_width == 1.0
    assert mesh.width_falloff == 1.0
    assert mesh.cross_angle_degrees == 90.0
    assert mesh.uv_speed_scale == 1.0

    collision = CollisionSample(hit=False)
    assert collision.hit is False
    assert collision.point == (0.0, 0.0, 0.0)
    assert collision.normal == (0.0, 0.0, 1.0)
    assert collision.support == 0.0


def test_mesh_data_shape_matches_contract():
    mesh_data = MeshData()
    assert mesh_data.vertices == []
    assert mesh_data.faces == []
    assert mesh_data.uv0 == []
    assert mesh_data.uv1 == []
