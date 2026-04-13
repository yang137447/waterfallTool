from __future__ import annotations

from .types import CollisionProvider, EmitterSettings, TrajectoryPoint, Vector3
from .vector_math import add, length, normalize, project_on_plane, scale


def _apply_drag(velocity: Vector3, drag: float, time_step: float) -> Vector3:
    factor = max(0.0, 1.0 - drag * time_step)
    return scale(velocity, factor)


def _advance_freefall(velocity: Vector3, settings: EmitterSettings) -> Vector3:
    dragged = _apply_drag(velocity, settings.drag, settings.time_step)
    return (dragged[0], dragged[1], dragged[2] - settings.gravity * settings.time_step)


def simulate_trajectory(
    start_position: Vector3,
    direction: Vector3,
    settings: EmitterSettings,
    collision_provider: CollisionProvider,
) -> list[TrajectoryPoint]:
    unit_direction = normalize(direction)
    velocity = scale(unit_direction, settings.speed)
    points = [TrajectoryPoint(position=start_position, velocity=velocity, speed=length(velocity), attached=False)]
    position = start_position

    for _ in range(settings.step_count):
        candidate_velocity = _advance_freefall(velocity, settings)
        candidate_position = add(position, scale(candidate_velocity, settings.time_step))
        collision = collision_provider.sample(position, candidate_position)

        if collision.hit and collision.support * settings.attach_strength >= settings.detach_threshold:
            slide_velocity = project_on_plane(candidate_velocity, collision.normal)
            position = collision.point
            velocity = slide_velocity
            points.append(TrajectoryPoint(position=position, velocity=velocity, speed=length(velocity), attached=True))
            continue

        position = candidate_position
        velocity = candidate_velocity
        points.append(TrajectoryPoint(position=position, velocity=velocity, speed=length(velocity), attached=False))

    return points
