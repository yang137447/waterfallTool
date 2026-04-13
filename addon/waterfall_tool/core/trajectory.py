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


def simulate_guided_trajectory(
    guide_positions: list[Vector3],
    guide_speeds: list[float],
    settings: EmitterSettings,
    collision_provider: CollisionProvider,
) -> list[TrajectoryPoint]:
    if not guide_positions:
        return []

    result: list[TrajectoryPoint] = []
    for index, position in enumerate(guide_positions):
        if index == 0:
            speed = guide_speeds[0] if guide_speeds else settings.speed
            result.append(TrajectoryPoint(position=position, velocity=(0.0, 0.0, 0.0), speed=speed, attached=False))
            continue

        previous = result[-1].position
        requested = guide_positions[index]
        requested_speed = (
            guide_speeds[index]
            if index < len(guide_speeds)
            else (guide_speeds[-1] if guide_speeds else settings.speed)
        )
        direction = normalize((requested[0] - previous[0], requested[1] - previous[1], requested[2] - previous[2]))
        collision = collision_provider.sample(previous, requested)

        if collision.hit and collision.support * settings.attach_strength >= settings.detach_threshold:
            velocity = project_on_plane(scale(direction, requested_speed), collision.normal)
            result.append(TrajectoryPoint(position=collision.point, velocity=velocity, speed=length(velocity), attached=True))
        else:
            velocity = scale(direction, requested_speed)
            result.append(TrajectoryPoint(position=requested, velocity=velocity, speed=length(velocity), attached=False))

    return result
