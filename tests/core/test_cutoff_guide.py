from waterfall_tool.adapters.blender_cutoff_guide import build_cutoff_outline


def test_build_cutoff_outline_uses_height_offset_and_size():
    vertices, edges = build_cutoff_outline(3.0, 2.0, -1.0, 8.0, 4.0)

    assert vertices == [
        (-2.0, -3.0, 3.0),
        (6.0, -3.0, 3.0),
        (6.0, 1.0, 3.0),
        (-2.0, 1.0, 3.0),
    ]
    assert edges == [(0, 1), (1, 2), (2, 3), (3, 0)]

