from __future__ import annotations

from math import sqrt

from .types import Vector3

EPSILON = 1.0e-8


def add(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def scale(v: Vector3, scalar: float) -> Vector3:
    return (v[0] * scalar, v[1] * scalar, v[2] * scalar)


def dot(a: Vector3, b: Vector3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vector3, b: Vector3) -> Vector3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def length(v: Vector3) -> float:
    return sqrt(dot(v, v))


def normalize(v: Vector3) -> Vector3:
    size = length(v)
    if size <= EPSILON:
        return (0.0, 0.0, 0.0)
    return scale(v, 1.0 / size)


def project_on_plane(v: Vector3, normal: Vector3) -> Vector3:
    unit_normal = normalize(normal)
    return sub(v, scale(unit_normal, dot(v, unit_normal)))


def lerp(a: Vector3, b: Vector3, t: float) -> Vector3:
    return (
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
        a[2] + (b[2] - a[2]) * t,
    )
