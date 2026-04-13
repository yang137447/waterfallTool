from __future__ import annotations

from types import SimpleNamespace

from waterfall_tool.operators.preview import resolve_emitter_curve_targets, set_preview_hidden


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
