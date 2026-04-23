from __future__ import annotations

from math import acos, radians

from .types import CollisionProvider, EmitterSettings, TrajectoryPoint, Vector3
from .vector_math import add, dot, length, normalize, project_on_plane, scale

SURFACE_FRICTION = 0.2
SURFACE_NORMAL_BLEND = 0.75
SURFACE_FOLLOW_MULTIPLIER = 3.0


def _apply_drag(velocity: Vector3, drag: float, time_step: float) -> Vector3:
    factor = max(0.0, 1.0 - drag * time_step)
    return scale(velocity, factor)


def _advance_freefall(velocity: Vector3, settings: EmitterSettings) -> Vector3:
    dragged = _apply_drag(velocity, settings.drag, settings.time_step)
    return (dragged[0], dragged[1], dragged[2] - settings.gravity * settings.time_step)


def _reduce_speed(velocity: Vector3, speed_loss: float) -> Vector3:
    current_speed = length(velocity)
    if current_speed <= 1.0e-8 or speed_loss <= 0.0:
        return velocity
    return scale(velocity, max(0.0, current_speed - speed_loss) / current_speed)


def _apply_surface_friction(velocity: Vector3, surface_normal: Vector3, settings: EmitterSettings) -> Vector3:
    support = max(0.0, min(1.0, normalize(surface_normal)[2]))
    friction_loss = SURFACE_FRICTION * settings.gravity * support * settings.time_step
    return _reduce_speed(velocity, friction_loss)


def _advance_attached(velocity: Vector3, surface_normal: Vector3, settings: EmitterSettings) -> Vector3:
    tangent_velocity = project_on_plane(_apply_drag(velocity, settings.drag, settings.time_step), surface_normal)
    gravity_step = project_on_plane((0.0, 0.0, -settings.gravity * settings.time_step), surface_normal)
    surface_velocity = project_on_plane(add(tangent_velocity, gravity_step), surface_normal)
    return _apply_surface_friction(surface_velocity, surface_normal, settings)


def _blend_surface_normal(previous_normal: Vector3, current_normal: Vector3) -> Vector3:
    blended = (
        previous_normal[0] * SURFACE_NORMAL_BLEND + current_normal[0] * (1.0 - SURFACE_NORMAL_BLEND),
        previous_normal[1] * SURFACE_NORMAL_BLEND + current_normal[1] * (1.0 - SURFACE_NORMAL_BLEND),
        previous_normal[2] * SURFACE_NORMAL_BLEND + current_normal[2] * (1.0 - SURFACE_NORMAL_BLEND),
    )
    if length(blended) <= 1.0e-8:
        return normalize(current_normal)
    return normalize(blended)


def _sample_surface_follow(
    candidate_position: Vector3,
    surface_normal: Vector3,
    settings: EmitterSettings,
    collision_provider: CollisionProvider,
):
    # Extend follow distance to help water stick to surfaces without popping off on small bumps
    follow_distance = max(settings.surface_offset * 3.0, settings.surface_offset * SURFACE_FOLLOW_MULTIPLIER)
    follow_start = add(candidate_position, scale(surface_normal, settings.surface_offset))
    follow_end = add(candidate_position, scale(surface_normal, -follow_distance))
    return collision_provider.sample(follow_start, follow_end)


def _collision_response(
    candidate_velocity: Vector3,
    collision,
    settings: EmitterSettings,
    resolved_normal: Vector3 | None = None,
) -> tuple[Vector3, Vector3, bool, Vector3]:
    normal = normalize(resolved_normal if resolved_normal is not None else collision.normal)
    hit_position = add(collision.point, scale(normal, settings.surface_offset))
    slide_velocity = project_on_plane(candidate_velocity, normal)
    impact_speed = max(0.0, -dot(candidate_velocity, normal))
    slide_velocity = _reduce_speed(slide_velocity, impact_speed * SURFACE_FRICTION)
    
    adhesion_support = 1.0 if normal[2] >= -1e-4 else max(0.0, 1.0 + normal[2])
    attached = adhesion_support * settings.attach_strength >= settings.detach_threshold
    return hit_position, slide_velocity, attached, normal


def _should_terminate(point: TrajectoryPoint, settings: EmitterSettings) -> bool:
    if settings.terminal_speed > 0.0 and point.speed <= settings.terminal_speed:
        return True
    if point.position[2] <= settings.cutoff_height:
        return True
    return False


def simulate_trajectory(
    start_position: Vector3,
    direction: Vector3,
    settings: EmitterSettings,
    collision_provider: CollisionProvider,
) -> list[TrajectoryPoint]:
    unit_direction = normalize(direction)
    # 保护: 当 unit_direction 是零向量时 (如果 direction 是零向量)
    if length(unit_direction) < 1.0e-8:
        unit_direction = (0.0, 0.0, -1.0)
    velocity = scale(unit_direction, settings.speed)
    points = [TrajectoryPoint(position=start_position, velocity=velocity, speed=length(velocity), attached=False, surface_normal=None)]
    position = start_position
    attached = False
    surface_normal = (0.0, 0.0, 1.0)

    for _ in range(settings.step_count):
        was_attached = attached
        previous_surface_normal = surface_normal
        if was_attached:
            candidate_velocity = _advance_attached(velocity, surface_normal, settings)
            tangent_step = scale(candidate_velocity, settings.time_step)
            candidate_position = add(position, tangent_step)
            collision_start = add(position, scale(surface_normal, settings.surface_offset))
            collision_end = add(candidate_position, scale(surface_normal, -settings.surface_offset))
        else:
            candidate_velocity = _advance_freefall(velocity, settings)
            candidate_position = add(position, scale(candidate_velocity, settings.time_step))
            collision_start = position
            collision_end = candidate_position

        collision = collision_provider.sample(collision_start, collision_end)
        follow_collision = None
        if was_attached and not collision.hit:
            collision = _sample_surface_follow(
                candidate_position,
                surface_normal,
                settings,
                collision_provider,
            )

        if collision.hit:
            start_to_end = (collision_end[0] - collision_start[0], collision_end[1] - collision_start[1], collision_end[2] - collision_start[2])
            dist_total = length(start_to_end)
            start_to_hit = (collision.point[0] - collision_start[0], collision.point[1] - collision_start[1], collision.point[2] - collision_start[2])
            dist_hit = length(start_to_hit)
            t = min(1.0, max(0.0, dist_hit / dist_total)) if dist_total > 1.0e-8 else 1.0

            velocity_at_impact = (
                velocity[0] + (candidate_velocity[0] - velocity[0]) * t,
                velocity[1] + (candidate_velocity[1] - velocity[1]) * t,
                velocity[2] + (candidate_velocity[2] - velocity[2]) * t,
            )

            resolved_normal = normalize(collision.normal)
            if was_attached:
                resolved_normal = _blend_surface_normal(previous_surface_normal, resolved_normal)

            position, velocity, attached, surface_normal = _collision_response(
                velocity_at_impact,
                collision,
                settings,
                resolved_normal,
            )
            if length(velocity) <= 1.0e-8:
                velocity = (0.0, 0.0, 0.0)
            point = TrajectoryPoint(position=position, velocity=velocity, speed=length(velocity), attached=attached, surface_normal=surface_normal)
            points.append(point)
            if _should_terminate(point, settings):
                break
            continue

        position = candidate_position
        velocity = candidate_velocity
        attached = False
        point = TrajectoryPoint(position=position, velocity=velocity, speed=length(velocity), attached=False, surface_normal=None)
        points.append(point)
        if _should_terminate(point, settings):
            break

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
            result.append(TrajectoryPoint(position=position, velocity=(0.0, 0.0, 0.0), speed=speed, attached=False, surface_normal=None))
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

        if collision.hit:
            requested_velocity = scale(direction, requested_speed)
            previous_velocity = result[-1].velocity if length(result[-1].velocity) > 1.0e-8 else requested_velocity
            hit_position, velocity, attached, _normal = _collision_response(requested_velocity, collision, settings)
            result.append(TrajectoryPoint(position=hit_position, velocity=velocity, speed=length(velocity), attached=attached, surface_normal=_normal))
        else:
            velocity = scale(direction, requested_speed)
            result.append(TrajectoryPoint(position=requested, velocity=velocity, speed=length(velocity), attached=False, surface_normal=None))

    return result
