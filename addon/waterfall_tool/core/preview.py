from __future__ import annotations

from .solver import advance_particle
from .types import FlowSettings, ParticleState


def apply_control_influences(
    breakup: float,
    split_score: float,
    position,
    control_sample,
    settings: FlowSettings,
):
    _ = position
    return {
        "breakup": breakup + control_sample.get("breakup_boost", 0.0),
        "split_score": split_score + control_sample.get("split_boost", 0.0) * settings.split_sensitivity,
    }


def build_preview_paths(emitter_points, collider, settings: FlowSettings, steps: int, control_sampler=None):
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
            control = control_sampler(particle.position) if control_sampler is not None else {"breakup_boost": 0.0, "split_boost": 0.0}
            influence = apply_control_influences(
                particle.breakup,
                particle.split_score,
                particle.position,
                control,
                settings,
            )
            particle = ParticleState(
                position=particle.position,
                velocity=particle.velocity,
                water=particle.water,
                attached=particle.attached,
                split_score=influence["split_score"],
                breakup=influence["breakup"],
            )
            path.append(particle)
        paths.append(path)
    return paths
