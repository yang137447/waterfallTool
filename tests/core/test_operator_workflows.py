from __future__ import annotations

import types
from types import SimpleNamespace

from waterfall_tool.core.types import MeshData
from waterfall_tool.operators import bake as bake_ops
from waterfall_tool.operators import preview as preview_ops
from waterfall_tool.operators.preview import (
    apply_persistent_handler,
    refresh_curve_preview,
    resolve_curves_from_update,
    resolve_emitter_curve_targets,
    resolve_preview_parent,
    should_refresh_curve_from_update,
    set_preview_hidden,
)
from waterfall_tool.operators.simulate import (
    _copy_curve_style_from_template,
    _copy_preview_materials,
    _resolve_source_curve_template,
    _resolve_curve_name_for_emitter,
    generate_all_enabled_emitters,
    iter_enabled_emitters,
)


class FakeObject:
    def __init__(
        self,
        name: str,
        object_type: str,
        *,
        props: dict | None = None,
        waterfall_emitter=None,
        waterfall_curve=None,
    ) -> None:
        self.name = name
        self.type = object_type
        self._props = props or {}
        self.waterfall_emitter = waterfall_emitter
        self.waterfall_curve = waterfall_curve
        self.hide_viewport = False
        self.hide_render = False
        self._hidden_calls: list[bool] = []

    def get(self, key, default=None):
        return self._props.get(key, default)

    def hide_set(self, hidden: bool):
        self._hidden_calls.append(hidden)


def test_iter_enabled_emitters_filters_only_enabled_empty_objects():
    enabled_emitter = FakeObject(
        "Emitter_A",
        "EMPTY",
        waterfall_emitter=SimpleNamespace(enabled=True),
        waterfall_curve=SimpleNamespace(),
    )
    disabled_emitter = FakeObject(
        "Emitter_B",
        "EMPTY",
        waterfall_emitter=SimpleNamespace(enabled=False),
        waterfall_curve=SimpleNamespace(),
    )
    mesh_object = FakeObject(
        "Mesh",
        "MESH",
        waterfall_emitter=SimpleNamespace(enabled=True),
        waterfall_curve=SimpleNamespace(),
    )

    found = list(iter_enabled_emitters([enabled_emitter, disabled_emitter, mesh_object]))

    assert found == [enabled_emitter]


def test_generate_all_enabled_emitters_runs_for_each_enabled_empty(monkeypatch):
    emitter_a = FakeObject(
        "Emitter_A",
        "EMPTY",
        waterfall_emitter=SimpleNamespace(enabled=True),
        waterfall_curve=SimpleNamespace(),
    )
    emitter_b = FakeObject(
        "Emitter_B",
        "EMPTY",
        waterfall_emitter=SimpleNamespace(enabled=True),
        waterfall_curve=SimpleNamespace(),
    )
    disabled = FakeObject(
        "Emitter_C",
        "EMPTY",
        waterfall_emitter=SimpleNamespace(enabled=False),
        waterfall_curve=SimpleNamespace(),
    )

    invoked: list[str] = []

    def fake_generate(emitter, _context):
        invoked.append(emitter.name)
        return object()

    monkeypatch.setattr("waterfall_tool.operators.simulate.generate_or_resimulate_curve", fake_generate)
    generated_count = generate_all_enabled_emitters(SimpleNamespace(), [emitter_a, emitter_b, disabled])

    assert generated_count == 2
    assert invoked == ["Emitter_A", "Emitter_B"]


def test_resolve_curve_name_for_emitter_reuses_its_own_existing_curve():
    emitter = FakeObject(
        "Emitter_A",
        "EMPTY",
        waterfall_emitter=SimpleNamespace(enabled=True, flow_curve_name="Emitter_A_FlowCurve"),
        waterfall_curve=SimpleNamespace(),
    )
    own_curve = FakeObject(
        "Emitter_A_FlowCurve",
        "CURVE",
        props={"waterfall_flow_curve": True},
        waterfall_emitter=SimpleNamespace(),
        waterfall_curve=SimpleNamespace(emitter_name="Emitter_A"),
    )

    name = _resolve_curve_name_for_emitter(emitter, {"Emitter_A_FlowCurve": own_curve})

    assert name == "Emitter_A_FlowCurve"


def test_resolve_curve_name_for_emitter_avoids_curve_name_copied_from_other_emitter():
    emitter = FakeObject(
        "Emitter_B",
        "EMPTY",
        waterfall_emitter=SimpleNamespace(enabled=True, flow_curve_name="Emitter_A_FlowCurve"),
        waterfall_curve=SimpleNamespace(),
    )
    other_curve = FakeObject(
        "Emitter_A_FlowCurve",
        "CURVE",
        props={"waterfall_flow_curve": True},
        waterfall_emitter=SimpleNamespace(),
        waterfall_curve=SimpleNamespace(emitter_name="Emitter_A"),
    )

    name = _resolve_curve_name_for_emitter(emitter, {"Emitter_A_FlowCurve": other_curve})

    assert name == "Emitter_B_FlowCurve"


def test_resolve_source_curve_template_returns_foreign_curve_when_name_is_copied():
    emitter = FakeObject(
        "Emitter_B",
        "EMPTY",
        waterfall_emitter=SimpleNamespace(enabled=True, flow_curve_name="Emitter_A_FlowCurve"),
        waterfall_curve=SimpleNamespace(),
    )
    other_curve = FakeObject(
        "Emitter_A_FlowCurve",
        "CURVE",
        props={"waterfall_flow_curve": True},
        waterfall_emitter=SimpleNamespace(),
        waterfall_curve=SimpleNamespace(emitter_name="Emitter_A"),
    )

    source_template = _resolve_source_curve_template(emitter, {"Emitter_A_FlowCurve": other_curve})

    assert source_template is other_curve


def test_copy_curve_style_from_template_copies_curve_shape_and_uv_fields():
    source_curve = FakeObject(
        "SourceCurve",
        "CURVE",
        props={"waterfall_flow_curve": True},
        waterfall_emitter=SimpleNamespace(),
        waterfall_curve=SimpleNamespace(
            curve_mode="PHYSICS_ASSISTED",
            preview_enabled=True,
            width_density=3,
            longitudinal_step_length=0.2,
            curvature_min_angle_degrees=10.0,
            start_width=1.2,
            end_width=0.7,
            width_falloff=1.4,
            base_width=2.0,
            speed_expansion=0.3,
            enable_cross_strip=False,
            cross_angle=45.0,
            cross_width_scale=0.8,
            cross_ramp_length=1.2,
            uv_base_speed=6.0,
            uv_speed_smoothing_length=0.5,
        ),
    )
    target_curve = FakeObject(
        "TargetCurve",
        "CURVE",
        props={"waterfall_flow_curve": True},
        waterfall_emitter=SimpleNamespace(),
        waterfall_curve=SimpleNamespace(
            curve_mode="MANUAL_SHAPE",
            preview_enabled=False,
            width_density=1,
            longitudinal_step_length=0.5,
            curvature_min_angle_degrees=15.0,
            start_width=1.0,
            end_width=1.0,
            width_falloff=1.0,
            base_width=1.0,
            speed_expansion=0.0,
            enable_cross_strip=True,
            cross_angle=90.0,
            cross_width_scale=1.0,
            cross_ramp_length=0.0,
            uv_base_speed=8.0,
            uv_speed_smoothing_length=0.0,
        ),
    )

    _copy_curve_style_from_template(source_curve, target_curve)

    assert target_curve.waterfall_curve.curve_mode == "PHYSICS_ASSISTED"
    assert target_curve.waterfall_curve.width_density == 3
    assert target_curve.waterfall_curve.base_width == 2.0
    assert target_curve.waterfall_curve.enable_cross_strip is False
    assert target_curve.waterfall_curve.cross_ramp_length == 1.2
    assert target_curve.waterfall_curve.uv_speed_smoothing_length == 0.5


def test_copy_preview_materials_replaces_target_material_stack():
    source_preview = FakeObject("SourcePreview", "MESH")
    target_preview = FakeObject("TargetPreview", "MESH")
    source_preview.data = SimpleNamespace(materials=["Mat_A", "Mat_B"])
    target_preview.data = SimpleNamespace(materials=["OldMat"])

    _copy_preview_materials(source_preview, target_preview)

    assert target_preview.data.materials == ["Mat_A", "Mat_B"]


def test_resolve_emitter_curve_targets_handles_selected_emitter_or_curve():
    emitter = FakeObject(
        "Emitter",
        "EMPTY",
        waterfall_emitter=SimpleNamespace(enabled=True, flow_curve_name="FlowCurve"),
        waterfall_curve=SimpleNamespace(),
    )
    curve = FakeObject(
        "FlowCurve",
        "CURVE",
        props={"waterfall_flow_curve": True},
        waterfall_emitter=SimpleNamespace(),
        waterfall_curve=SimpleNamespace(emitter_name="Emitter"),
    )
    objects = {"Emitter": emitter, "FlowCurve": curve}

    selected_emitter = resolve_emitter_curve_targets(emitter, objects)
    selected_curve = resolve_emitter_curve_targets(curve, objects)

    assert selected_emitter == (emitter, curve)
    assert selected_curve == (emitter, curve)


def test_resolve_emitter_curve_targets_rejects_non_empty_objects_as_emitters():
    non_emitter = FakeObject(
        "PreviewMesh",
        "MESH",
        waterfall_emitter=SimpleNamespace(flow_curve_name=""),
        waterfall_curve=SimpleNamespace(),
    )

    selected = resolve_emitter_curve_targets(non_emitter, {"PreviewMesh": non_emitter})

    assert selected == (None, None)


def test_resolve_emitter_curve_targets_ignores_non_tool_curve_name_collisions():
    emitter = FakeObject(
        "Emitter",
        "EMPTY",
        waterfall_emitter=SimpleNamespace(enabled=True, flow_curve_name="FlowCurve"),
        waterfall_curve=SimpleNamespace(),
    )
    unrelated = FakeObject(
        "FlowCurve",
        "CURVE",
        props={"waterfall_flow_curve": False},
        waterfall_emitter=SimpleNamespace(),
        waterfall_curve=SimpleNamespace(),
    )

    selected = resolve_emitter_curve_targets(emitter, {"Emitter": emitter, "FlowCurve": unrelated})

    assert selected == (emitter, None)


def test_set_preview_hidden_toggles_existing_preview_object_visibility():
    preview = FakeObject("FlowCurve_Preview", "MESH", props={"waterfall_generated": True})
    curve = FakeObject(
        "FlowCurve",
        "CURVE",
        props={"waterfall_flow_curve": True},
        waterfall_emitter=SimpleNamespace(),
        waterfall_curve=SimpleNamespace(preview_mesh_name="FlowCurve_Preview"),
    )
    objects = {"FlowCurve_Preview": preview}

    hidden_preview = set_preview_hidden(curve, objects, hidden=True)
    visible_preview = set_preview_hidden(curve, objects, hidden=False)

    assert hidden_preview is preview
    assert visible_preview is preview
    assert preview._hidden_calls == [True, False]
    assert preview.hide_viewport is False
    assert preview.hide_render is False


def test_set_preview_hidden_ignores_non_generated_preview_name_collisions():
    unrelated = FakeObject("FlowCurve_Preview", "MESH")
    curve = FakeObject(
        "FlowCurve",
        "CURVE",
        props={"waterfall_flow_curve": True},
        waterfall_emitter=SimpleNamespace(),
        waterfall_curve=SimpleNamespace(preview_mesh_name="FlowCurve_Preview"),
    )
    objects = {"FlowCurve_Preview": unrelated}

    result = set_preview_hidden(curve, objects, hidden=True)

    assert result is None
    assert unrelated._hidden_calls == []


def test_resolve_preview_parent_prefers_linked_emitter():
    emitter = FakeObject(
        "Emitter",
        "EMPTY",
        waterfall_emitter=SimpleNamespace(enabled=True, flow_curve_name="FlowCurve"),
        waterfall_curve=SimpleNamespace(),
    )
    curve = FakeObject(
        "FlowCurve",
        "CURVE",
        props={"waterfall_flow_curve": True},
        waterfall_emitter=SimpleNamespace(),
        waterfall_curve=SimpleNamespace(emitter_name="Emitter"),
    )

    parent = resolve_preview_parent(curve, {"Emitter": emitter})

    assert parent is emitter


def test_resolve_emitter_curve_targets_ignores_disabled_empty_objects():
    emitter = FakeObject(
        "Emitter",
        "EMPTY",
        waterfall_emitter=SimpleNamespace(enabled=False, flow_curve_name="FlowCurve"),
        waterfall_curve=SimpleNamespace(),
    )
    curve = FakeObject(
        "FlowCurve",
        "CURVE",
        props={"waterfall_flow_curve": True},
        waterfall_emitter=SimpleNamespace(),
        waterfall_curve=SimpleNamespace(emitter_name="Emitter"),
    )

    selected = resolve_emitter_curve_targets(emitter, {"Emitter": emitter, "FlowCurve": curve})

    assert selected == (None, None)


def test_apply_persistent_handler_uses_blender_persistent_decorator_when_available():
    seen = []

    def persistent(handler):
        seen.append(handler)

        def wrapped(*args, **kwargs):
            return handler(*args, **kwargs)

        wrapped._is_persistent = True
        return wrapped

    fake_bpy = SimpleNamespace(app=SimpleNamespace(handlers=SimpleNamespace(persistent=persistent)))

    def handler(_scene, _depsgraph):
        return "ok"

    decorated = apply_persistent_handler(handler, fake_bpy)

    assert seen == [handler]
    assert getattr(decorated, "_is_persistent", False) is True


def test_refresh_curve_preview_returns_none_and_hides_existing_preview_for_empty_mesh(monkeypatch):
    preview = FakeObject("FlowCurve_Preview", "MESH", props={"waterfall_generated": True})
    curve = FakeObject(
        "FlowCurve",
        "CURVE",
        props={"waterfall_flow_curve": True},
        waterfall_emitter=SimpleNamespace(),
        waterfall_curve=SimpleNamespace(
            preview_enabled=True,
            curve_mode="MANUAL_SHAPE",
            emitter_name="",
            preview_mesh_name="FlowCurve_Preview",
            baked_mesh_name="",
            width_density=1,
            longitudinal_step_length=0.5,
            curvature_min_angle_degrees=15.0,
            start_width=1.0,
            end_width=1.0,
            width_falloff=1.0,
            cross_angle=90.0,
            uv_base_speed=1.0,
        ),
    )

    fake_bpy = SimpleNamespace(data=SimpleNamespace(objects={"FlowCurve_Preview": preview}))
    monkeypatch.setattr(preview_ops, "bpy", fake_bpy)
    monkeypatch.setattr(preview_ops, "build_x_card_mesh", lambda _points, _settings: MeshData(vertices=[], faces=[]))
    monkeypatch.setattr(
        "waterfall_tool.adapters.blender_curve.read_flow_curve_points",
        lambda _curve: ([(0.0, 0.0, 0.0), (0.0, 0.0, -1.0)], [1.0, 1.0]),
    )
    monkeypatch.setattr(
        "waterfall_tool.adapters.blender_mesh.create_or_update_mesh_object",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("preview object should not be created for empty mesh")),
    )

    result = refresh_curve_preview(curve, context=types.SimpleNamespace())

    assert result is None
    assert preview._hidden_calls == [True]


def test_refresh_curve_preview_can_build_for_bake_while_preview_visibility_stays_hidden(monkeypatch):
    rebuilt_preview = FakeObject("FlowCurve_Preview", "MESH", props={"waterfall_generated": True})
    curve = FakeObject(
        "FlowCurve",
        "CURVE",
        props={"waterfall_flow_curve": True},
        waterfall_emitter=SimpleNamespace(),
        waterfall_curve=SimpleNamespace(
            preview_enabled=False,
            curve_mode="MANUAL_SHAPE",
            emitter_name="",
            preview_mesh_name="FlowCurve_Preview",
            baked_mesh_name="",
            width_density=1,
            longitudinal_step_length=0.5,
            curvature_min_angle_degrees=15.0,
            start_width=1.0,
            end_width=1.0,
            width_falloff=1.0,
            cross_angle=90.0,
            uv_base_speed=1.0,
        ),
    )

    fake_bpy = SimpleNamespace(data=SimpleNamespace(objects={"FlowCurve_Preview": rebuilt_preview}))
    monkeypatch.setattr(preview_ops, "bpy", fake_bpy)
    monkeypatch.setattr(preview_ops, "build_x_card_mesh", lambda _points, _settings: MeshData(vertices=[(0.0, 0.0, 0.0)], faces=[(0, 0, 0, 0)]))
    monkeypatch.setattr(
        "waterfall_tool.adapters.blender_curve.read_flow_curve_points",
        lambda _curve: ([(0.0, 0.0, 0.0), (0.0, 0.0, -1.0)], [1.0, 1.0]),
    )
    monkeypatch.setattr(
        "waterfall_tool.adapters.blender_mesh.create_or_update_mesh_object",
        lambda *_args, **_kwargs: rebuilt_preview,
    )

    result = refresh_curve_preview(
        curve,
        context=types.SimpleNamespace(),
        allow_when_preview_disabled=True,
        force_visible=False,
    )

    assert result is rebuilt_preview
    assert rebuilt_preview._hidden_calls == [True]


def test_should_refresh_curve_from_update_requires_geometry_change_on_tool_curve():
    update = SimpleNamespace(
        id=FakeObject("FlowCurve", "CURVE", props={"waterfall_flow_curve": True}),
        is_updated_geometry=True,
        is_updated_transform=False,
    )

    assert should_refresh_curve_from_update(update) is True


def test_should_refresh_curve_from_update_ignores_transform_only_updates():
    update = SimpleNamespace(
        id=FakeObject("FlowCurve", "CURVE", props={"waterfall_flow_curve": True}),
        is_updated_geometry=False,
        is_updated_transform=True,
    )

    assert should_refresh_curve_from_update(update) is False


def test_resolve_curves_from_update_ignores_transform_only_tool_curve_updates():
    curve = FakeObject(
        "FlowCurve",
        "CURVE",
        props={"waterfall_flow_curve": True},
        waterfall_emitter=SimpleNamespace(),
        waterfall_curve=SimpleNamespace(),
    )
    update = SimpleNamespace(
        id=curve,
        is_updated_geometry=False,
        is_updated_transform=True,
    )

    result = resolve_curves_from_update(update, {"FlowCurve": curve})

    assert result == []


def test_resolve_curves_from_update_maps_curve_datablock_geometry_back_to_tool_curve():
    curve_data = object()
    curve = FakeObject(
        "FlowCurve",
        "CURVE",
        props={"waterfall_flow_curve": True},
        waterfall_emitter=SimpleNamespace(),
        waterfall_curve=SimpleNamespace(),
    )
    curve.data = curve_data
    update = SimpleNamespace(
        id=curve_data,
        is_updated_geometry=True,
        is_updated_transform=False,
    )

    result = resolve_curves_from_update(update, {"FlowCurve": curve})

    assert result == [curve]


def test_bake_preview_mesh_copies_preview_world_transform_to_baked_object():
    class FakeMeshData:
        def copy(self):
            return FakeMeshData()

    class FakeBakedObject(FakeObject):
        def __init__(self, name: str, mesh_data):
            super().__init__(name, "MESH")
            self.data = mesh_data
            self.matrix_world = "IDENTITY"

        def __setitem__(self, key, value):
            self._props[key] = value

    class FakeDataObjects(dict):
        def new(self, name, mesh_data):
            baked = FakeBakedObject(name, mesh_data)
            self[baked.name] = baked
            return baked

    preview = FakeObject("FlowCurve_Preview", "MESH", props={"waterfall_generated": True})
    preview.data = FakeMeshData()
    preview.matrix_world = "WORLD_XFORM"
    curve = FakeObject(
        "FlowCurve",
        "CURVE",
        props={"waterfall_flow_curve": True},
        waterfall_emitter=SimpleNamespace(),
        waterfall_curve=SimpleNamespace(
            baked_mesh_name="",
            preview_enabled=True,
        ),
    )
    data_objects = FakeDataObjects()
    linked = []
    fake_bpy = SimpleNamespace(data=SimpleNamespace(objects=data_objects))
    context = SimpleNamespace(collection=SimpleNamespace(objects=SimpleNamespace(link=lambda obj: linked.append(obj))))

    baked = bake_ops.bake_preview_mesh_for_curve(
        curve,
        preview,
        context,
        fake_bpy,
        set_preview_hidden_fn=lambda *_args, **_kwargs: None,
    )

    assert baked is not None
    assert baked.matrix_world == "WORLD_XFORM"
