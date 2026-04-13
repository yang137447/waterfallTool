from __future__ import annotations

import types
from types import SimpleNamespace

from waterfall_tool.core.types import MeshData
from waterfall_tool.operators import preview as preview_ops
from waterfall_tool.operators.preview import (
    apply_persistent_handler,
    refresh_curve_preview,
    resolve_emitter_curve_targets,
    set_preview_hidden,
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


def test_resolve_emitter_curve_targets_handles_selected_emitter_or_curve():
    emitter = FakeObject(
        "Emitter",
        "EMPTY",
        waterfall_emitter=SimpleNamespace(flow_curve_name="FlowCurve"),
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


def test_set_preview_hidden_toggles_existing_preview_object_visibility():
    preview = FakeObject("FlowCurve_Preview", "MESH")
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
    preview = FakeObject("FlowCurve_Preview", "MESH")
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
            base_segment_density=1.0,
            curvature_refine_strength=1.0,
            start_width=1.0,
            end_width=1.0,
            width_falloff=1.0,
            cross_angle=90.0,
            uv_speed_scale=1.0,
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
