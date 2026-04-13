from __future__ import annotations

from typing import Any

try:
    import bpy
except ModuleNotFoundError:  # pragma: no cover - executed outside Blender.
    bpy = None


def _safe_operator_call(operator_id: str, context: Any) -> None:
    if bpy is None:
        return

    ops_root, _, op_name = operator_id.partition(".")
    if not ops_root or not op_name:
        return

    ops_namespace = getattr(bpy.ops, ops_root, None)
    operator = getattr(ops_namespace, op_name, None)
    if operator is None:
        return

    try:
        operator("INVOKE_DEFAULT")
    except TypeError:
        operator()
    except RuntimeError:
        return


def _refresh_from_emitter(self: Any, context: Any) -> None:
    del self
    _safe_operator_call("waterfall.rebuild_preview", context)


def _refresh_from_curve(self: Any, context: Any) -> None:
    del self
    _safe_operator_call("waterfall.simulate_curve", context)


if bpy is not None:

    class WaterfallEmitterSettings(bpy.types.PropertyGroup):
        auto_refresh: bpy.props.BoolProperty(
            name="Auto Refresh",
            default=True,
            update=_refresh_from_emitter,
        )

    class WaterfallCurveSettings(bpy.types.PropertyGroup):
        auto_simulate: bpy.props.BoolProperty(
            name="Auto Simulate",
            default=True,
            update=_refresh_from_curve,
        )

else:

    class WaterfallEmitterSettings:
        pass

    class WaterfallCurveSettings:
        pass
