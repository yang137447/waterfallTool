from __future__ import annotations

import bpy
import mathutils

from ..adapters.blender_terrain import (
    COLLECTION_ROLE_GENERATED,
    COLLECTION_ROLE_KEY,
    GENERATED_TAG_KEY,
    GENERATED_TERRAIN_COLLECTION_NAME,
)
from ..terrain.emitters import choose_handoff_emitter_name
from ..terrain.types import SuggestedEmitter


def _iter_collection_tree(root: bpy.types.Collection) -> list[bpy.types.Collection]:
    stack = [root]
    seen: set[int] = set()
    ordered: list[bpy.types.Collection] = []
    while stack:
        col = stack.pop()
        try:
            ptr = col.as_pointer()
        except Exception:
            ptr = id(col)
        if ptr in seen:
            continue
        seen.add(ptr)
        ordered.append(col)
        stack.extend(list(col.children))
    return ordered


def _find_generated_collection(root: bpy.types.Collection) -> bpy.types.Collection | None:
    """Find the generated terrain collection (role-based first, name fallback).

    Terrain generation tags its collection with a role custom property; using that avoids global
    name-based assumptions and stays consistent across scenes/files.
    """
    tree = _iter_collection_tree(root)
    for col in tree:
        if col.get(COLLECTION_ROLE_KEY) == COLLECTION_ROLE_GENERATED:
            return col
    for col in tree:
        if col.name == GENERATED_TERRAIN_COLLECTION_NAME:
            return col
    return None


def _safe_int(value) -> int | None:
    try:
        return int(value)
    except Exception:
        return None


def _emitter_sort_key(obj: bpy.types.Object) -> tuple[int, str]:
    raw = obj.get("wft_emitter_index", None)
    parsed = _safe_int(raw)
    # Missing/malformed indexes sort after valid ones, but never throw before validation.
    return (parsed if parsed is not None else 10**9, obj.name or "")


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
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        scene = getattr(context, "scene", None)
        if scene is None or not hasattr(scene, "wft_settings"):
            return False
        generated_collection = _find_generated_collection(scene.collection)
        if generated_collection is None:
            return False
        tagged_objects = [obj for obj in generated_collection.objects if obj.get(GENERATED_TAG_KEY, False)]
        if not any(obj.name == "WFT_Terrain_MainTerrain" for obj in tagged_objects):
            return False
        if not any(
            obj.name.startswith("WFT_Terrain_SuggestedEmitter_") and obj.type == "CURVE"
            for obj in tagged_objects
        ):
            return False
        return True

    def execute(self, context):
        settings = context.scene.wft_settings
        scene = context.scene
        generated_collection = _find_generated_collection(scene.collection)
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
        for obj in sorted(emitter_objects, key=_emitter_sort_key):
            for required_key in ("wft_emitter_index", "wft_level_index", "wft_strength"):
                if required_key not in obj:
                    self.report(
                        {"ERROR"},
                        f"Generated terrain is missing emitter metadata ({obj.name}: {required_key}). Re-generate terrain.",
                    )
                    return {"CANCELLED"}

            try:
                # Validate metadata early; sorting must never be the first failure point.
                _ = int(obj["wft_emitter_index"])
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
