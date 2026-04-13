from waterfall_tool.core.trajectory import simulate_guided_trajectory, simulate_trajectory
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
        return CollisionSample(hit=True, point=end, normal=(0.0, 0.0, 1.0), support=0.1)


def test_no_collision_falls_under_gravity():
    settings = EmitterSettings(speed=0.0, gravity=10.0, drag=0.0, time_step=0.1, step_count=3)
    points = simulate_trajectory((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), settings, NoCollision())
    assert len(points) == 4
    assert points[-1].position[2] < points[0].position[2]
    assert points[-1].attached is False


def test_collision_with_support_slides_along_surface():
    settings = EmitterSettings(speed=4.0, gravity=10.0, drag=0.0, time_step=0.1, step_count=6, attach_strength=1.0)
    points = simulate_trajectory((0.0, 0.0, 0.15), (1.0, 0.0, -0.2), settings, GroundCollision())
    attached_points = [point for point in points if point.attached]
    assert attached_points
    assert attached_points[-1].position[2] == 0.0
    assert attached_points[-1].velocity[2] == 0.0


def test_weak_support_detaches_and_keeps_falling():
    settings = EmitterSettings(speed=2.0, gravity=10.0, drag=0.0, time_step=0.1, step_count=3, detach_threshold=0.5)
    points = simulate_trajectory((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), settings, WeakSupportCollision())
    assert all(point.attached is False for point in points[1:])
    assert points[-1].velocity[2] < 0.0


def test_guided_reflow_keeps_manual_points_when_there_is_no_collision():
    settings = EmitterSettings(speed=4.0, gravity=10.0, drag=0.0, time_step=0.1, step_count=4)
    guide = [(0.0, 0.0, 1.0), (0.5, 0.0, 0.5), (1.0, 0.0, 0.0)]
    points = simulate_guided_trajectory(guide, [4.0, 3.0, 2.0], settings, NoCollision())
    assert [point.position for point in points] == guide


def test_guided_reflow_snaps_supported_points_to_surface():
    settings = EmitterSettings(speed=4.0, gravity=10.0, drag=0.0, time_step=0.1, step_count=4, attach_strength=1.0)
    guide = [(0.0, 0.0, 1.0), (0.5, 0.0, -0.5), (1.0, 0.0, -1.0)]
    points = simulate_guided_trajectory(guide, [4.0, 3.0, 2.0], settings, GroundCollision())
    assert points[1].position[2] == 0.0
    assert points[2].position[2] == 0.0
    assert points[1].attached is True
