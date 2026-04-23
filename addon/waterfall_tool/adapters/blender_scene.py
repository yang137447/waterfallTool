from __future__ import annotations

from ..core.types import CollisionProvider, CollisionSample

BACKFACE_CULL_EPSILON = 1.0e-8


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

        start_vector = mathutils.Vector(start)
        end_vector = mathutils.Vector(end)
        direction = end_vector - start_vector
        distance = direction.length
        if distance <= 1.0e-8:
            return CollisionSample(hit=False)
        direction.normalize()
        depsgraph = self.context.evaluated_depsgraph_get()
        best_hit = None

        for obj in self._collision_objects():
            evaluated = obj.evaluated_get(depsgraph)
            local_start = evaluated.matrix_world.inverted() @ start_vector
            local_end = evaluated.matrix_world.inverted() @ end_vector
            local_direction = evaluated.matrix_world.to_3x3().inverted() @ direction
            local_distance = (local_end - local_start).length
            hit, location, normal, _face_index = evaluated.ray_cast(
                local_start, local_direction, distance=local_distance
            )
            if not hit:
                continue
            world_location = evaluated.matrix_world @ location
            world_normal = (evaluated.matrix_world.to_3x3().inverted().transposed() @ normal).normalized()
            normal_facing = world_normal.x * direction.x + world_normal.y * direction.y + world_normal.z * direction.z
            if normal_facing > BACKFACE_CULL_EPSILON:
                # Ignore back-face hits; keep front-facing and near-parallel contacts.
                continue
            hit_distance = (world_location - start_vector).length
            if best_hit is None or hit_distance < best_hit[0]:
                best_hit = (hit_distance, world_location, world_normal)

        if best_hit is None:
            return CollisionSample(hit=False)

        _distance, location, normal = best_hit
        support = max(0.0, min(1.0, normal.z))
        return CollisionSample(hit=True, point=tuple(location), normal=tuple(normal), support=support)
