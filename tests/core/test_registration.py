from waterfall_tool import bl_info, register, unregister


def test_addon_module_exposes_blender_entrypoints():
    assert bl_info["name"] == "Waterfall Tool"
    assert callable(register)
    assert callable(unregister)
