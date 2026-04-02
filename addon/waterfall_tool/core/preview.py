from __future__ import annotations

from .solver import advance_particle
from .types import FlowSettings, ParticleState


def build_preview_paths(emitter_points, collider, settings: FlowSettings, steps: int):
    paths = []
    for point in emitter_points:
        particle = ParticleState(
            position=point,
            velocity=(0.0, 0.0, -0.5),
            water=1.0,
            attached=True,
            split_score=0.0,
            breakup=0.0,
        )
        path = [particle]
        for _ in range(steps):
            sample = collider.sample(particle.position, particle.velocity)
            particle = advance_particle(particle, sample, settings)
            path.append(particle)
        paths.append(path)
    return paths
