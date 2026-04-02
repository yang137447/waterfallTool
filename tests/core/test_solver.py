from waterfall_tool.core.solver import advance_particle
from waterfall_tool.core.types import CollisionSample, FlowSettings, ParticleState


def test_particle_stays_attached_on_supported_surface():
    particle = ParticleState(
        position=(0.0, 0.0, 0.0),
        velocity=(0.0, 0.0, -1.0),
        water=1.0,
        attached=True,
        split_score=0.0,
        breakup=0.0,
    )
    sample = CollisionSample(
        hit=True,
        normal=(0.0, 1.0, 0.0),
        tangent=(1.0, 0.0, -0.1),
        support=0.9,
        obstacle=0.1,
    )
    settings = FlowSettings(
        time_step=0.1,
        gravity=9.8,
        attachment=0.8,
        split_sensitivity=0.5,
        breakup_rate=0.25,
    )

    updated = advance_particle(particle, sample, settings)

    assert updated.attached is True
    assert updated.position[0] > particle.position[0]


def test_particle_detaches_and_accumulates_split_when_support_is_lost():
    particle = ParticleState(
        position=(0.0, 0.0, 0.0),
        velocity=(0.0, 0.0, -1.0),
        water=1.0,
        attached=True,
        split_score=0.0,
        breakup=0.0,
    )
    sample = CollisionSample(
        hit=True,
        normal=(0.0, 1.0, 0.0),
        tangent=(1.0, 0.0, -0.6),
        support=0.1,
        obstacle=0.9,
    )
    settings = FlowSettings(
        time_step=0.1,
        gravity=9.8,
        attachment=0.8,
        split_sensitivity=0.5,
        breakup_rate=0.25,
    )

    updated = advance_particle(particle, sample, settings)

    assert updated.attached is False
    assert updated.split_score > 0.0
    assert updated.breakup > 0.0
