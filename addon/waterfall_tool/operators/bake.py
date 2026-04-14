from __future__ import annotations

try:
    import bpy
except ModuleNotFoundError:
    bpy = None

from ..operators.preview import refresh_curve_preview, resolve_emitter_curve_targets, set_preview_hidden


def bake_preview_mesh_for_curve(curve, preview, context, bpy_module, *, set_preview_hidden_fn):
    mesh_copy = preview.data.copy()
    baked = bpy_module.data.objects.new(f"{curve.name}_Baked", mesh_copy)
    context.collection.objects.link(baked)
    baked.matrix_world = preview.matrix_world
    baked["waterfall_generated"] = True
    curve.waterfall_curve.baked_mesh_name = baked.name
    curve.waterfall_curve.preview_enabled = False
    set_preview_hidden_fn(curve, bpy_module.data.objects, hidden=True)
    return baked


if bpy is not None:

    class WATERFALL_OT_bake_mesh(bpy.types.Operator):
        bl_idname = "waterfall.bake_mesh"
        bl_label = "Bake Mesh"
        bl_options = {"REGISTER", "UNDO"}

        def execute(self, context):
            _emitter, curve = resolve_emitter_curve_targets(context.object, bpy.data.objects)
            if curve is None or curve.type != "CURVE":
                self.report({"ERROR"}, "Select a flow curve before baking")
                return {"CANCELLED"}

            preview = refresh_curve_preview(
                curve,
                context,
                allow_when_preview_disabled=True,
                force_visible=False,
            )
            if preview is None:
                self.report({"ERROR"}, "Preview is disabled or empty")
                return {"CANCELLED"}

            bake_preview_mesh_for_curve(
                curve,
                preview,
                context,
                bpy,
                set_preview_hidden_fn=set_preview_hidden,
            )
            return {"FINISHED"}

else:

    class WATERFALL_OT_bake_mesh:
        pass
