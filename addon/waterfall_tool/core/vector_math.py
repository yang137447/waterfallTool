from __future__ import annotations

import math

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
    return math.sqrt(dot(v, v))


def normalize(v: Vector3) -> Vector3:
    size = length(v)
    if size <= EPSILON:
        return (0.0, 0.0, 0.0)
    return (v[0] / size, v[1] / size, v[2] / size)


def project_on_plane(v: Vector3, normal: Vector3) -> Vector3:
    n = normalize(normal)
    return sub(v, scale(n, dot(v, n)))


def lerp(a: Vector3, b: Vector3, t: float) -> Vector3:
    return add(a, scale(sub(b, a), t))
