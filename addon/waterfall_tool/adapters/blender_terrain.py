from __future__ import annotations

from typing import Any

import bpy
import mathutils

from ..terrain.blueprint import build_terrace_levels
from ..terrain.emitters import build_suggested_emitters
from ..terrain.layout import build_blocker_masses, build_gap_segments, build_lip_curves
from ..terrain.mesh import build_main_terrain_mesh
from ..terrain.overrides import apply_lip_overrides
from ..terrain.types import LipCurveDraft, TerrainBlueprint

DEFAULT_WIDTH_DECAY = 0.1
DEFAULT_DEPTH_DECAY = 0.12
DEFAULT_LIP_ROUNDNESS = 0.4
DEFAULT_GAP_FREQUENCY = 0.25
DEFAULT_BLOCKER_DENSITY = 0.3
DEFAULT_SEED = 7

GENERATED_TERRAIN_COLLECTION_NAME = "WFT_Terrain_Generated"
TEMP_COLLECTION_NAME = "WFT_Terrain_Generated__temp"
GENERATED_TAG_KEY = "wft_generated_terrain"


def read_axis_points(axis_object: bpy.types.Object) -> list[tuple[float, float, float]]:
    if axis_object is None:
        raise ValueError("Terrain axis object is not set")
    if axis_object.type != "CURVE":
        raise ValueError(f"Terrain axis object must be a Curve, got: {axis_object.type}")
    if axis_object.data is None or not getattr(axis_object.data, "splines", None):
        raise ValueError("Terrain axis curve has no splines")
    if len(axis_object.data.splines) < 1:
        raise ValueError("Terrain axis curve must have at least one spline")

    spline = axis_object.data.splines[0]
    spline_type = getattr(spline, "type", None)
    if spline_type == "BEZIER":
        if not getattr(spline, "bezier_points", None) or len(spline.bezier_points) < 2:
            raise ValueError("Terrain axis Bezier spline must have at least 2 bezier points")
        points = [mathutils.Vector(point.co[:3]) for point in spline.bezier_points]
    elif spline_type in {"POLY", "NURBS"}:
        if not getattr(spline, "points", None) or len(spline.points) < 2:
            raise ValueError(f"Terrain axis {spline_type} spline must have at least 2 points")
        points = [mathutils.Vector(point.co[:3]) for point in spline.points]
    else:
        raise ValueError(f"Unsupported terrain axis spline type: {spline_type!r} (use Poly, Nurbs, or Bezier)")

    return [tuple(axis_object.matrix_world @ point) for point in points]


def _ensure_collection(scene: bpy.types.Scene, name: str) -> bpy.types.Collection:
    existing = bpy.data.collections.get(name)
    if existing is None:
        existing = bpy.data.collections.new(name)
    if existing.name not in {child.name for child in scene.collection.children}:
        scene.collection.children.link(existing)
    return existing


def _remove_collection_if_present(scene: bpy.types.Scene, name: str) -> None:
    col = bpy.data.collections.get(name)
    if col is None:
        return
    for child in list(scene.collection.children):
        if child == col:
            scene.collection.children.unlink(col)
            break
    bpy.data.collections.remove(col)


DEFAULT_OVERRIDE_CONTINUITY_SEGMENTS = ((0.0, 1.0),)  # Overrides reuse the generator’s full continuity span so manual edits stay compatible with generated lips.


def _level_index_from_float(value: float) -> int | None:
    if not value.is_integer():
        return None
    level_index = int(value)
    return level_index if level_index >= 0 else None


def _parse_level_index(raw_value: Any) -> int | None:
    if raw_value is None:
        return None
    if isinstance(raw_value, int):
        return raw_value if raw_value >= 0 else None
    if isinstance(raw_value, float):
        return _level_index_from_float(raw_value)
    if isinstance(raw_value, str):
        candidate = raw_value.strip()
        if not candidate:
            return None
        try:
            level_index = int(candidate)
        except ValueError:
            return None
        return level_index if level_index >= 0 else None
    return None


def read_lip_overrides(collection: bpy.types.Collection | None) -> dict[int, LipCurveDraft]:
    """Read curve overrides deterministically, reusing the full continuity range so generated lips stay compatible."""
    if collection is None:
        return {}

    overrides: dict[int, LipCurveDraft] = {}
    # Sorting by name makes duplicate `level_index` overrides deterministic (later names override earlier ones).
    for obj in sorted(collection.objects, key=lambda item: item.name or ""):
        if obj.type != "CURVE":
            continue

        level_index = _parse_level_index(obj.get("wft_level_index"))
        if level_index is None:
            continue

        data = getattr(obj, "data", None)
        if data is None or not getattr(data, "splines", None):
            continue

        spline = data.splines[0]
        raw_points = getattr(spline, "bezier_points", None)
        if raw_points is None:
            raw_points = getattr(spline, "points", None)
        if not raw_points:
            continue

        matrix = obj.matrix_world
        points = tuple(tuple(matrix @ mathutils.Vector(point.co[:3])) for point in raw_points)

        overrides[level_index] = LipCurveDraft(
            level_index=level_index,
            points=points,
            continuity_segments=DEFAULT_OVERRIDE_CONTINUITY_SEGMENTS,
            overridden=True,
        )

    return overrides


def _delete_generated_outputs(outputs: list[bpy.types.Object]) -> None:
    for obj in list(outputs):
        if not obj.get(GENERATED_TAG_KEY, False):
            continue

        data = getattr(obj, "data", None)
        bpy.data.objects.remove(obj, do_unlink=True)
        if data is None:
            continue
        try:
            if hasattr(data, "users") and data.users == 0:
                if isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)
                elif isinstance(data, bpy.types.Curve):
                    bpy.data.curves.remove(data)
        except ReferenceError:
            pass


def _preflight_reserved_names(
    *,
    generated_collection: bpy.types.Collection,
    old_outputs: list[bpy.types.Object],
    reserved_object_names: list[str],
) -> None:
    # Ensure we never silently promote into ".001" names due to collisions.
    old_output_ids = {obj.as_pointer() for obj in old_outputs}
    for name in reserved_object_names:
        existing = bpy.data.objects.get(name)
        if existing is None:
            continue
        if existing.as_pointer() in old_output_ids:
            continue
        if existing.get(GENERATED_TAG_KEY, False):
            raise ValueError(
                f"Name collision: found generated-tagged object '{name}' outside "
                f"the '{GENERATED_TERRAIN_COLLECTION_NAME}' collection"
            )
        in_generated_collection = any(obj.as_pointer() == existing.as_pointer() for obj in generated_collection.objects)
        location = f"in collection '{generated_collection.name}'" if in_generated_collection else "in the scene"
        raise ValueError(
            f"Name collision: object '{name}' already exists ({location}) and is not generated by WFT terrain. "
            "Rename or remove it before generating."
        )


def _rename_or_fail(obj: bpy.types.Object, desired_name: str) -> None:
    obj.name = desired_name
    if obj.name != desired_name:
        raise RuntimeError(f"Failed to promote object name to '{desired_name}' (got '{obj.name}')")


def _rename_data_or_fail(data, desired_name: str) -> None:
    data.name = desired_name
    if data.name != desired_name:
        raise RuntimeError(f"Failed to promote datablock name to '{desired_name}' (got '{data.name}')")


def _backup_rename_outputs(outputs: list[bpy.types.Object]) -> list[tuple[bpy.types.Object, str, str | None]]:
    renamed: list[tuple[bpy.types.Object, str, str | None]] = []
    for obj in outputs:
        old_name = obj.name
        old_data_name = getattr(getattr(obj, "data", None), "name", None)

        # Choose a unique backup name to avoid collisions.
        suffix = 0
        while True:
            candidate = f"{old_name}__OLD__{suffix:02d}"
            if bpy.data.objects.get(candidate) is None:
                break
            suffix += 1
        obj.name = candidate

        if getattr(obj, "data", None) is not None and old_data_name is not None:
            data = obj.data
            data_suffix = 0
            while True:
                data_candidate = f"{old_data_name}__OLD__{data_suffix:02d}"
                # Curves and meshes live in separate name spaces; only check the relevant datablock type.
                if isinstance(data, bpy.types.Mesh):
                    exists = bpy.data.meshes.get(data_candidate) is not None
                elif isinstance(data, bpy.types.Curve):
                    exists = bpy.data.curves.get(data_candidate) is not None
                else:
                    exists = False
                if not exists:
                    break
                data_suffix += 1
            data.name = data_candidate

        renamed.append((obj, old_name, old_data_name))
    return renamed


def _restore_output_names(renamed: list[tuple[bpy.types.Object, str, str | None]]) -> None:
    for obj, original_name, original_data_name in renamed:
        try:
            obj.name = original_name
            if getattr(obj, "data", None) is not None and original_data_name is not None:
                obj.data.name = original_data_name
        except ReferenceError:
            # Object/data may have been removed elsewhere; ignore.
            pass


def build_blueprint_from_scene(settings) -> TerrainBlueprint:
    axis_points = read_axis_points(settings.terrain_axis_object)
    top_elevation = max(point[2] for point in axis_points)
    return TerrainBlueprint(
        axis_points=axis_points,
        level_count=settings.terrain_level_count,
        top_elevation=top_elevation,
        total_drop=settings.terrain_total_drop,
        base_width=settings.terrain_base_width,
        terrace_depth=settings.terrain_depth,
        width_decay=DEFAULT_WIDTH_DECAY,
        depth_decay=DEFAULT_DEPTH_DECAY,
        lip_roundness=DEFAULT_LIP_ROUNDNESS,
        gap_frequency=DEFAULT_GAP_FREQUENCY,
        blocker_density=DEFAULT_BLOCKER_DENSITY,
        seed=DEFAULT_SEED,
    )


def create_terrain_objects(context: bpy.types.Context, settings) -> None:
    # Build and validate first (pure Python pipeline + axis validation). Only replace outputs if
    # replacement objects are created successfully.
    blueprint = build_blueprint_from_scene(settings)
    levels = build_terrace_levels(blueprint)
    lips = build_lip_curves(levels, blueprint)
    overrides = read_lip_overrides(settings.terrain_override_collection)
    lips = apply_lip_overrides(lips, overrides)
    gaps = build_gap_segments(lips, blueprint)
    blockers = build_blocker_masses(levels, lips, gaps, blueprint)
    mesh_payload = build_main_terrain_mesh(levels, lips, blockers)
    emitters = build_suggested_emitters(lips, gaps)

    scene = context.scene
    generated_collection = _ensure_collection(scene, GENERATED_TERRAIN_COLLECTION_NAME)
    old_outputs = [obj for obj in list(generated_collection.objects) if obj.get(GENERATED_TAG_KEY, False)]

    # Clean up any prior temp collection up front (safe: it's not part of approved outputs).
    _remove_collection_if_present(scene, TEMP_COLLECTION_NAME)
    temp_collection = _ensure_collection(scene, TEMP_COLLECTION_NAME)

    try:
        mesh = bpy.data.meshes.new("WFT_Terrain__TMP_MainTerrainMesh")
        mesh.from_pydata(mesh_payload.vertices, [], mesh_payload.faces)
        mesh.update()
        terrain_object = bpy.data.objects.new("WFT_Terrain__TMP_MainTerrain", mesh)
        terrain_object[GENERATED_TAG_KEY] = True
        temp_collection.objects.link(terrain_object)

        for index, emitter in enumerate(emitters):
            curve_data = bpy.data.curves.new(f"WFT_Terrain__TMP_SuggestedEmitterCurve_{index:02d}", type="CURVE")
            curve_data.dimensions = "3D"
            spline = curve_data.splines.new("POLY")
            spline.points.add(len(emitter.points) - 1)
            for point_index, point in enumerate(emitter.points):
                spline.points[point_index].co = (*point, 1.0)
            emitter_object = bpy.data.objects.new(f"WFT_Terrain__TMP_SuggestedEmitter_{index:02d}", curve_data)
            emitter_object[GENERATED_TAG_KEY] = True
            # Persist minimal chooser metadata so handoff can select without re-running the terrain pipeline.
            emitter_object["wft_emitter_index"] = index
            emitter_object["wft_level_index"] = emitter.level_index
            emitter_object["wft_strength"] = float(emitter.strength)
            temp_collection.objects.link(emitter_object)

        reserved_object_names = ["WFT_Terrain_MainTerrain"] + [
            f"WFT_Terrain_SuggestedEmitter_{index:02d}" for index in range(len(emitters))
        ]
        _preflight_reserved_names(
            generated_collection=generated_collection,
            old_outputs=old_outputs,
            reserved_object_names=reserved_object_names,
        )

        # Replace outputs transactionally:
        # 1) stage new objects (link + rename) while keeping old outputs intact (but renamed aside)
        # 2) only delete the old tagged outputs after the new ones have their final names and are linked
        backup_map: list[tuple[bpy.types.Object, str, str | None]] = []
        promoted_objects: list[bpy.types.Object] = []

        try:
            backup_map = _backup_rename_outputs(old_outputs)

            for obj in list(temp_collection.objects):
                generated_collection.objects.link(obj)
                promoted_objects.append(obj)

                if obj.name == "WFT_Terrain__TMP_MainTerrain":
                    _rename_or_fail(obj, "WFT_Terrain_MainTerrain")
                    if obj.data is not None:
                        _rename_data_or_fail(obj.data, "WFT_Terrain_MainTerrainMesh")
                elif obj.name.startswith("WFT_Terrain__TMP_SuggestedEmitter_"):
                    desired_name = obj.name.replace(
                        "WFT_Terrain__TMP_SuggestedEmitter_",
                        "WFT_Terrain_SuggestedEmitter_",
                    )
                    _rename_or_fail(obj, desired_name)
                    if obj.data is not None:
                        desired_curve_name = obj.data.name.replace(
                            "WFT_Terrain__TMP_SuggestedEmitterCurve_",
                            "WFT_Terrain_SuggestedEmitterCurve_",
                        )
                        _rename_data_or_fail(obj.data, desired_curve_name)

            for obj in list(temp_collection.objects):
                temp_collection.objects.unlink(obj)

        except Exception:
            # Best-effort rollback: unlink any staged temp objects, delete them, and restore old names.
            for obj in promoted_objects:
                try:
                    generated_collection.objects.unlink(obj)
                except Exception:
                    pass
            _delete_generated_outputs(promoted_objects)
            _restore_output_names(backup_map)
            raise

        # Now it is safe to delete the old outputs (they are no longer needed and the new outputs are in place).
        _delete_generated_outputs(old_outputs)

    except Exception:
        # Ensure temp staging objects are removed even if we fail before promotion starts.
        leftovers = [obj for obj in list(temp_collection.objects) if obj.get(GENERATED_TAG_KEY, False)]
        _delete_generated_outputs(leftovers)
        raise

    finally:
        # Ensure the temp staging collection is always cleaned up.
        _remove_collection_if_present(scene, TEMP_COLLECTION_NAME)
