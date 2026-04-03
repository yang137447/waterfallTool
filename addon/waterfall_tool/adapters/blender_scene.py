from __future__ import annotations

import bpy
import mathutils

from ..core.emitter_sampling import sample_polyline_evenly
from ..core.types import CollisionSample


def sample_emitter_points(emitter_object: bpy.types.Object, count: int):
    if emitter_object is None or emitter_object.type != "CURVE":
        return []

    spline = emitter_object.data.splines[0]
    if spline.type == "BEZIER":
        points = [emitter_object.matrix_world @ point.co for point in spline.bezier_points]
    else:
        points = [emitter_object.matrix_world @ mathutils.Vector(point.co[:3]) for point in spline.points]

    if not points:
        return []

    point_tuples = tuple(tuple(point) for point in points)
    return sample_polyline_evenly(point_tuples, count)


class BlenderCollider:
    def __init__(self, collider_object: bpy.types.Object):
        self.collider_object = collider_object

    def sample(self, position, velocity) -> CollisionSample:
        if self.collider_object is None or self.collider_object.type != "MESH":
            return CollisionSample(
                hit=False,
                normal=(0.0, 1.0, 0.0),
                tangent=(velocity[0], velocity[1], velocity[2]),
                support=0.0,
                obstacle=0.0,
            )

        world_position = mathutils.Vector(position)
        local_position = self.collider_object.matrix_world.inverted() @ world_position
        hit, location, normal, _face_index = self.collider_object.closest_point_on_mesh(local_position)

        if not hit:
            return CollisionSample(
                hit=False,
                normal=(0.0, 1.0, 0.0),
                tangent=(velocity[0], velocity[1], velocity[2]),
                support=0.0,
                obstacle=0.0,
            )

        world_normal = (self.collider_object.matrix_world.to_3x3() @ normal).normalized()
        velocity_vector = mathutils.Vector(velocity)
        tangent_vector = velocity_vector - world_normal * velocity_vector.dot(world_normal)
        if tangent_vector.length == 0.0:
            tangent_vector = mathutils.Vector((0.25, 0.0, -0.5))
        else:
            tangent_vector.normalize()

        distance = (local_position - location).length
        support = max(0.0, min(1.0, 1.0 - distance))
        obstacle = max(0.0, min(1.0, abs(world_normal.x)))

        return CollisionSample(
            hit=True,
            normal=(world_normal.x, world_normal.y, world_normal.z),
            tangent=(tangent_vector.x, tangent_vector.y, tangent_vector.z),
            support=support,
            obstacle=obstacle,
        )


def sample_control_influences(position, split_guide_object, breakup_region_object):
    _ = position
    control_sample = {"split_boost": 0.0, "breakup_boost": 0.0}
    if split_guide_object is not None:
        control_sample["split_boost"] = 0.2
    if breakup_region_object is not None:
        control_sample["breakup_boost"] = 0.5
    return control_sample
