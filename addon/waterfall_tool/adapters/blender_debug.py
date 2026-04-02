from __future__ import annotations

import bpy


def ensure_preview_curves(context: bpy.types.Context, paths):
    existing = bpy.data.objects.get("WFT_PreviewPaths")
    if existing is not None:
        bpy.data.objects.remove(existing, do_unlink=True)

    curve = bpy.data.curves.new("WFT_PreviewPathsCurve", type="CURVE")
    curve.dimensions = "3D"

    for path in paths:
        spline = curve.splines.new("POLY")
        spline.points.add(len(path) - 1)
        for index, state in enumerate(path):
            spline.points[index].co = (*state.position, 1.0)

    obj = bpy.data.objects.new("WFT_PreviewPaths", curve)
    context.scene.collection.objects.link(obj)
    return obj
