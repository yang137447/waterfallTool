from math import acos, degrees

import pytest

from waterfall_tool.core.trajectory import (
    _blend_surface_normal,
    simulate_guided_trajectory,
    simulate_trajectory,
)
from waterfall_tool.core.types import CollisionProvider, CollisionSample, EmitterSettings


class NoCollision(CollisionProvider):
    def sample(self, start, end):
        return CollisionSample(hit=False)


class GroundCollision(CollisionProvider):
    def sample(self, start, end):
        if end[2] <= 0.0:
            return CollisionSample(hit=True, point=(end[0], end[1], 0.0), normal=(0.0, 0.0, 1.0), support=1.0)
        return CollisionSample(hit=False)


class WeakSupportCollision(CollisionProvider):
    def sample(self, start, end):
        return CollisionSample(hit=True, point=end, normal=(0.0, 0.0, -1.0), support=0.1)


class StickyGapCollision(CollisionProvider):
    def __init__(self):
        self.calls = 0

    def sample(self, start, end):
        self.calls += 1
        if self.calls == 2:
            return CollisionSample(hit=False)
        if start[2] >= 0.0 and end[2] <= 0.0:
            return CollisionSample(hit=True, point=((start[0] + end[0]) * 0.5, 0.0, 0.0), normal=(0.0, 0.0, 1.0), support=1.0)
        if start[2] > 0.0 and end[2] < start[2]:
            return CollisionSample(hit=True, point=(end[0], end[1], 0.0), normal=(0.0, 0.0, 1.0), support=1.0)
        return CollisionSample(hit=False)


class JaggedSurfaceCollision(CollisionProvider):
    def sample(self, start, end):
        if end[2] >= start[2]:
            return CollisionSample(hit=False)
        phase = int(abs(end[0]) * 10.0) % 2
        normal = (0.0, 0.0, 1.0) if phase == 0 else (0.65, 0.0, 0.7599342076785331)
        return CollisionSample(hit=True, point=(end[0], end[1], 0.0), normal=normal, support=max(0.0, normal[2]))


def _angle_degrees(a, b):
    dot_value = a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
    length_a = (a[0] ** 2 + a[1] ** 2 + a[2] ** 2) ** 0.5
    length_b = (b[0] ** 2 + b[1] ** 2 + b[2] ** 2) ** 0.5
    cosine = max(-1.0, min(1.0, dot_value / (length_a * length_b)))
    return degrees(acos(cosine))


def test_no_collision_falls_under_gravity():
    settings = EmitterSettings(speed=0.0, gravity=10.0, drag=0.0, time_step=0.1, step_count=3)
    points = simulate_trajectory((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), settings, NoCollision())
    assert len(points) == 4
    assert points[-1].position[2] < points[0].position[2]
    assert points[-1].attached is False


def test_collision_with_support_slides_along_surface():
    settings = EmitterSettings(speed=4.0, gravity=10.0, drag=0.0, time_step=0.1, step_count=6, attach_strength=1.0, surface_offset=0.01)
    points = simulate_trajectory((0.0, 0.0, 0.15), (1.0, 0.0, -0.2), settings, GroundCollision())
    attached_points = [point for point in points if point.attached]
    assert attached_points
    assert attached_points[-1].position[2] > 0.0
    assert attached_points[-1].velocity[2] == 0.0


def test_supported_surface_contact_loses_speed_over_time_due_to_surface_friction():
    settings = EmitterSettings(speed=4.0, gravity=10.0, drag=0.0, time_step=0.1, step_count=8, attach_strength=1.0, surface_offset=0.01)
    points = simulate_trajectory((0.0, 0.0, 0.15), (1.0, 0.0, -0.2), settings, GroundCollision())
    attached_points = [point for point in points if point.attached]
    assert len(attached_points) >= 2
    assert attached_points[-1].speed < attached_points[0].speed


def test_attached_surface_follow_does_not_drop_to_freefall_on_small_sampling_gap():
    settings = EmitterSettings(speed=3.0, gravity=10.0, drag=0.0, time_step=0.1, step_count=5, attach_strength=1.0, surface_offset=0.01)
    points = simulate_trajectory((0.0, 0.0, 0.2), (1.0, 0.0, -0.1), settings, StickyGapCollision())
    assert points[1].attached is True
    assert points[2].attached is True
    assert points[2].position[2] > 0.0


def test_surface_normal_blending_softens_triangle_normal_changes():
    blended = _blend_surface_normal((0.0, 0.0, 1.0), (0.4, 0.0, 0.916515138991168))
    assert 0.0 < blended[0] < 0.4
    assert blended[2] > 0.916515138991168


def test_macro_surface_field_reduces_attached_normal_jitter_on_jagged_surface():
    settings = EmitterSettings(
        speed=2.0,
        gravity=10.0,
        drag=0.0,
        time_step=0.1,
        step_count=8,
        attach_strength=1.0,
        detach_threshold=0.2,
        surface_offset=0.01,
        surface_flow_radius=0.25,
        surface_flow_samples=12,
        surface_flow_relaxation=1.0,
        surface_flow_inertia=0.8,
    )
    points = simulate_trajectory((0.0, 0.0, 0.2), (1.0, 0.0, -0.2), settings, JaggedSurfaceCollision())
    attached_normals = [point.surface_normal for point in points if point.attached and point.surface_normal is not None]
    assert len(attached_normals) >= 3
    adjacent_angles = [_angle_degrees(attached_normals[i], attached_normals[i + 1]) for i in range(len(attached_normals) - 1)]
    assert max(adjacent_angles) < 35.0


def test_weak_support_still_resolves_hit_without_penetrating_surface():
    settings = EmitterSettings(speed=2.0, gravity=10.0, drag=0.0, time_step=0.1, step_count=3, detach_threshold=0.5)
    points = simulate_trajectory((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), settings, WeakSupportCollision())
    assert all(point.attached is False for point in points[1:])
    assert points[-1].position[2] > 0.0
    assert points[-1].velocity[2] == 0.0


def test_free_simulation_terminates_when_speed_drops_below_terminal_speed():
    settings = EmitterSettings(
        speed=1.0,
        gravity=0.0,
        drag=20.0,
        time_step=0.1,
        step_count=10,
        terminal_speed=0.1,
    )
    points = simulate_trajectory((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), settings, NoCollision())
    assert len(points) == 2
    assert points[-1].speed <= 0.1


def test_free_simulation_terminates_when_below_cutoff_height():
    settings = EmitterSettings(
        speed=0.0,
        gravity=10.0,
        drag=0.0,
        time_step=0.1,
        step_count=10,
        cutoff_height=0.95,
    )
    points = simulate_trajectory((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), settings, NoCollision())
    assert len(points) == 2
    assert points[-1].position[2] <= 0.95


def test_guided_reflow_keeps_manual_points_when_there_is_no_collision():
    settings = EmitterSettings(speed=4.0, gravity=10.0, drag=0.0, time_step=0.1, step_count=4)
    guide = [(0.0, 0.0, 1.0), (0.5, 0.0, 0.5), (1.0, 0.0, 0.0)]
    points = simulate_guided_trajectory(guide, [4.0, 3.0, 2.0], settings, NoCollision())
    assert [point.position for point in points] == guide


def test_guided_reflow_snaps_supported_points_to_surface():
    settings = EmitterSettings(speed=4.0, gravity=10.0, drag=0.0, time_step=0.1, step_count=4, attach_strength=1.0, surface_offset=0.01)
    guide = [(0.0, 0.0, 1.0), (0.5, 0.0, -0.5), (1.0, 0.0, -1.0)]
    points = simulate_guided_trajectory(guide, [4.0, 3.0, 2.0], settings, GroundCollision())
    assert points[1].position[2] > 0.0
    assert points[2].position[2] > 0.0
    assert points[1].attached is True


def test_guided_reflow_uses_settings_speed_when_guide_speeds_is_empty():
    settings = EmitterSettings(speed=4.0, gravity=10.0, drag=0.0, time_step=0.1, step_count=4)
    guide = [(0.0, 0.0, 1.0), (0.5, 0.0, 0.5), (1.0, 0.0, 0.0)]
    points = simulate_guided_trajectory(guide, [], settings, NoCollision())
    assert [point.position for point in points] == guide
    assert [point.speed for point in points] == pytest.approx([4.0, 4.0, 4.0])
