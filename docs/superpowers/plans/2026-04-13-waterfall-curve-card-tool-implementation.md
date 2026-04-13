# Waterfall Curve Card Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first Blender add-on version of the waterfall curve card tool from the approved design spec.

**Architecture:** Keep trajectory solving, adaptive resampling, stable frame generation, and X-card mesh generation in pure Python modules under `addon/waterfall_tool/core` so they can be tested with `pytest`. Keep Blender-only behavior in `adapters`, `properties`, `operators`, and `panel`, with the runtime flow `Emitter -> simulated Flow Curve -> live Preview Mesh -> independent Baked Mesh`.

**Tech Stack:** Python 3.11-compatible code, Blender Python API, `pytest`, PowerShell, repository root `D:\YYBWorkSpace\GitHub\waterfallTool`.

---

## File Structure

- Create: `.gitignore`
- Create: `pyproject.toml`
- Create: `addon/waterfall_tool/__init__.py`
- Create: `addon/waterfall_tool/registration.py`
- Create: `addon/waterfall_tool/core/__init__.py`
- Create: `addon/waterfall_tool/core/types.py`
- Create: `addon/waterfall_tool/core/vector_math.py`
- Create: `addon/waterfall_tool/core/trajectory.py`
- Create: `addon/waterfall_tool/core/curve_sampling.py`
- Create: `addon/waterfall_tool/core/frames.py`
- Create: `addon/waterfall_tool/core/mesh_builder.py`
- Create: `addon/waterfall_tool/adapters/__init__.py`
- Create: `addon/waterfall_tool/adapters/blender_scene.py`
- Create: `addon/waterfall_tool/adapters/blender_curve.py`
- Create: `addon/waterfall_tool/adapters/blender_mesh.py`
- Create: `addon/waterfall_tool/properties.py`
- Create: `addon/waterfall_tool/operators/__init__.py`
- Create: `addon/waterfall_tool/operators/simulate.py`
- Create: `addon/waterfall_tool/operators/preview.py`
- Create: `addon/waterfall_tool/operators/bake.py`
- Create: `addon/waterfall_tool/panel.py`
- Create: `scripts/smoke_blender_addon.py`
- Create: `tests/core/test_vector_math.py`
- Create: `tests/core/test_trajectory.py`
- Create: `tests/core/test_curve_sampling.py`
- Create: `tests/core/test_frames.py`
- Create: `tests/core/test_mesh_builder.py`
- Create: `tests/core/test_registration_contract.py`

---

### Task 1: Project Scaffold And Core Contracts

**Files:**
- Create: `.gitignore`
- Create: `pyproject.toml`
- Create: `addon/waterfall_tool/__init__.py`
- Create: `addon/waterfall_tool/core/__init__.py`
- Create: `addon/waterfall_tool/core/types.py`
- Create: `addon/waterfall_tool/core/vector_math.py`
- Create: `tests/core/test_vector_math.py`

- [ ] **Step 1: Write the failing vector math tests**

Create `tests/core/test_vector_math.py`:

```python
from waterfall_tool.core.vector_math import add, cross, dot, length, normalize, project_on_plane, scale, sub


def test_vector_operations_are_tuple_based():
    assert add((1.0, 2.0, 3.0), (4.0, 5.0, 6.0)) == (5.0, 7.0, 9.0)
    assert sub((4.0, 5.0, 6.0), (1.0, 2.0, 3.0)) == (3.0, 3.0, 3.0)
    assert scale((1.0, -2.0, 3.0), 2.0) == (2.0, -4.0, 6.0)
    assert dot((1.0, 2.0, 3.0), (3.0, 2.0, 1.0)) == 10.0
    assert cross((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)) == (0.0, 0.0, 1.0)


def test_normalize_handles_zero_length_vectors():
    assert normalize((0.0, 0.0, 0.0)) == (0.0, 0.0, 0.0)
    assert normalize((0.0, 3.0, 4.0)) == (0.0, 0.6, 0.8)
    assert length((0.0, 3.0, 4.0)) == 5.0


def test_project_on_plane_removes_normal_component():
    assert project_on_plane((1.0, 2.0, 3.0), (0.0, 0.0, 1.0)) == (1.0, 2.0, 0.0)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
pytest tests/core/test_vector_math.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'waterfall_tool'`.

- [ ] **Step 3: Add project configuration and core base files**

Create `.gitignore`:

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
*.blend1
*.blend2
*.blend@
*.tmp
```

Create `pyproject.toml`:

```toml
[tool.pytest.ini_options]
pythonpath = ["addon"]
testpaths = ["tests"]
addopts = "-q"
```

Create `addon/waterfall_tool/__init__.py`:

```python
from __future__ import annotations

bl_info = {
    "name": "Waterfall Curve Card Tool",
    "author": "waterfallTool",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Waterfall",
    "description": "Simulate editable waterfall flow curves and generate X-card strip meshes.",
    "category": "Object",
}


def register() -> None:
    from .registration import register

    register()


def unregister() -> None:
    from .registration import unregister

    unregister()
```

Create `addon/waterfall_tool/core/__init__.py`:

```python
from __future__ import annotations
```

Create `addon/waterfall_tool/core/types.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field

Vector3 = tuple[float, float, float]
Vector2 = tuple[float, float]


@dataclass(frozen=True)
class EmitterSettings:
    speed: float = 8.0
    gravity: float = 9.81
    drag: float = 0.0
    time_step: float = 0.05
    step_count: int = 80
    attach_strength: float = 0.7
    detach_threshold: float = 0.35


@dataclass(frozen=True)
class MeshSettings:
    base_segment_density: float = 1.0
    curvature_refine_strength: float = 1.0
    start_width: float = 1.0
    end_width: float = 1.0
    width_falloff: float = 1.0
    cross_angle_degrees: float = 90.0
    uv_speed_scale: float = 1.0


@dataclass(frozen=True)
class CollisionSample:
    hit: bool
    point: Vector3 = (0.0, 0.0, 0.0)
    normal: Vector3 = (0.0, 0.0, 1.0)
    support: float = 0.0


@dataclass(frozen=True)
class TrajectoryPoint:
    position: Vector3
    velocity: Vector3
    speed: float
    attached: bool = False


@dataclass(frozen=True)
class CurveSample:
    position: Vector3
    tangent: Vector3
    speed: float
    arc_length: float
    t: float


@dataclass(frozen=True)
class Frame:
    tangent: Vector3
    normal: Vector3
    binormal: Vector3


@dataclass(frozen=True)
class MeshData:
    vertices: list[Vector3] = field(default_factory=list)
    faces: list[tuple[int, int, int, int]] = field(default_factory=list)
    uv0: list[list[Vector2]] = field(default_factory=list)
    uv1: list[list[Vector2]] = field(default_factory=list)


class CollisionProvider:
    def sample(self, start: Vector3, end: Vector3) -> CollisionSample:
        return CollisionSample(hit=False)
```

Create `addon/waterfall_tool/core/vector_math.py`:

```python
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
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```powershell
pytest tests/core/test_vector_math.py -v
```

Expected: PASS for all 3 tests.

- [ ] **Step 5: Commit**

```powershell
git add .gitignore pyproject.toml addon/waterfall_tool/__init__.py addon/waterfall_tool/core/__init__.py addon/waterfall_tool/core/types.py addon/waterfall_tool/core/vector_math.py tests/core/test_vector_math.py
git commit -m "feat: scaffold waterfall core package"
```

---

### Task 2: Trajectory Solver With Attach And Detach

**Files:**
- Create: `addon/waterfall_tool/core/trajectory.py`
- Create: `tests/core/test_trajectory.py`

- [ ] **Step 1: Write the failing trajectory tests**

Create `tests/core/test_trajectory.py`:

```python
from waterfall_tool.core.trajectory import simulate_trajectory
from waterfall_tool.core.types import CollisionProvider, CollisionSample, EmitterSettings


class NoCollision(CollisionProvider):
    def sample(self, start, end):
        return CollisionSample(hit=False)


class GroundCollision(CollisionProvider):
    def sample(self, start, end):
        if end[2] <= 0.0:
            return CollisionSample(hit=True, point=(end[0], end[1], 0.0), normal=(0.0, 0.0, 1.0), support=1.0)
        return CollisionSample(hit=False)


class WeakSupportCollision(CollisionProvider):
    def sample(self, start, end):
        return CollisionSample(hit=True, point=end, normal=(0.0, 0.0, 1.0), support=0.1)


def test_no_collision_falls_under_gravity():
    settings = EmitterSettings(speed=0.0, gravity=10.0, drag=0.0, time_step=0.1, step_count=3)
    points = simulate_trajectory((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), settings, NoCollision())
    assert len(points) == 4
    assert points[-1].position[2] < points[0].position[2]
    assert points[-1].attached is False


def test_collision_with_support_slides_along_surface():
    settings = EmitterSettings(speed=4.0, gravity=10.0, drag=0.0, time_step=0.1, step_count=6, attach_strength=1.0)
    points = simulate_trajectory((0.0, 0.0, 0.15), (1.0, 0.0, -0.2), settings, GroundCollision())
    attached_points = [point for point in points if point.attached]
    assert attached_points
    assert attached_points[-1].position[2] == 0.0
    assert attached_points[-1].velocity[2] == 0.0


def test_weak_support_detaches_and_keeps_falling():
    settings = EmitterSettings(speed=2.0, gravity=10.0, drag=0.0, time_step=0.1, step_count=3, detach_threshold=0.5)
    points = simulate_trajectory((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), settings, WeakSupportCollision())
    assert all(point.attached is False for point in points[1:])
    assert points[-1].velocity[2] < 0.0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```powershell
pytest tests/core/test_trajectory.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'waterfall_tool.core.trajectory'`.

- [ ] **Step 3: Add the trajectory solver**

Create `addon/waterfall_tool/core/trajectory.py`:

```python
from __future__ import annotations

from .types import CollisionProvider, EmitterSettings, TrajectoryPoint, Vector3
from .vector_math import add, length, normalize, project_on_plane, scale


def _apply_drag(velocity: Vector3, drag: float, time_step: float) -> Vector3:
    factor = max(0.0, 1.0 - drag * time_step)
    return scale(velocity, factor)


def _advance_freefall(velocity: Vector3, settings: EmitterSettings) -> Vector3:
    dragged = _apply_drag(velocity, settings.drag, settings.time_step)
    return (dragged[0], dragged[1], dragged[2] - settings.gravity * settings.time_step)


def simulate_trajectory(
    start_position: Vector3,
    direction: Vector3,
    settings: EmitterSettings,
    collision_provider: CollisionProvider,
) -> list[TrajectoryPoint]:
    unit_direction = normalize(direction)
    velocity = scale(unit_direction, settings.speed)
    points = [TrajectoryPoint(position=start_position, velocity=velocity, speed=length(velocity), attached=False)]
    position = start_position

    for _ in range(settings.step_count):
        candidate_velocity = _advance_freefall(velocity, settings)
        candidate_position = add(position, scale(candidate_velocity, settings.time_step))
        collision = collision_provider.sample(position, candidate_position)

        if collision.hit and collision.support * settings.attach_strength >= settings.detach_threshold:
            slide_velocity = project_on_plane(candidate_velocity, collision.normal)
            position = collision.point
            velocity = slide_velocity
            points.append(TrajectoryPoint(position=position, velocity=velocity, speed=length(velocity), attached=True))
            continue

        position = candidate_position
        velocity = candidate_velocity
        points.append(TrajectoryPoint(position=position, velocity=velocity, speed=length(velocity), attached=False))

    return points
```

- [ ] **Step 4: Run the trajectory tests**

Run:

```powershell
pytest tests/core/test_trajectory.py -v
```

Expected: PASS for all 3 tests.

- [ ] **Step 5: Run all core tests**

Run:

```powershell
pytest tests/core -v
```

Expected: PASS for all existing tests.

- [ ] **Step 6: Commit**

```powershell
git add addon/waterfall_tool/core/trajectory.py tests/core/test_trajectory.py
git commit -m "feat: simulate waterfall trajectory"
```

---

### Task 3: Physics-Assisted Curve Reflow

**Files:**
- Modify: `addon/waterfall_tool/core/trajectory.py`
- Modify: `tests/core/test_trajectory.py`

- [ ] **Step 1: Extend the failing tests for guided reflow**

Append to `tests/core/test_trajectory.py`:

```python

def test_guided_reflow_keeps_manual_points_when_there_is_no_collision():
    settings = EmitterSettings(speed=4.0, gravity=10.0, drag=0.0, time_step=0.1, step_count=4)
    guide = [(0.0, 0.0, 1.0), (0.5, 0.0, 0.5), (1.0, 0.0, 0.0)]
    points = simulate_guided_trajectory(guide, [4.0, 3.0, 2.0], settings, NoCollision())
    assert [point.position for point in points] == guide


def test_guided_reflow_snaps_supported_points_to_surface():
    settings = EmitterSettings(speed=4.0, gravity=10.0, drag=0.0, time_step=0.1, step_count=4, attach_strength=1.0)
    guide = [(0.0, 0.0, 1.0), (0.5, 0.0, -0.5), (1.0, 0.0, -1.0)]
    points = simulate_guided_trajectory(guide, [4.0, 3.0, 2.0], settings, GroundCollision())
    assert points[1].position[2] == 0.0
    assert points[2].position[2] == 0.0
    assert points[1].attached is True
```

Also update the import at the top of the file:

```python
from waterfall_tool.core.trajectory import simulate_guided_trajectory, simulate_trajectory
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```powershell
pytest tests/core/test_trajectory.py -v
```

Expected: FAIL with `ImportError: cannot import name 'simulate_guided_trajectory'`.

- [ ] **Step 3: Add guided reflow to the trajectory module**

Append to `addon/waterfall_tool/core/trajectory.py`:

```python

def simulate_guided_trajectory(
    guide_positions: list[Vector3],
    guide_speeds: list[float],
    settings: EmitterSettings,
    collision_provider: CollisionProvider,
) -> list[TrajectoryPoint]:
    if not guide_positions:
        return []

    result: list[TrajectoryPoint] = []
    for index, position in enumerate(guide_positions):
        if index == 0:
            speed = guide_speeds[0] if guide_speeds else settings.speed
            result.append(TrajectoryPoint(position=position, velocity=(0.0, 0.0, 0.0), speed=speed, attached=False))
            continue

        previous = result[-1].position
        requested = guide_positions[index]
        requested_speed = guide_speeds[index] if index < len(guide_speeds) else guide_speeds[-1]
        direction = normalize((requested[0] - previous[0], requested[1] - previous[1], requested[2] - previous[2]))
        collision = collision_provider.sample(previous, requested)

        if collision.hit and collision.support * settings.attach_strength >= settings.detach_threshold:
            velocity = project_on_plane(scale(direction, requested_speed), collision.normal)
            result.append(TrajectoryPoint(position=collision.point, velocity=velocity, speed=length(velocity), attached=True))
        else:
            velocity = scale(direction, requested_speed)
            result.append(TrajectoryPoint(position=requested, velocity=velocity, speed=length(velocity), attached=False))

    return result
```

- [ ] **Step 4: Run the trajectory tests again**

Run:

```powershell
pytest tests/core/test_trajectory.py -v
```

Expected: PASS for all trajectory tests, including guided reflow.

- [ ] **Step 5: Commit**

```powershell
git add addon/waterfall_tool/core/trajectory.py tests/core/test_trajectory.py
git commit -m "feat: support physics assisted curve reflow"
```

---

### Task 4: Adaptive Curve Sampling And Width Falloff

**Files:**
- Create: `addon/waterfall_tool/core/curve_sampling.py`
- Create: `tests/core/test_curve_sampling.py`

- [ ] **Step 1: Write the failing curve sampling tests**

Create `tests/core/test_curve_sampling.py`:

```python
from waterfall_tool.core.curve_sampling import compute_width, resample_polyline
from waterfall_tool.core.types import MeshSettings, TrajectoryPoint


def point(position, speed=1.0):
    return TrajectoryPoint(position=position, velocity=(speed, 0.0, 0.0), speed=speed)


def test_width_falloff_interpolates_start_to_end():
    settings = MeshSettings(start_width=2.0, end_width=1.0, width_falloff=1.0)
    assert compute_width(settings, 0.0) == 2.0
    assert compute_width(settings, 1.0) == 1.0
    assert compute_width(settings, 0.5) == 1.5


def test_resample_polyline_preserves_endpoints_and_arc_lengths():
    samples = resample_polyline(
        [point((0.0, 0.0, 0.0), 2.0), point((0.0, 0.0, -2.0), 4.0)],
        base_segment_density=2.0,
        curvature_refine_strength=0.0,
    )
    assert samples[0].position == (0.0, 0.0, 0.0)
    assert samples[-1].position == (0.0, 0.0, -2.0)
    assert samples[-1].arc_length == 2.0
    assert [sample.t for sample in samples] == sorted(sample.t for sample in samples)


def test_curvature_adds_more_samples_near_bends():
    straight = [point((0.0, 0.0, 0.0)), point((0.0, 0.0, -1.0)), point((0.0, 0.0, -2.0))]
    bent = [point((0.0, 0.0, 0.0)), point((1.0, 0.0, -1.0)), point((0.0, 0.0, -2.0))]
    straight_samples = resample_polyline(straight, base_segment_density=1.0, curvature_refine_strength=2.0)
    bent_samples = resample_polyline(bent, base_segment_density=1.0, curvature_refine_strength=2.0)
    assert len(bent_samples) > len(straight_samples)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```powershell
pytest tests/core/test_curve_sampling.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'waterfall_tool.core.curve_sampling'`.

- [ ] **Step 3: Add adaptive sampling**

Create `addon/waterfall_tool/core/curve_sampling.py`:

```python
from __future__ import annotations

from math import acos, ceil

from .types import CurveSample, MeshSettings, TrajectoryPoint
from .vector_math import dot, length, lerp, normalize, sub


def compute_width(settings: MeshSettings, normalized_t: float) -> float:
    t = min(1.0, max(0.0, normalized_t))
    shaped = t ** max(0.001, settings.width_falloff)
    return settings.start_width + (settings.end_width - settings.start_width) * shaped


def _segment_curvature(points: list[TrajectoryPoint], index: int) -> float:
    if index <= 0 or index >= len(points) - 1:
        return 0.0
    incoming = normalize(sub(points[index].position, points[index - 1].position))
    outgoing = normalize(sub(points[index + 1].position, points[index].position))
    return acos(min(1.0, max(-1.0, dot(incoming, outgoing))))


def resample_polyline(
    points: list[TrajectoryPoint],
    base_segment_density: float,
    curvature_refine_strength: float,
) -> list[CurveSample]:
    if not points:
        return []
    if len(points) == 1:
        point = points[0]
        return [CurveSample(position=point.position, tangent=(0.0, 0.0, -1.0), speed=point.speed, arc_length=0.0, t=0.0)]

    segment_lengths: list[float] = []
    total_length = 0.0
    for index in range(len(points) - 1):
        segment_length = length(sub(points[index + 1].position, points[index].position))
        segment_lengths.append(segment_length)
        total_length += segment_length

    samples: list[CurveSample] = []
    walked = 0.0
    for index, segment_length in enumerate(segment_lengths):
        a = points[index]
        b = points[index + 1]
        tangent = normalize(sub(b.position, a.position))
        curvature = max(_segment_curvature(points, index), _segment_curvature(points, index + 1))
        density = max(0.1, base_segment_density) * (1.0 + curvature * max(0.0, curvature_refine_strength))
        steps = max(1, int(ceil(segment_length * density)))

        for step in range(steps):
            if index > 0 and step == 0:
                continue
            local_t = step / steps
            arc_length = walked + segment_length * local_t
            normalized_t = 0.0 if total_length <= 1.0e-8 else arc_length / total_length
            speed = a.speed + (b.speed - a.speed) * local_t
            samples.append(
                CurveSample(
                    position=lerp(a.position, b.position, local_t),
                    tangent=tangent,
                    speed=speed,
                    arc_length=arc_length,
                    t=normalized_t,
                )
            )
        walked += segment_length

    final = points[-1]
    previous = points[-2]
    samples.append(
        CurveSample(
            position=final.position,
            tangent=normalize(sub(final.position, previous.position)),
            speed=final.speed,
            arc_length=total_length,
            t=1.0,
        )
    )
    return samples
```

- [ ] **Step 4: Run the curve sampling tests**

Run:

```powershell
pytest tests/core/test_curve_sampling.py -v
```

Expected: PASS for all 3 tests.

- [ ] **Step 5: Commit**

```powershell
git add addon/waterfall_tool/core/curve_sampling.py tests/core/test_curve_sampling.py
git commit -m "feat: resample waterfall flow curves"
```

---

### Task 5: Stable Frame Propagation

**Files:**
- Create: `addon/waterfall_tool/core/frames.py`
- Create: `tests/core/test_frames.py`

- [ ] **Step 1: Write the failing frame tests**

Create `tests/core/test_frames.py`:

```python
from waterfall_tool.core.frames import build_frames
from waterfall_tool.core.types import CurveSample
from waterfall_tool.core.vector_math import dot, length


def sample(position, tangent):
    return CurveSample(position=position, tangent=tangent, speed=1.0, arc_length=0.0, t=0.0)


def test_frames_are_orthonormal():
    frames = build_frames(
        [
            sample((0.0, 0.0, 0.0), (0.0, 0.0, -1.0)),
            sample((0.0, 0.0, -1.0), (1.0, 0.0, -1.0)),
        ]
    )
    for frame in frames:
        assert round(length(frame.tangent), 6) == 1.0
        assert round(length(frame.normal), 6) == 1.0
        assert round(length(frame.binormal), 6) == 1.0
        assert round(dot(frame.tangent, frame.normal), 6) == 0.0
        assert round(dot(frame.tangent, frame.binormal), 6) == 0.0


def test_frames_do_not_flip_for_vertical_curve():
    frames = build_frames(
        [
            sample((0.0, 0.0, 0.0), (0.0, 0.0, -1.0)),
            sample((0.0, 0.0, -1.0), (0.0, 0.0, -1.0)),
            sample((0.0, 0.0, -2.0), (0.0, 0.0, -1.0)),
        ]
    )
    assert frames[0].normal == frames[1].normal == frames[2].normal
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```powershell
pytest tests/core/test_frames.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'waterfall_tool.core.frames'`.

- [ ] **Step 3: Add stable frame propagation**

Create `addon/waterfall_tool/core/frames.py`:

```python
from __future__ import annotations

from .types import CurveSample, Frame, Vector3
from .vector_math import cross, dot, length, normalize, project_on_plane

WORLD_UP: Vector3 = (0.0, 0.0, 1.0)
WORLD_RIGHT: Vector3 = (1.0, 0.0, 0.0)


def _fallback_normal(tangent: Vector3) -> Vector3:
    candidate = project_on_plane(WORLD_UP, tangent)
    if length(candidate) <= 1.0e-8:
        candidate = project_on_plane(WORLD_RIGHT, tangent)
    return normalize(candidate)


def build_frames(samples: list[CurveSample]) -> list[Frame]:
    frames: list[Frame] = []
    previous_normal: Vector3 | None = None

    for sample in samples:
        tangent = normalize(sample.tangent)
        if length(tangent) <= 1.0e-8:
            tangent = (0.0, 0.0, -1.0)

        if previous_normal is None:
            normal = _fallback_normal(tangent)
        else:
            normal = project_on_plane(previous_normal, tangent)
            if length(normal) <= 1.0e-8:
                normal = _fallback_normal(tangent)
            normal = normalize(normal)

        binormal = normalize(cross(tangent, normal))
        normal = normalize(cross(binormal, tangent))

        if previous_normal is not None and dot(normal, previous_normal) < 0.0:
            normal = (-normal[0], -normal[1], -normal[2])
            binormal = (-binormal[0], -binormal[1], -binormal[2])

        frames.append(Frame(tangent=tangent, normal=normal, binormal=binormal))
        previous_normal = normal

    return frames
```

- [ ] **Step 4: Run the frame tests**

Run:

```powershell
pytest tests/core/test_frames.py -v
```

Expected: PASS for both tests.

- [ ] **Step 5: Commit**

```powershell
git add addon/waterfall_tool/core/frames.py tests/core/test_frames.py
git commit -m "feat: build stable curve frames"
```

---

### Task 6: X-Card Mesh Builder With UV0 And Speed UV

**Files:**
- Create: `addon/waterfall_tool/core/mesh_builder.py`
- Create: `tests/core/test_mesh_builder.py`

- [ ] **Step 1: Write the failing mesh builder tests**

Create `tests/core/test_mesh_builder.py`:

```python
from waterfall_tool.core.mesh_builder import build_x_card_mesh
from waterfall_tool.core.types import MeshSettings, TrajectoryPoint


def point(position, speed=1.0):
    return TrajectoryPoint(position=position, velocity=(0.0, 0.0, -speed), speed=speed)


def test_mesh_has_two_card_strips_with_quad_faces():
    settings = MeshSettings(start_width=2.0, end_width=2.0, cross_angle_degrees=90.0)
    mesh = build_x_card_mesh(
        [point((0.0, 0.0, 0.0), 1.0), point((0.0, 0.0, -1.0), 2.0), point((0.0, 0.0, -2.0), 3.0)],
        settings,
    )
    assert len(mesh.vertices) == 12
    assert len(mesh.faces) == 4
    assert len(mesh.uv0) == 4
    assert len(mesh.uv1) == 4


def test_width_changes_along_curve():
    settings = MeshSettings(start_width=2.0, end_width=1.0, width_falloff=1.0, cross_angle_degrees=90.0)
    mesh = build_x_card_mesh([point((0.0, 0.0, 0.0)), point((0.0, 0.0, -2.0))], settings)
    start_left = mesh.vertices[0]
    start_right = mesh.vertices[1]
    end_left = mesh.vertices[2]
    end_right = mesh.vertices[3]
    start_width = abs(start_right[0] - start_left[0]) + abs(start_right[1] - start_left[1])
    end_width = abs(end_right[0] - end_left[0]) + abs(end_right[1] - end_left[1])
    assert end_width < start_width


def test_speed_is_packed_into_uv1():
    settings = MeshSettings(start_width=1.0, end_width=1.0, uv_speed_scale=1.0)
    mesh = build_x_card_mesh([point((0.0, 0.0, 0.0), 1.0), point((0.0, 0.0, -1.0), 3.0)], settings)
    uv1_values = [uv for face in mesh.uv1 for uv in face]
    assert min(value[1] for value in uv1_values) == 0.0
    assert max(value[1] for value in uv1_values) == 1.0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```powershell
pytest tests/core/test_mesh_builder.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'waterfall_tool.core.mesh_builder'`.

- [ ] **Step 3: Add the mesh builder**

Create `addon/waterfall_tool/core/mesh_builder.py`:

```python
from __future__ import annotations

from math import cos, radians, sin

from .curve_sampling import compute_width, resample_polyline
from .frames import build_frames
from .types import MeshData, MeshSettings, TrajectoryPoint, Vector3
from .vector_math import add, scale


def _rotate_in_frame(normal: Vector3, binormal: Vector3, angle_degrees: float) -> Vector3:
    angle = radians(angle_degrees)
    return add(scale(normal, cos(angle)), scale(binormal, sin(angle)))


def _speed_range(points: list[TrajectoryPoint]) -> tuple[float, float]:
    speeds = [point.speed for point in points]
    if not speeds:
        return (0.0, 1.0)
    minimum = min(speeds)
    maximum = max(speeds)
    if abs(maximum - minimum) <= 1.0e-8:
        return (minimum, minimum + 1.0)
    return (minimum, maximum)


def _normalized_speed(speed: float, minimum: float, maximum: float, scale_value: float) -> float:
    value = (speed - minimum) / (maximum - minimum)
    return min(1.0, max(0.0, value * max(0.0, scale_value)))


def build_x_card_mesh(points: list[TrajectoryPoint], settings: MeshSettings) -> MeshData:
    samples = resample_polyline(points, settings.base_segment_density, settings.curvature_refine_strength)
    if len(samples) < 2:
        return MeshData()

    frames = build_frames(samples)
    speed_min, speed_max = _speed_range(points)
    mesh = MeshData()
    strip_angles = (-settings.cross_angle_degrees * 0.5, settings.cross_angle_degrees * 0.5)

    for strip_angle in strip_angles:
        strip_start = len(mesh.vertices)
        for sample, frame in zip(samples, frames, strict=True):
            half_width = compute_width(settings, sample.t) * 0.5
            axis = _rotate_in_frame(frame.normal, frame.binormal, strip_angle)
            mesh.vertices.append(add(sample.position, scale(axis, -half_width)))
            mesh.vertices.append(add(sample.position, scale(axis, half_width)))

        for index in range(len(samples) - 1):
            a = strip_start + index * 2
            b = a + 1
            c = a + 3
            d = a + 2
            mesh.faces.append((a, b, c, d))
            start = samples[index]
            end = samples[index + 1]
            mesh.uv0.append([(0.0, start.arc_length), (1.0, start.arc_length), (1.0, end.arc_length), (0.0, end.arc_length)])
            start_speed = _normalized_speed(start.speed, speed_min, speed_max, settings.uv_speed_scale)
            end_speed = _normalized_speed(end.speed, speed_min, speed_max, settings.uv_speed_scale)
            mesh.uv1.append([(0.0, start_speed), (1.0, start_speed), (1.0, end_speed), (0.0, end_speed)])

    return mesh
```

- [ ] **Step 4: Run the mesh builder tests**

Run:

```powershell
pytest tests/core/test_mesh_builder.py -v
```

Expected: PASS for all 3 tests.

- [ ] **Step 5: Run the full core suite**

Run:

```powershell
pytest tests/core -v
```

Expected: PASS for all existing core tests.

- [ ] **Step 6: Commit**

```powershell
git add addon/waterfall_tool/core/mesh_builder.py tests/core/test_mesh_builder.py
git commit -m "feat: build x-card waterfall mesh"
```

---

### Task 7: Blender Properties And Registration Contract

**Files:**
- Create: `addon/waterfall_tool/registration.py`
- Create: `addon/waterfall_tool/properties.py`
- Create: `addon/waterfall_tool/operators/__init__.py`
- Create: `tests/core/test_registration_contract.py`

- [ ] **Step 1: Write the failing registration contract test**

Create `tests/core/test_registration_contract.py`:

```python
from waterfall_tool.registration import CLASS_NAMES


def test_registration_class_names_are_stable():
    assert CLASS_NAMES == (
        "WaterfallEmitterSettings",
        "WaterfallCurveSettings",
        "WATERFALL_OT_simulate_curve",
        "WATERFALL_OT_rebuild_preview",
        "WATERFALL_OT_bake_mesh",
        "WATERFALL_PT_curve_card_panel",
    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
pytest tests/core/test_registration_contract.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'waterfall_tool.registration'`.

- [ ] **Step 3: Add property groups and import-safe registration**

Create `addon/waterfall_tool/operators/__init__.py`:

```python
from __future__ import annotations
```

Create `addon/waterfall_tool/properties.py`:

```python
from __future__ import annotations

try:
    import bpy
except ModuleNotFoundError:
    bpy = None


def _safe_operator_call(operator_id: str) -> None:
    if bpy is None:
        return
    try:
        namespace, name = operator_id.split(".")
        getattr(getattr(bpy.ops, namespace), name)()
    except RuntimeError:
        return


def _refresh_from_emitter(_self, _context) -> None:
    _safe_operator_call("waterfall.simulate_curve")


def _refresh_from_curve(_self, _context) -> None:
    _safe_operator_call("waterfall.rebuild_preview")


if bpy is not None:

    class WaterfallEmitterSettings(bpy.types.PropertyGroup):
        speed: bpy.props.FloatProperty(name="Speed", default=8.0, min=0.0, update=_refresh_from_emitter)
        direction_axis: bpy.props.EnumProperty(
            name="Direction Axis",
            items=[
                ("NEG_Z", "-Z", "Use local -Z as initial velocity direction"),
                ("POS_Y", "+Y", "Use local +Y as initial velocity direction"),
                ("NEG_Y", "-Y", "Use local -Y as initial velocity direction"),
            ],
            default="NEG_Z",
            update=_refresh_from_emitter,
        )
        gravity: bpy.props.FloatProperty(name="Gravity", default=9.81, min=0.0, update=_refresh_from_emitter)
        drag: bpy.props.FloatProperty(name="Drag", default=0.0, min=0.0, update=_refresh_from_emitter)
        simulation_step_count: bpy.props.IntProperty(name="Simulation Steps", default=80, min=1, update=_refresh_from_emitter)
        simulation_time_step: bpy.props.FloatProperty(name="Time Step", default=0.05, min=0.001, update=_refresh_from_emitter)
        attach_strength: bpy.props.FloatProperty(name="Attach Strength", default=0.7, min=0.0, max=1.0, update=_refresh_from_emitter)
        detach_threshold: bpy.props.FloatProperty(name="Detach Threshold", default=0.35, min=0.0, max=1.0, update=_refresh_from_emitter)
        preview_enabled: bpy.props.BoolProperty(name="Preview Enabled", default=True, update=_refresh_from_emitter)
        flow_curve_name: bpy.props.StringProperty(name="Flow Curve")


    class WaterfallCurveSettings(bpy.types.PropertyGroup):
        curve_mode: bpy.props.EnumProperty(
            name="Curve Mode",
            items=[
                ("MANUAL_SHAPE", "Manual Shape", "Use the edited curve directly"),
                ("PHYSICS_ASSISTED", "Physics Assisted", "Re-apply collision correction from edited points"),
            ],
            default="MANUAL_SHAPE",
            update=_refresh_from_curve,
        )
        preview_enabled: bpy.props.BoolProperty(name="Preview Enabled", default=True, update=_refresh_from_curve)
        base_segment_density: bpy.props.FloatProperty(name="Base Segment Density", default=1.0, min=0.1, update=_refresh_from_curve)
        curvature_refine_strength: bpy.props.FloatProperty(name="Curvature Refine Strength", default=1.0, min=0.0, update=_refresh_from_curve)
        start_width: bpy.props.FloatProperty(name="Start Width", default=1.0, min=0.0, update=_refresh_from_curve)
        end_width: bpy.props.FloatProperty(name="End Width", default=1.0, min=0.0, update=_refresh_from_curve)
        width_falloff: bpy.props.FloatProperty(name="Width Falloff", default=1.0, min=0.001, update=_refresh_from_curve)
        cross_angle: bpy.props.FloatProperty(name="Cross Angle", default=90.0, min=1.0, max=179.0, update=_refresh_from_curve)
        uv_speed_scale: bpy.props.FloatProperty(name="UV Speed Scale", default=1.0, min=0.0, update=_refresh_from_curve)
        emitter_name: bpy.props.StringProperty(name="Emitter")
        preview_mesh_name: bpy.props.StringProperty(name="Preview Mesh")
        baked_mesh_name: bpy.props.StringProperty(name="Baked Mesh")

else:

    class WaterfallEmitterSettings:
        pass


    class WaterfallCurveSettings:
        pass
```

Create `addon/waterfall_tool/registration.py`:

```python
from __future__ import annotations

CLASS_NAMES = (
    "WaterfallEmitterSettings",
    "WaterfallCurveSettings",
    "WATERFALL_OT_simulate_curve",
    "WATERFALL_OT_rebuild_preview",
    "WATERFALL_OT_bake_mesh",
    "WATERFALL_PT_curve_card_panel",
)


def _classes() -> list[type]:
    from .operators.bake import WATERFALL_OT_bake_mesh
    from .operators.preview import WATERFALL_OT_rebuild_preview
    from .operators.simulate import WATERFALL_OT_simulate_curve
    from .panel import WATERFALL_PT_curve_card_panel
    from .properties import WaterfallCurveSettings, WaterfallEmitterSettings

    return [
        WaterfallEmitterSettings,
        WaterfallCurveSettings,
        WATERFALL_OT_simulate_curve,
        WATERFALL_OT_rebuild_preview,
        WATERFALL_OT_bake_mesh,
        WATERFALL_PT_curve_card_panel,
    ]


def register() -> None:
    import bpy

    classes = _classes()
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.waterfall_emitter = bpy.props.PointerProperty(type=classes[0])
    bpy.types.Object.waterfall_curve = bpy.props.PointerProperty(type=classes[1])


def unregister() -> None:
    import bpy

    if hasattr(bpy.types.Object, "waterfall_curve"):
        del bpy.types.Object.waterfall_curve
    if hasattr(bpy.types.Object, "waterfall_emitter"):
        del bpy.types.Object.waterfall_emitter
    for cls in reversed(_classes()):
        bpy.utils.unregister_class(cls)
```

- [ ] **Step 4: Run the registration contract test**

Run:

```powershell
pytest tests/core/test_registration_contract.py -v
```

Expected: PASS for the registration contract test.

- [ ] **Step 5: Commit**

```powershell
git add addon/waterfall_tool/operators/__init__.py addon/waterfall_tool/properties.py addon/waterfall_tool/registration.py tests/core/test_registration_contract.py
git commit -m "feat: add waterfall property registration"
```

---

### Task 8: Blender Scene, Curve, And Mesh Adapters

**Files:**
- Create: `addon/waterfall_tool/adapters/__init__.py`
- Create: `addon/waterfall_tool/adapters/blender_scene.py`
- Create: `addon/waterfall_tool/adapters/blender_curve.py`
- Create: `addon/waterfall_tool/adapters/blender_mesh.py`

- [ ] **Step 1: Create the adapter package**

Create `addon/waterfall_tool/adapters/__init__.py`:

```python
from __future__ import annotations
```

- [ ] **Step 2: Add the scene collision adapter**

Create `addon/waterfall_tool/adapters/blender_scene.py`:

```python
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
            world_normal = (evaluated.matrix_world.to_3x3() @ normal).normalized()
            hit_distance = (world_location - mathutils.Vector(start)).length
            if best_hit is None or hit_distance < best_hit[0]:
                best_hit = (hit_distance, world_location, world_normal)

        if best_hit is None:
            return CollisionSample(hit=False)

        _distance, location, normal = best_hit
        support = max(0.0, min(1.0, normal.z))
        return CollisionSample(hit=True, point=tuple(location), normal=tuple(normal), support=support)
```

- [ ] **Step 3: Add curve and mesh adapters**

Create `addon/waterfall_tool/adapters/blender_curve.py`:

```python
from __future__ import annotations

from ..core.types import TrajectoryPoint


def create_or_update_flow_curve(context, name: str, points: list[TrajectoryPoint]):
    import bpy

    curve_obj = bpy.data.objects.get(name)
    if curve_obj is None:
        curve_data = bpy.data.curves.new(name=name, type="CURVE")
        curve_data.dimensions = "3D"
        curve_obj = bpy.data.objects.new(name, curve_data)
        context.collection.objects.link(curve_obj)
    else:
        curve_data = curve_obj.data
        curve_data.splines.clear()

    spline = curve_data.splines.new("POLY")
    spline.points.add(max(0, len(points) - 1))
    for spline_point, trajectory_point in zip(spline.points, points, strict=True):
        x, y, z = trajectory_point.position
        spline_point.co = (x, y, z, 1.0)

    curve_obj["waterfall_flow_curve"] = True
    curve_obj["waterfall_speed_cache"] = [point.speed for point in points]
    return curve_obj


def read_flow_curve_points(curve_obj) -> tuple[list[tuple[float, float, float]], list[float]]:
    if not curve_obj.data.splines:
        return ([], [])
    spline = curve_obj.data.splines[0]
    speed_cache = list(curve_obj.get("waterfall_speed_cache", []))
    positions = []
    speeds = []
    for index, spline_point in enumerate(spline.points):
        world = curve_obj.matrix_world @ spline_point.co.to_3d()
        positions.append(tuple(world))
        speeds.append(float(speed_cache[index]) if index < len(speed_cache) else 1.0)
    return (positions, speeds)
```

Create `addon/waterfall_tool/adapters/blender_mesh.py`:

```python
from __future__ import annotations

from ..core.types import MeshData


def create_or_update_mesh_object(context, name: str, mesh_data: MeshData, *, generated: bool = True):
    import bpy

    obj = bpy.data.objects.get(name)
    if obj is None:
        blender_mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, blender_mesh)
        context.collection.objects.link(obj)
    else:
        blender_mesh = obj.data
        blender_mesh.clear_geometry()

    blender_mesh.from_pydata(mesh_data.vertices, [], mesh_data.faces)
    blender_mesh.update()

    if mesh_data.uv0:
        uv0 = blender_mesh.uv_layers.new(name="UV0")
        _write_uv_layer(uv0, mesh_data.uv0)
    if mesh_data.uv1:
        uv1 = blender_mesh.uv_layers.new(name="UV1_Speed")
        _write_uv_layer(uv1, mesh_data.uv1)

    obj["waterfall_generated"] = generated
    return obj


def _write_uv_layer(layer, face_uvs):
    loop_index = 0
    for face in face_uvs:
        for uv in face:
            layer.data[loop_index].uv = uv
            loop_index += 1
```

- [ ] **Step 4: Run the full core suite**

Run:

```powershell
pytest tests/core -v
```

Expected: PASS for all existing core tests because Blender imports stay inside adapter functions.

- [ ] **Step 5: Commit**

```powershell
git add addon/waterfall_tool/adapters/__init__.py addon/waterfall_tool/adapters/blender_scene.py addon/waterfall_tool/adapters/blender_curve.py addon/waterfall_tool/adapters/blender_mesh.py
git commit -m "feat: add blender data adapters"
```

---

### Task 9: Operators, Panel, And Live Refresh Hooks

**Files:**
- Create: `addon/waterfall_tool/operators/simulate.py`
- Create: `addon/waterfall_tool/operators/preview.py`
- Create: `addon/waterfall_tool/operators/bake.py`
- Create: `addon/waterfall_tool/panel.py`
- Modify: `addon/waterfall_tool/registration.py`

- [ ] **Step 1: Add the simulate operator**

Create `addon/waterfall_tool/operators/simulate.py`:

```python
from __future__ import annotations

try:
    import bpy
    import mathutils
except ModuleNotFoundError:
    bpy = None
    mathutils = None

from ..core.trajectory import simulate_trajectory
from ..core.types import EmitterSettings


def _direction_from_axis(obj, axis: str):
    vectors = {
        "NEG_Z": (0.0, 0.0, -1.0),
        "POS_Y": (0.0, 1.0, 0.0),
        "NEG_Y": (0.0, -1.0, 0.0),
    }
    local = vectors.get(axis, (0.0, 0.0, -1.0))
    world = obj.matrix_world.to_3x3() @ mathutils.Vector(local)
    return tuple(world.normalized())


if bpy is not None:

    class WATERFALL_OT_simulate_curve(bpy.types.Operator):
        bl_idname = "waterfall.simulate_curve"
        bl_label = "Generate / Re-simulate Curve"
        bl_options = {"REGISTER", "UNDO"}

        def execute(self, context):
            from ..adapters.blender_curve import create_or_update_flow_curve
            from ..adapters.blender_scene import BlenderVisibleMeshCollisionProvider

            emitter = context.object
            if emitter is None:
                self.report({"ERROR"}, "Select an emitter empty")
                return {"CANCELLED"}

            props = emitter.waterfall_emitter
            settings = EmitterSettings(
                speed=props.speed,
                gravity=props.gravity,
                drag=props.drag,
                time_step=props.simulation_time_step,
                step_count=props.simulation_step_count,
                attach_strength=props.attach_strength,
                detach_threshold=props.detach_threshold,
            )
            curve_name = props.flow_curve_name or f"{emitter.name}_FlowCurve"
            collision_provider = BlenderVisibleMeshCollisionProvider(context, excluded_names={curve_name})
            points = simulate_trajectory(
                tuple(emitter.matrix_world.translation),
                _direction_from_axis(emitter, props.direction_axis),
                settings,
                collision_provider,
            )
            curve = create_or_update_flow_curve(context, curve_name, points)
            props.flow_curve_name = curve.name
            curve.waterfall_curve.emitter_name = emitter.name
            bpy.ops.waterfall.rebuild_preview()
            return {"FINISHED"}

else:

    class WATERFALL_OT_simulate_curve:
        pass
```

- [ ] **Step 2: Add preview, bake, panel, and depsgraph live refresh**

Create `addon/waterfall_tool/operators/preview.py`:

```python
from __future__ import annotations

try:
    import bpy
except ModuleNotFoundError:
    bpy = None

from ..core.mesh_builder import build_x_card_mesh
from ..core.trajectory import simulate_guided_trajectory
from ..core.types import EmitterSettings, MeshSettings, TrajectoryPoint


def refresh_curve_preview(curve, context):
    from ..adapters.blender_curve import read_flow_curve_points
    from ..adapters.blender_mesh import create_or_update_mesh_object
    from ..adapters.blender_scene import BlenderVisibleMeshCollisionProvider

    props = curve.waterfall_curve
    if not props.preview_enabled:
        return None

    positions, speeds = read_flow_curve_points(curve)
    points = [TrajectoryPoint(position=position, velocity=(0.0, 0.0, -speed), speed=speed) for position, speed in zip(positions, speeds, strict=True)]

    if props.curve_mode == "PHYSICS_ASSISTED" and props.emitter_name:
        emitter = bpy.data.objects.get(props.emitter_name)
        if emitter is not None:
            emitter_props = emitter.waterfall_emitter
            emitter_settings = EmitterSettings(
                speed=emitter_props.speed,
                gravity=emitter_props.gravity,
                drag=emitter_props.drag,
                time_step=emitter_props.simulation_time_step,
                step_count=emitter_props.simulation_step_count,
                attach_strength=emitter_props.attach_strength,
                detach_threshold=emitter_props.detach_threshold,
            )
            collision_provider = BlenderVisibleMeshCollisionProvider(
                context,
                excluded_names={props.preview_mesh_name, props.baked_mesh_name, curve.name},
            )
            points = simulate_guided_trajectory(positions, speeds, emitter_settings, collision_provider)

    mesh_settings = MeshSettings(
        base_segment_density=props.base_segment_density,
        curvature_refine_strength=props.curvature_refine_strength,
        start_width=props.start_width,
        end_width=props.end_width,
        width_falloff=props.width_falloff,
        cross_angle_degrees=props.cross_angle,
        uv_speed_scale=props.uv_speed_scale,
    )
    preview_name = props.preview_mesh_name or f"{curve.name}_Preview"
    mesh = build_x_card_mesh(points, mesh_settings)
    preview = create_or_update_mesh_object(context, preview_name, mesh, generated=True)
    props.preview_mesh_name = preview.name
    return preview


if bpy is not None:

    def depsgraph_refresh(scene, depsgraph):
        context = bpy.context
        for update in depsgraph.updates:
            obj = getattr(update, "id", None)
            if getattr(obj, "type", None) == "CURVE" and obj.get("waterfall_flow_curve"):
                refresh_curve_preview(obj, context)


    class WATERFALL_OT_rebuild_preview(bpy.types.Operator):
        bl_idname = "waterfall.rebuild_preview"
        bl_label = "Rebuild Preview"
        bl_options = {"REGISTER", "UNDO"}

        def execute(self, context):
            curve = context.object
            if curve is None or curve.type != "CURVE":
                emitter = context.object
                curve = bpy.data.objects.get(emitter.waterfall_emitter.flow_curve_name) if emitter else None
            if curve is None or curve.type != "CURVE":
                self.report({"ERROR"}, "Select a flow curve or emitter")
                return {"CANCELLED"}
            refresh_curve_preview(curve, context)
            return {"FINISHED"}

else:

    def depsgraph_refresh(scene, depsgraph):
        return None


    class WATERFALL_OT_rebuild_preview:
        pass
```

Create `addon/waterfall_tool/operators/bake.py`:

```python
from __future__ import annotations

try:
    import bpy
except ModuleNotFoundError:
    bpy = None

from ..operators.preview import refresh_curve_preview


if bpy is not None:

    class WATERFALL_OT_bake_mesh(bpy.types.Operator):
        bl_idname = "waterfall.bake_mesh"
        bl_label = "Bake Mesh"
        bl_options = {"REGISTER", "UNDO"}

        def execute(self, context):
            curve = context.object
            if curve is None or curve.type != "CURVE":
                self.report({"ERROR"}, "Select a flow curve before baking")
                return {"CANCELLED"}

            preview = refresh_curve_preview(curve, context)
            if preview is None:
                self.report({"ERROR"}, "Preview is disabled or empty")
                return {"CANCELLED"}

            mesh_copy = preview.data.copy()
            baked = bpy.data.objects.new(f"{curve.name}_Baked", mesh_copy)
            context.collection.objects.link(baked)
            baked["waterfall_generated"] = True
            curve.waterfall_curve.baked_mesh_name = baked.name
            curve.waterfall_curve.preview_enabled = False
            return {"FINISHED"}

else:

    class WATERFALL_OT_bake_mesh:
        pass
```

Create `addon/waterfall_tool/panel.py`:

```python
from __future__ import annotations

try:
    import bpy
except ModuleNotFoundError:
    bpy = None


if bpy is not None:

    class WATERFALL_PT_curve_card_panel(bpy.types.Panel):
        bl_label = "Waterfall Curve Cards"
        bl_idname = "WATERFALL_PT_curve_card_panel"
        bl_space_type = "VIEW_3D"
        bl_region_type = "UI"
        bl_category = "Waterfall"

        def draw(self, context):
            layout = self.layout
            obj = context.object
            if obj is None:
                layout.label(text="Select an emitter or flow curve")
                return

            emitter = obj.waterfall_emitter
            curve = obj.waterfall_curve

            simulation = layout.box()
            simulation.label(text="Simulation")
            simulation.prop(emitter, "speed")
            simulation.prop(emitter, "direction_axis")
            simulation.prop(emitter, "gravity")
            simulation.prop(emitter, "drag")
            simulation.prop(emitter, "simulation_step_count")
            simulation.prop(emitter, "simulation_time_step")
            simulation.prop(emitter, "attach_strength")
            simulation.prop(emitter, "detach_threshold")
            simulation.operator("waterfall.simulate_curve")

            curve_box = layout.box()
            curve_box.label(text="Curve Mode")
            curve_box.prop(curve, "curve_mode")

            preview = layout.box()
            preview.label(text="Mesh Preview")
            preview.prop(curve, "preview_enabled")
            preview.prop(curve, "base_segment_density")
            preview.prop(curve, "curvature_refine_strength")
            preview.prop(curve, "start_width")
            preview.prop(curve, "end_width")
            preview.prop(curve, "width_falloff")
            preview.prop(curve, "cross_angle")
            preview.prop(curve, "uv_speed_scale")
            preview.operator("waterfall.rebuild_preview")

            bake = layout.box()
            bake.label(text="Bake")
            bake.operator("waterfall.bake_mesh")

else:

    class WATERFALL_PT_curve_card_panel:
        pass
```

Modify `addon/waterfall_tool/registration.py` to register the live refresh handler:

```python
from __future__ import annotations

CLASS_NAMES = (
    "WaterfallEmitterSettings",
    "WaterfallCurveSettings",
    "WATERFALL_OT_simulate_curve",
    "WATERFALL_OT_rebuild_preview",
    "WATERFALL_OT_bake_mesh",
    "WATERFALL_PT_curve_card_panel",
)


def _classes() -> list[type]:
    from .operators.bake import WATERFALL_OT_bake_mesh
    from .operators.preview import WATERFALL_OT_rebuild_preview
    from .operators.simulate import WATERFALL_OT_simulate_curve
    from .panel import WATERFALL_PT_curve_card_panel
    from .properties import WaterfallCurveSettings, WaterfallEmitterSettings

    return [
        WaterfallEmitterSettings,
        WaterfallCurveSettings,
        WATERFALL_OT_simulate_curve,
        WATERFALL_OT_rebuild_preview,
        WATERFALL_OT_bake_mesh,
        WATERFALL_PT_curve_card_panel,
    ]


def register() -> None:
    import bpy

    from .operators.preview import depsgraph_refresh

    classes = _classes()
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.waterfall_emitter = bpy.props.PointerProperty(type=classes[0])
    bpy.types.Object.waterfall_curve = bpy.props.PointerProperty(type=classes[1])
    if depsgraph_refresh not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(depsgraph_refresh)


def unregister() -> None:
    import bpy

    from .operators.preview import depsgraph_refresh

    if depsgraph_refresh in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(depsgraph_refresh)
    if hasattr(bpy.types.Object, "waterfall_curve"):
        del bpy.types.Object.waterfall_curve
    if hasattr(bpy.types.Object, "waterfall_emitter"):
        del bpy.types.Object.waterfall_emitter
    for cls in reversed(_classes()):
        bpy.utils.unregister_class(cls)
```

- [ ] **Step 3: Run the full core suite**

Run:

```powershell
pytest tests/core -v
```

Expected: PASS for all existing core tests. Blender code remains import-safe because `bpy` imports are guarded.

- [ ] **Step 4: Commit**

```powershell
git add addon/waterfall_tool/operators/simulate.py addon/waterfall_tool/operators/preview.py addon/waterfall_tool/operators/bake.py addon/waterfall_tool/panel.py addon/waterfall_tool/registration.py
git commit -m "feat: connect live preview operators"
```

---

### Task 10: Blender Smoke Script And Verification

**Files:**
- Create: `scripts/smoke_blender_addon.py`

- [ ] **Step 1: Create a Blender smoke script**

Create `scripts/smoke_blender_addon.py`:

```python
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import bpy

REPO_ROOT = Path(__file__).resolve().parents[1]
ADDON_ROOT = REPO_ROOT / "addon"
if str(ADDON_ROOT) not in sys.path:
    sys.path.insert(0, str(ADDON_ROOT))

import waterfall_tool

importlib.reload(waterfall_tool)
waterfall_tool.register()

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

emitter = bpy.data.objects.new("SmokeEmitter", None)
bpy.context.collection.objects.link(emitter)
bpy.context.view_layer.objects.active = emitter
emitter.select_set(True)
emitter.waterfall_emitter.speed = 6.0
emitter.waterfall_emitter.simulation_step_count = 12
bpy.ops.waterfall.simulate_curve()

curve = bpy.data.objects.get(emitter.waterfall_emitter.flow_curve_name)
assert curve is not None
assert curve.type == "CURVE"

bpy.context.view_layer.objects.active = curve
curve.select_set(True)
curve.waterfall_curve.start_width = 1.0
curve.waterfall_curve.end_width = 0.5
curve.waterfall_curve.curve_mode = "PHYSICS_ASSISTED"
bpy.ops.waterfall.rebuild_preview()

preview = bpy.data.objects.get(curve.waterfall_curve.preview_mesh_name)
assert preview is not None
assert preview.type == "MESH"
assert "UV0" in preview.data.uv_layers
assert "UV1_Speed" in preview.data.uv_layers

bpy.ops.waterfall.bake_mesh()
baked = bpy.data.objects.get(curve.waterfall_curve.baked_mesh_name)
assert baked is not None
assert baked.type == "MESH"
assert curve.waterfall_curve.preview_enabled is False

waterfall_tool.unregister()
print("waterfall smoke passed")
```

- [ ] **Step 2: Run the pure Python suite**

Run:

```powershell
pytest tests/core -v
```

Expected: PASS for all tests.

- [ ] **Step 3: Run the Blender smoke script**

Run after setting `BLENDER_EXE` to the local Blender executable path:

```powershell
& $env:BLENDER_EXE --background --python scripts/smoke_blender_addon.py
```

Expected: PASS with output containing `waterfall smoke passed`.

- [ ] **Step 4: Commit**

```powershell
git add scripts/smoke_blender_addon.py
git commit -m "test: add blender addon smoke script"
```

---

### Task 11: Final Verification Pass

**Files:**
- Modify only files that fail verification.

- [ ] **Step 1: Run the full Python suite**

Run:

```powershell
pytest tests/core -v
```

Expected: PASS for all tests.

- [ ] **Step 2: Run the Blender smoke suite**

Run:

```powershell
& $env:BLENDER_EXE --background --python scripts/smoke_blender_addon.py
```

Expected: PASS with output containing `waterfall smoke passed`.

- [ ] **Step 3: Inspect git status**

Run:

```powershell
git status --short
```

Expected: no uncommitted changes.

- [ ] **Step 4: If verification required fixes, commit the fixes**

Run only if Step 1 or Step 2 required code changes:

```powershell
git add addon tests scripts pyproject.toml .gitignore
git commit -m "fix: stabilize waterfall curve card tool"
```

Expected: a commit is created only when verification fixes changed tracked files.

---

## Self-Review Notes

- Spec coverage: The plan covers emitter-driven single-trajectory generation, object-property persistence, visible mesh collision probing, manual curve editing, physics-assisted curve reflow, curvature-adaptive sampling, stable frame propagation, X-card mesh construction, UV0 flow layout, UV1 speed packing, live preview rebuilds, baked mesh output, and preview auto-disable after bake.
- Scope check: The plan does not implement branching, multi-emitter batching, terrain generation, spray, fog, material graph generation, LOD, or global performance auto-degrade, matching the approved spec.
- Verification: Pure Python behavior is covered by `pytest tests/core -v`; Blender behavior is covered by `scripts/smoke_blender_addon.py`.
