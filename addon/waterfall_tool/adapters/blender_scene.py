from __future__ import annotations

from ..core.types import CollisionProvider, CollisionSample


class BlenderVisibleMeshCollisionProvider(CollisionProvider):
    def __init__(self, context, excluded_names: set[str] | None = None):
        self.context = context
        self.excluded_names = excluded_names or set()

    def _collision_objects(self):
        for obj in self.context.scene.objects:
            if obj.name in self.excluded_names:
                continue
            if obj.type != "MESH":
                continue
            if not obj.visible_get():
                continue
            if obj.get("waterfall_generated"):
                continue
            yield obj

    def sample(self, start, end):
        import mathutils

        direction = mathutils.Vector(end) - mathutils.Vector(start)
        distance = direction.length
        if distance <= 1.0e-8:
            return CollisionSample(hit=False)
        direction.normalize()
        depsgraph = self.context.evaluated_depsgraph_get()
        best_hit = None

        for obj in self._collision_objects():
            evaluated = obj.evaluated_get(depsgraph)
            local_start = evaluated.matrix_world.inverted() @ mathutils.Vector(start)
            local_direction = evaluated.matrix_world.to_3x3().inverted() @ direction
            hit, location, normal, _face_index = evaluated.ray_cast(local_start, local_direction, distance=distance)
            if not hit:
                continue
            world_location = evaluated.matrix_world @ location
            world_normal = (evaluated.matrix_world.to_3x3().inverted().transposed() @ normal).normalized()
            hit_distance = (world_location - mathutils.Vector(start)).length
            if best_hit is None or hit_distance < best_hit[0]:
                best_hit = (hit_distance, world_location, world_normal)

        if best_hit is None:
            return CollisionSample(hit=False)

        _distance, location, normal = best_hit
        support = max(0.0, min(1.0, normal.z))
        return CollisionSample(hit=True, point=tuple(location), normal=tuple(normal), support=support)
