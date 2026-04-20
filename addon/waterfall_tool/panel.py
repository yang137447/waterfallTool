from __future__ import annotations

try:
    import bpy
except ModuleNotFoundError:
    bpy = None


if bpy is not None:

    class WATERFALL_PT_curve_card_panel(bpy.types.Panel):
        bl_label = "Waterfall Curve Cards"
        bl_idname = "WATERFALL_PT_curve_card_panel"
        bl_space_type = "VIEW_3D"
        bl_region_type = "UI"
        bl_category = "Waterfall"

        def draw(self, context):
            from .operators.preview import resolve_emitter_curve_targets

            layout = self.layout
            obj = context.object
            if obj is None:
                layout.label(text="Select an emitter or flow curve")
                return

            emitter_obj, curve_obj = resolve_emitter_curve_targets(obj, bpy.data.objects)
            emitter = getattr(emitter_obj, "waterfall_emitter", None)
            curve = getattr(curve_obj, "waterfall_curve", None)

            if emitter is not None:
                simulation = layout.box()
                simulation.label(text="Simulation")
                simulation.prop(emitter, "speed")
                simulation.prop(emitter, "direction_axis")
                simulation.prop(emitter, "gravity")
                simulation.prop(emitter, "drag")
                simulation.prop(emitter, "simulation_step_count")
                simulation.prop(emitter, "simulation_time_step")
                simulation.prop(emitter, "attach_strength")
                simulation.prop(emitter, "detach_threshold")
                simulation.operator("waterfall.simulate_curve")

            if curve is None:
                layout.label(text="Generate or select a linked flow curve")
                return

            curve_box = layout.box()
            curve_box.label(text="Curve Mode")
            curve_box.prop(curve, "curve_mode")

            preview = layout.box()
            preview.label(text="Mesh Preview")
            preview.prop(curve, "preview_enabled")

            density = preview.box()
            density.label(text="Density")
            density.prop(curve, "base_segment_density", text="Base Density")
            density.prop(curve, "curvature_refine_strength", text="Curvature Influence")
            density.prop(curve, "curvature_density_max_multiplier", text="Curvature Max Multiplier")
            density.prop(curve, "target_face_count", text="Target Faces (0=Auto)")
            density.prop(curve, "max_segment_count", text="Max Segments (0=Auto)")

            shape = preview.box()
            shape.label(text="Shape")
            shape.prop(curve, "start_width")
            shape.prop(curve, "end_width")
            shape.prop(curve, "width_falloff")
            shape.prop(curve, "cross_angle")

            uv = preview.box()
            uv.label(text="UV")
            uv.prop(curve, "uv_speed_scale")
            preview.operator("waterfall.rebuild_preview")

            bake = layout.box()
            bake.label(text="Bake")
            bake.operator("waterfall.bake_mesh")

else:

    class WATERFALL_PT_curve_card_panel:
        pass
