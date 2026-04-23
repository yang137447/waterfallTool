from waterfall_tool.core.frames import build_frames
from waterfall_tool.core.types import CurveSample
from waterfall_tool.core.vector_math import dot, length


def sample(position, tangent, surface_normal=None):
    return CurveSample(position=position, tangent=tangent, speed=1.0, arc_length=0.0, t=0.0, surface_normal=surface_normal)


def test_frames_are_orthonormal():
    frames = build_frames(
        [
            sample((0.0, 0.0, 0.0), (0.0, 0.0, -1.0)),
            sample((0.0, 0.0, -1.0), (1.0, 0.0, -1.0)),
        ]
    )
    for frame in frames:
        assert round(length(frame.tangent), 6) == 1.0
        assert round(length(frame.normal), 6) == 1.0
        assert round(length(frame.binormal), 6) == 1.0
        assert round(dot(frame.tangent, frame.normal), 6) == 0.0
        assert round(dot(frame.tangent, frame.binormal), 6) == 0.0


def test_frames_do_not_flip_for_vertical_curve():
    frames = build_frames(
        [
            sample((0.0, 0.0, 0.0), (0.0, 0.0, -1.0)),
            sample((0.0, 0.0, -1.0), (0.0, 0.0, -1.0)),
            sample((0.0, 0.0, -2.0), (0.0, 0.0, -1.0)),
        ]
    )
    assert frames[0].normal == frames[1].normal == frames[2].normal


def test_frames_align_binormal_to_surface_normal():
    frames = build_frames(
        [
            sample((0.0, 0.0, 0.0), (0.0, 0.0, -1.0), surface_normal=(1.0, 0.0, 0.0)),
            sample((0.0, 0.0, -1.0), (0.0, 1.0, -1.0), surface_normal=(1.0, 0.0, 0.0)),
        ]
    )
    # The binormal should be aligned with the surface normal (1.0, 0.0, 0.0) or its inverse
    for frame in frames:
        assert round(abs(frame.binormal[0]), 6) == 1.0
        assert round(frame.binormal[1], 6) == 0.0
        assert round(frame.binormal[2], 6) == 0.0


def test_frames_keep_main_strip_parallel_to_surface_when_attached():
    frames = build_frames(
        [
            sample((0.0, 0.0, 0.0), (0.0, 0.0, -1.0), surface_normal=(1.0, 0.0, 0.0)),
            sample((0.0, 0.0, -1.0), (0.0, 1.0, -1.0), surface_normal=(1.0, 0.0, 0.0)),
        ]
    )
    for frame in frames:
        assert round(dot(frame.normal, (1.0, 0.0, 0.0)), 6) == 0.0
