from __future__ import annotations

import bpy
import mathutils

from ..adapters.blender_terrain import (
    GENERATED_TAG_KEY,
    GENERATED_TERRAIN_COLLECTION_NAME,
)
from ..terrain.emitters import choose_handoff_emitter_name
from ..terrain.types import SuggestedEmitter


def _find_collection_recursive(
    root: bpy.types.Collection, name: str
) -> bpy.types.Collection | None:
    stack = [root]
    seen: set[int] = set()
    while stack:
        collection = stack.pop()
        if id(collection) in seen:
            continue
        seen.add(id(collection))
        if collection.name == name:
            return collection
        stack.extend(list(collection.children))
    return None


def _read_curve_world_points(obj: bpy.types.Object) -> list[tuple[float, float, float]]:
    data = getattr(obj, "data", None)
    if data is None or not getattr(data, "splines", None):
        raise ValueError(f"{obj.name}: curve has no splines")
    if len(data.splines) < 1:
        raise ValueError(f"{obj.name}: curve has no splines")

    spline = data.splines[0]
    matrix = obj.matrix_world
    points: list[tuple[float, float, float]] = []

    if getattr(spline, "type", None) == "BEZIER":
        raw_points = getattr(spline, "bezier_points", None) or []
        for point in raw_points:
            points.append(tuple(matrix @ mathutils.Vector(point.co[:3])))
    else:
        raw_points = getattr(spline, "points", None) or []
        for point in raw_points:
            points.append(tuple(matrix @ mathutils.Vector(point.co[:3])))

    if len(points) < 2:
        raise ValueError(f"{obj.name}: expected at least 2 curve points, got {len(points)}")
    return points


class WFT_OT_UseGeneratedTerrainForWaterfall(bpy.types.Operator):
    bl_idname = "wft.use_generated_terrain_for_waterfall"
    bl_label = "Use Terrain For Waterfall"

    def execute(self, context):
        settings = context.scene.wft_settings
        scene = context.scene
        generated_collection = _find_collection_recursive(scene.collection, GENERATED_TERRAIN_COLLECTION_NAME)
        if generated_collection is None:
            self.report({"ERROR"}, "Generate terrain before handoff")
            return {"CANCELLED"}

        tagged_objects = {obj.name: obj for obj in generated_collection.objects if obj.get(GENERATED_TAG_KEY, False)}
        terrain = tagged_objects.get("WFT_Terrain_MainTerrain")
        if terrain is None:
            self.report({"ERROR"}, "Generate terrain before handoff")
            return {"CANCELLED"}

        emitter_objects = [
            obj
            for obj in tagged_objects.values()
            if obj.name.startswith("WFT_Terrain_SuggestedEmitter_") and obj.type == "CURVE"
        ]
        if not emitter_objects:
            self.report({"ERROR"}, "Generate terrain before handoff")
            return {"CANCELLED"}

        emitters: list[SuggestedEmitter] = []
        object_names: list[str] = []
        for obj in sorted(emitter_objects, key=lambda item: int(item.get("wft_emitter_index", -1))):
            for required_key in ("wft_emitter_index", "wft_level_index", "wft_strength"):
                if required_key not in obj:
                    self.report(
                        {"ERROR"},
                        f"Generated terrain is missing emitter metadata ({obj.name}: {required_key}). Re-generate terrain.",
                    )
                    return {"CANCELLED"}

            try:
                points = _read_curve_world_points(obj)
                level_index = int(obj["wft_level_index"])
                strength = float(obj["wft_strength"])
            except Exception as exc:
                self.report({"ERROR"}, f"Invalid generated emitter data ({obj.name}): {exc}")
                return {"CANCELLED"}

            emitters.append(
                SuggestedEmitter(
                    level_index=level_index,
                    points=points,
                    strength=strength,
                    enabled=True,
                )
            )
            object_names.append(obj.name)

        try:
            chosen_name = choose_handoff_emitter_name(object_names, emitters)
        except Exception as exc:
            self.report({"ERROR"}, f"Could not choose terrain emitter: {exc}")
            return {"CANCELLED"}

        emitter = tagged_objects.get(chosen_name)
        if emitter is None:
            self.report({"ERROR"}, "Generated terrain emitter was not found for handoff")
            return {"CANCELLED"}

        settings.emitter_object = emitter
        settings.collider_object = terrain
        return {"FINISHED"}
