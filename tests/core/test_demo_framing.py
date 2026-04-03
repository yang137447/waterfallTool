from waterfall_tool.demo.framing import compute_demo_camera_frame


def test_compute_demo_camera_frame_uses_oblique_angle_and_frames_height():
    frame = compute_demo_camera_frame(
        bounds_min=(-4.2, -1.8, -2.1),
        bounds_max=(4.2, 2.8, 5.5),
    )

    assert frame.location[0] < 0.0
    assert frame.location[1] < -8.0
    assert frame.location[2] > 3.0
    assert frame.target[2] > 1.0
