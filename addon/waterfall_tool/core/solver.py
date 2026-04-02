from __future__ import annotations

from .types import CollisionSample, FlowSettings, ParticleState
from .vector_math import add, normalize, scale


def advance_particle(
    particle: ParticleState,
    sample: CollisionSample,
    settings: FlowSettings,
) -> ParticleState:
    support_score = sample.support * settings.attachment
    attached = sample.hit and support_score >= 0.3

    if attached:
        direction = normalize(sample.tangent)
        velocity = scale(direction, max(0.5, particle.water))
    else:
        velocity = (
            particle.velocity[0],
            particle.velocity[1],
            particle.velocity[2] - settings.gravity * settings.time_step,
        )

    position = add(particle.position, scale(velocity, settings.time_step))
    split_score = particle.split_score + sample.obstacle * settings.split_sensitivity
    breakup = particle.breakup + (1.0 - sample.support) * settings.breakup_rate

    return ParticleState(
        position=position,
        velocity=velocity,
        water=particle.water,
        attached=attached,
        split_score=split_score,
        breakup=breakup,
    )
