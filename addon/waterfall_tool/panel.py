from __future__ import annotations

try:
    import bpy
except ModuleNotFoundError:
    bpy = None


if bpy is not None:

    def _draw_foldout(layout, data, prop_name: str, label: str):
        row = layout.row()
        is_open = bool(getattr(data, prop_name))
        icon = "TRIA_DOWN" if is_open else "TRIA_RIGHT"
        row.prop(data, prop_name, text=label, emboss=False, icon=icon)
        return is_open

    class WATERFALL_PT_curve_card_panel(bpy.types.Panel):
        bl_label = "Waterfall Curve Cards"
        bl_idname = "WATERFALL_PT_curve_card_panel"
        bl_space_type = "VIEW_3D"
        bl_region_type = "UI"
        bl_category = "Waterfall"

        def draw(self, context):
            from .operators.preview import resolve_emitter_curve_targets

            layout = self.layout
            global_settings = getattr(context.scene, "waterfall_global", None)
            obj = context.object
            if obj is None:
                layout.label(text="Select an emitter or flow curve")

            if global_settings is not None:
                global_box = layout.box()
                if _draw_foldout(global_box, global_settings, "ui_global_properties_open", "Global Properties"):
                    if _draw_foldout(global_box, global_settings, "ui_global_simulation_open", "Global Simulation"):
                        global_sim = global_box.box()
                        global_sim.prop(global_settings, "gravity")
                        global_sim.prop(global_settings, "drag")
                        global_sim.prop(global_settings, "simulation_step_count")
                        global_sim.prop(global_settings, "simulation_time_step")
                        global_sim.prop(global_settings, "attach_strength")
                        global_sim.prop(global_settings, "detach_threshold")
                        global_sim.prop(global_settings, "surface_offset")

                    if _draw_foldout(global_box, global_settings, "ui_global_termination_open", "Termination"):
                        global_termination = global_box.box()
                        global_termination.prop(global_settings, "terminal_speed")
                        global_termination.prop(global_settings, "cutoff_height")

                    if _draw_foldout(global_box, global_settings, "ui_global_cutoff_guide_open", "Cutoff Guide"):
                        guide_box = global_box.box()
                        guide_box.prop(global_settings, "show_cutoff_guide")
                        if global_settings.show_cutoff_guide:
                            offset_row = guide_box.row(align=True)
                            offset_row.prop(global_settings, "cutoff_offset_x")
                            offset_row.prop(global_settings, "cutoff_offset_y")
                            size_row = guide_box.row(align=True)
                            size_row.prop(global_settings, "cutoff_size_x")
                            size_row.prop(global_settings, "cutoff_size_y")

            if obj is None:
                return

            emitter_setup = None
            if getattr(obj, "type", None) == "EMPTY":
                emitter_setup = getattr(obj, "waterfall_emitter", None)

            if emitter_setup is not None:
                setup = layout.box()
                if _draw_foldout(setup, global_settings, "ui_object_properties_open", "Object Properties"):
                    emitter_box = setup.box()
                    if _draw_foldout(emitter_box, global_settings, "ui_object_emitter_open", "Emitter"):
                        inner = emitter_box.box()
                        inner.prop(emitter_setup, "enabled", text="Use As Waterfall Emitter")

            emitter_obj, curve_obj = resolve_emitter_curve_targets(obj, bpy.data.objects)
            emitter = getattr(emitter_obj, "waterfall_emitter", None)
            curve = getattr(curve_obj, "waterfall_curve", None)

            if emitter_setup is not None and not getattr(emitter_setup, "enabled", False):
                layout.label(text="Enable this Empty to use independent emitter settings")
                return

            if emitter is not None:
                simulation = layout.box()
                if _draw_foldout(simulation, global_settings, "ui_object_emission_open", "Emission"):
                    inner = simulation.box()
                    inner.prop(emitter, "speed")
                    inner.prop(emitter, "direction_axis")
                    inner.operator("waterfall.simulate_curve")

            if curve is None:
                layout.label(text="Generate or select a linked flow curve")
                return

            preview = layout.box()
            if _draw_foldout(preview, global_settings, "ui_object_mesh_preview_open", "Mesh Preview"):
                preview_body = preview.box()
                preview_body.prop(curve, "curve_mode")
                preview_body.prop(curve, "preview_enabled")

                if _draw_foldout(preview_body, global_settings, "ui_object_density_open", "Density"):
                    density = preview_body.box()
                    density.prop(curve, "width_density")
                    density.prop(curve, "longitudinal_step_length")
                    density.prop(curve, "curvature_min_angle_degrees", text="Curvature Min Angle")

                if _draw_foldout(preview_body, global_settings, "ui_object_shape_open", "Shape"):
                    shape = preview_body.box()
                    shape.prop(curve, "base_width", text="Base Width")
                    shape.prop(curve, "speed_expansion", text="Speed Expansion")
                    shape.prop(curve, "start_width", text="Start Width")
                    shape.prop(curve, "end_width", text="End Width")
                    shape.prop(curve, "width_falloff", text="Falloff")
                    shape.prop(curve, "enable_cross_strip")
                    shape.prop(curve, "cross_angle")
                    shape.prop(curve, "cross_width_scale")

                if _draw_foldout(preview_body, global_settings, "ui_object_uv_open", "UV"):
                    uv = preview_body.box()
                    uv.prop(curve, "uv_base_speed")
                    uv.prop(curve, "uv_speed_smoothing_length")

                rebuild_text = "Rebuild Preview" if curve.preview_enabled else "Build Hidden Preview"
                preview_body.operator("waterfall.rebuild_preview", text=rebuild_text)

            bake = layout.box()
            if _draw_foldout(bake, global_settings, "ui_object_bake_open", "Bake"):
                bake.box().operator("waterfall.bake_mesh")

else:

    class WATERFALL_PT_curve_card_panel:
        pass
