import pytest

from waterfall_tool.core.vector_math import add, cross, dot, length, normalize, project_on_plane, scale, sub


def test_vector_operations_are_tuple_based():
    assert add((1.0, 2.0, 3.0), (4.0, 5.0, 6.0)) == (5.0, 7.0, 9.0)
    assert sub((4.0, 5.0, 6.0), (1.0, 2.0, 3.0)) == (3.0, 3.0, 3.0)
    assert scale((1.0, -2.0, 3.0), 2.0) == (2.0, -4.0, 6.0)
    assert dot((1.0, 2.0, 3.0), (3.0, 2.0, 1.0)) == 10.0
    assert cross((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)) == (0.0, 0.0, 1.0)


def test_normalize_handles_zero_length_vectors():
    assert normalize((0.0, 0.0, 0.0)) == (0.0, 0.0, 0.0)
    assert normalize((0.0, 3.0, 4.0)) == pytest.approx((0.0, 0.6, 0.8))
    assert length((0.0, 3.0, 4.0)) == 5.0


def test_project_on_plane_removes_normal_component():
    assert project_on_plane((1.0, 2.0, 3.0), (0.0, 0.0, 1.0)) == (1.0, 2.0, 0.0)
