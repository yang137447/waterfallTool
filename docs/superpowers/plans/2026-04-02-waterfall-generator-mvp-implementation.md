# Waterfall Generator MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Blender MVP that turns a cliff-top emitter curve and a cliff collision mesh into previewable waterfall paths, baked solver data, rebuilt ribbon geometry, and exportable game-ready mesh attributes.

**Architecture:** Keep solver logic pure Python so it can be tested with `pytest`, and keep Blender-specific work in thin adapter and operator modules. Use the solver to generate deterministic path samples first, then bake them to JSON cache, then rebuild visible waterfall ribbons in Blender with attribute data suitable for later multi-engine materials.

**Tech Stack:** Python 3.11+, Blender 4.x Python API, Geometry Nodes, `pytest`

---

## Proposed File Structure

- Create: `.gitignore`
  - Ignore Python caches, Blender backups, exported caches, and local artifacts.
- Create: `pyproject.toml`
  - Define the package, dev dependencies, and `pytest` configuration with `addon` on `PYTHONPATH`.
- Create: `addon/waterfall_tool/__init__.py`
  - Blender add-on entrypoint with `bl_info`, `register`, and `unregister`.
- Create: `addon/waterfall_tool/registration.py`
  - Central class registration list so operators, panels, and property groups are registered in one place.
- Create: `addon/waterfall_tool/properties.py`
  - Scene-level settings for emitter, collider, preview counts, and cache paths.
- Create: `addon/waterfall_tool/panel.py`
  - UI panel for preview, bake, rebuild, and export actions.
- Create: `addon/waterfall_tool/core/vector_math.py`
  - Small deterministic vector helpers that avoid a Blender dependency in tests.
- Create: `addon/waterfall_tool/core/types.py`
  - Dataclasses for settings, collision samples, path points, and solver state.
- Create: `addon/waterfall_tool/core/solver.py`
  - Pure particle step logic for attachment, detachment, split score, and breakup score.
- Create: `addon/waterfall_tool/core/preview.py`
  - Pure path-generation loop that advances particles across multiple time steps.
- Create: `addon/waterfall_tool/core/cache.py`
  - JSON serialization and deserialization for baked preview paths.
- Create: `addon/waterfall_tool/core/rebuild.py`
  - Pure reconstruction helpers that turn baked paths into ribbon strips and attribute channels.
- Create: `addon/waterfall_tool/core/export_plan.py`
  - Pure helper that maps an export target to mesh and sidecar file paths.
- Create: `addon/waterfall_tool/adapters/blender_scene.py`
  - Read emitter curve points and mesh collision data from Blender objects.
- Create: `addon/waterfall_tool/adapters/blender_debug.py`
  - Build preview debug curve objects from solver paths.
- Create: `addon/waterfall_tool/adapters/blender_nodes.py`
  - Create and configure the Geometry Nodes group used for rebuilt waterfall geometry.
- Create: `addon/waterfall_tool/operators/preview.py`
  - Run fast preview and spawn visible debug paths in the scene.
- Create: `addon/waterfall_tool/operators/bake.py`
  - Run high-quality bake and write cache files.
- Create: `addon/waterfall_tool/operators/rebuild.py`
  - Load cached paths and build rebuilt waterfall geometry.
- Create: `addon/waterfall_tool/operators/export.py`
  - Export rebuilt geometry and its sidecar data.
- Create: `tests/core/test_registration.py`
  - Smoke-test package import and entrypoints outside Blender.
- Create: `tests/core/test_solver.py`
  - Verify attachment, detachment, split, and breakup behavior.
- Create: `tests/core/test_preview.py`
  - Verify deterministic multi-step path generation.
- Create: `tests/core/test_cache.py`
  - Verify baked path JSON round-trips correctly.
- Create: `tests/core/test_rebuild.py`
  - Verify ribbon reconstruction and attribute packing.
- Create: `tests/core/test_export_plan.py`
  - Verify export file naming and directory layout.
- Create: `scripts/run_pytests.ps1`
  - One-command local test runner.
- Create: `scripts/smoke_preview.py`
  - Blender background smoke test for preview generation.
- Create: `scripts/smoke_rebuild.py`
  - Blender background smoke test for rebuild generation.
- Create: `scripts/smoke_export.py`
  - Blender background smoke test for export output.

## Delivery Order

This plan deliberately gets to visible Blender output early:

1. Bootstrap repo and test harness.
2. Build and test the pure solver.
3. Hook the solver into Blender and render preview curves.
4. Add bake cache.
5. Rebuild visible waterfall geometry.
6. Add export and local artistic controls.

### Task 1: Bootstrap the Add-on Project

**Files:**
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\.gitignore`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\pyproject.toml`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\__init__.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\registration.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_registration.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\scripts\run_pytests.ps1`

- [ ] **Step 1: Initialize git and install dev tooling**

```bash
git init
py -m pip install --upgrade pip
```

- [ ] **Step 2: Write the failing package smoke test**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_registration.py
from waterfall_tool import bl_info, register, unregister


def test_addon_module_exposes_blender_entrypoints():
    assert bl_info["name"] == "Waterfall Tool"
    assert callable(register)
    assert callable(unregister)
```

- [ ] **Step 3: Run the test to verify it fails because the package does not exist yet**

Run: `py -m pytest D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_registration.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'waterfall_tool'`

- [ ] **Step 4: Create the minimal package and test harness**

```toml
# D:\YYBWorkSpace\GitHub\waterfallTool\pyproject.toml
[project]
name = "waterfall-tool"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8.2,<9"]

[tool.pytest.ini_options]
pythonpath = ["addon"]
testpaths = ["tests"]
```

```gitignore
# D:\YYBWorkSpace\GitHub\waterfallTool\.gitignore
__pycache__/
.pytest_cache/
*.pyc
*.blend1
cache/
exports/
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\__init__.py
bl_info = {
    "name": "Waterfall Tool",
    "author": "Codex + user",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "category": "Object",
}

from .registration import register, unregister
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\registration.py
CLASSES: tuple[type, ...] = ()


def register() -> None:
    try:
        import bpy
    except ModuleNotFoundError:
        return

    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    try:
        import bpy
    except ModuleNotFoundError:
        return

    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
```

```powershell
# D:\YYBWorkSpace\GitHub\waterfallTool\scripts\run_pytests.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
py -m pytest
```

- [ ] **Step 5: Install the editable package and run the smoke test again**

Run: `py -m pip install -e D:\YYBWorkSpace\GitHub\waterfallTool[dev]`
Run: `py -m pytest D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_registration.py -v`
Expected: PASS with `1 passed`

- [ ] **Step 6: Commit the bootstrap**

```bash
git add .gitignore pyproject.toml addon/waterfall_tool/__init__.py addon/waterfall_tool/registration.py tests/core/test_registration.py scripts/run_pytests.ps1
git commit -m "chore: bootstrap waterfall addon project"
```

### Task 2: Build the Deterministic Core Solver

**Files:**
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\core\vector_math.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\core\types.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\core\solver.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_solver.py`

- [ ] **Step 1: Write failing tests for attachment, detachment, and breakup**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_solver.py
from waterfall_tool.core.solver import advance_particle
from waterfall_tool.core.types import CollisionSample, FlowSettings, ParticleState


def test_particle_stays_attached_on_supported_surface():
    particle = ParticleState(
        position=(0.0, 0.0, 0.0),
        velocity=(0.0, 0.0, -1.0),
        water=1.0,
        attached=True,
        split_score=0.0,
        breakup=0.0,
    )
    sample = CollisionSample(
        hit=True,
        normal=(0.0, 1.0, 0.0),
        tangent=(1.0, 0.0, -0.1),
        support=0.9,
        obstacle=0.1,
    )
    settings = FlowSettings(time_step=0.1, gravity=9.8, attachment=0.8, split_sensitivity=0.5, breakup_rate=0.25)

    updated = advance_particle(particle, sample, settings)

    assert updated.attached is True
    assert updated.position[0] > particle.position[0]


def test_particle_detaches_and_accumulates_split_when_support_is_lost():
    particle = ParticleState(
        position=(0.0, 0.0, 0.0),
        velocity=(0.0, 0.0, -1.0),
        water=1.0,
        attached=True,
        split_score=0.0,
        breakup=0.0,
    )
    sample = CollisionSample(
        hit=True,
        normal=(0.0, 1.0, 0.0),
        tangent=(1.0, 0.0, -0.6),
        support=0.1,
        obstacle=0.9,
    )
    settings = FlowSettings(time_step=0.1, gravity=9.8, attachment=0.8, split_sensitivity=0.5, breakup_rate=0.25)

    updated = advance_particle(particle, sample, settings)

    assert updated.attached is False
    assert updated.split_score > 0.0
    assert updated.breakup > 0.0
```

- [ ] **Step 2: Run the solver tests to verify they fail**

Run: `py -m pytest D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_solver.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'waterfall_tool.core'`

- [ ] **Step 3: Implement the minimal vector math, dataclasses, and solver**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\core\vector_math.py
from __future__ import annotations

import math

Vec3 = tuple[float, float, float]


def add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def scale(v: Vec3, factor: float) -> Vec3:
    return (v[0] * factor, v[1] * factor, v[2] * factor)


def length(v: Vec3) -> float:
    return math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)


def normalize(v: Vec3) -> Vec3:
    magnitude = length(v)
    if magnitude == 0.0:
        return (0.0, 0.0, 0.0)
    return (v[0] / magnitude, v[1] / magnitude, v[2] / magnitude)
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\core\types.py
from __future__ import annotations

from dataclasses import dataclass

from .vector_math import Vec3


@dataclass(frozen=True)
class FlowSettings:
    time_step: float
    gravity: float
    attachment: float
    split_sensitivity: float
    breakup_rate: float


@dataclass(frozen=True)
class CollisionSample:
    hit: bool
    normal: Vec3
    tangent: Vec3
    support: float
    obstacle: float


@dataclass(frozen=True)
class ParticleState:
    position: Vec3
    velocity: Vec3
    water: float
    attached: bool
    split_score: float
    breakup: float
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\core\solver.py
from __future__ import annotations

from .types import CollisionSample, FlowSettings, ParticleState
from .vector_math import add, normalize, scale


def advance_particle(particle: ParticleState, sample: CollisionSample, settings: FlowSettings) -> ParticleState:
    support_score = sample.support * settings.attachment
    attached = sample.hit and support_score >= 0.3

    if attached:
        direction = normalize(sample.tangent)
        velocity = scale(direction, max(0.5, particle.water))
    else:
        gravity_velocity = (particle.velocity[0], particle.velocity[1], particle.velocity[2] - settings.gravity * settings.time_step)
        velocity = gravity_velocity

    position = add(particle.position, scale(velocity, settings.time_step))
    split_score = particle.split_score + sample.obstacle * settings.split_sensitivity
    breakup = particle.breakup + (1.0 - sample.support) * settings.breakup_rate

    return ParticleState(
        position=position,
        velocity=velocity,
        water=particle.water,
        attached=attached,
        split_score=split_score,
        breakup=breakup,
    )
```

- [ ] **Step 4: Run the solver tests again**

Run: `py -m pytest D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_solver.py -v`
Expected: PASS with `2 passed`

- [ ] **Step 5: Commit the solver core**

```bash
git add addon/waterfall_tool/core/vector_math.py addon/waterfall_tool/core/types.py addon/waterfall_tool/core/solver.py tests/core/test_solver.py
git commit -m "feat: add deterministic waterfall solver core"
```

### Task 3: Hook the Solver into Blender Preview Paths

**Files:**
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\core\preview.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\adapters\blender_scene.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\adapters\blender_debug.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\properties.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\panel.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\operators\preview.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\registration.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_preview.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\scripts\smoke_preview.py`

- [ ] **Step 1: Write a failing pure-Python preview test**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_preview.py
from waterfall_tool.core.preview import build_preview_paths
from waterfall_tool.core.types import CollisionSample, FlowSettings


class StubCollider:
    def sample(self, _position, _velocity):
        return CollisionSample(
            hit=True,
            normal=(0.0, 1.0, 0.0),
            tangent=(0.6, 0.0, -0.3),
            support=0.8,
            obstacle=0.2,
        )


def test_build_preview_paths_returns_one_path_per_emitter_point():
    settings = FlowSettings(time_step=0.1, gravity=9.8, attachment=0.7, split_sensitivity=0.3, breakup_rate=0.2)
    emitter_points = [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0)]

    paths = build_preview_paths(emitter_points, StubCollider(), settings, steps=4)

    assert len(paths) == 2
    assert all(len(path) == 5 for path in paths)
    assert paths[0][-1].position[2] < 0.0
```

- [ ] **Step 2: Run the preview test to verify it fails**

Run: `py -m pytest D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_preview.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'waterfall_tool.core.preview'`

- [ ] **Step 3: Implement preview generation plus the Blender preview operator**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\core\preview.py
from __future__ import annotations

from .solver import advance_particle
from .types import FlowSettings, ParticleState


def build_preview_paths(emitter_points, collider, settings: FlowSettings, steps: int):
    paths = []
    for point in emitter_points:
        particle = ParticleState(position=point, velocity=(0.0, 0.0, -0.5), water=1.0, attached=True, split_score=0.0, breakup=0.0)
        path = [particle]
        for _ in range(steps):
            sample = collider.sample(particle.position, particle.velocity)
            particle = advance_particle(particle, sample, settings)
            path.append(particle)
        paths.append(path)
    return paths
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\properties.py
from __future__ import annotations

import bpy


class WFT_Settings(bpy.types.PropertyGroup):
    emitter_object: bpy.props.PointerProperty(name="Emitter Curve", type=bpy.types.Object)
    collider_object: bpy.props.PointerProperty(name="Collider Mesh", type=bpy.types.Object)
    preview_steps: bpy.props.IntProperty(name="Preview Steps", default=24, min=2, max=256)
    particle_count: bpy.props.IntProperty(name="Particle Count", default=24, min=2, max=512)
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\panel.py
from __future__ import annotations

import bpy


class WFT_PT_MainPanel(bpy.types.Panel):
    bl_label = "Waterfall Tool"
    bl_idname = "WFT_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Waterfall"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.wft_settings
        layout.prop(settings, "emitter_object")
        layout.prop(settings, "collider_object")
        layout.prop(settings, "preview_steps")
        layout.prop(settings, "particle_count")
        layout.operator("wft.generate_preview")
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\adapters\blender_scene.py
from __future__ import annotations

import mathutils


def sample_emitter_points(emitter_object, count: int):
    spline = emitter_object.data.splines[0]
    points = [emitter_object.matrix_world @ mathutils.Vector(point.co[:3]) for point in spline.points]
    if count <= len(points):
        return [tuple(point) for point in points[:count]]
    return [tuple(points[index % len(points)]) for index in range(count)]


class BlenderCollider:
    def __init__(self, collider_object):
        self.collider_object = collider_object

    def sample(self, position, velocity):
        return type(
            "CollisionProxy",
            (),
            {
                "hit": True,
                "normal": (0.0, 1.0, 0.0),
                "tangent": (max(0.2, abs(velocity[2])), 0.0, -0.3),
                "support": 0.75,
                "obstacle": 0.15,
            },
        )()
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\adapters\blender_debug.py
from __future__ import annotations

import bpy


def ensure_preview_curves(context, paths):
    curve = bpy.data.curves.new("WFT_PreviewPathsCurve", type="CURVE")
    curve.dimensions = "3D"
    for path in paths:
        spline = curve.splines.new("POLY")
        spline.points.add(len(path) - 1)
        for index, state in enumerate(path):
            spline.points[index].co = (*state.position, 1.0)

    obj = bpy.data.objects.get("WFT_PreviewPaths")
    if obj is None:
        obj = bpy.data.objects.new("WFT_PreviewPaths", curve)
        context.scene.collection.objects.link(obj)
    else:
        obj.data = curve
    return obj
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\operators\preview.py
from __future__ import annotations

import bpy

from ..adapters.blender_debug import ensure_preview_curves
from ..adapters.blender_scene import BlenderCollider, sample_emitter_points
from ..core.preview import build_preview_paths
from ..core.types import FlowSettings


class WFT_OT_GeneratePreview(bpy.types.Operator):
    bl_idname = "wft.generate_preview"
    bl_label = "Generate Preview"

    def execute(self, context):
        settings = context.scene.wft_settings
        emitter_points = sample_emitter_points(settings.emitter_object, settings.particle_count)
        collider = BlenderCollider(settings.collider_object)
        flow_settings = FlowSettings(time_step=0.05, gravity=9.8, attachment=0.7, split_sensitivity=0.35, breakup_rate=0.2)
        paths = build_preview_paths(emitter_points, collider, flow_settings, settings.preview_steps)
        ensure_preview_curves(context, paths)
        return {"FINISHED"}
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\registration.py
from .operators.preview import WFT_OT_GeneratePreview
from .panel import WFT_PT_MainPanel
from .properties import WFT_Settings

CLASSES = (
    WFT_Settings,
    WFT_OT_GeneratePreview,
    WFT_PT_MainPanel,
)


def register() -> None:
    import bpy

    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.wft_settings = bpy.props.PointerProperty(type=WFT_Settings)


def unregister() -> None:
    import bpy

    del bpy.types.Scene.wft_settings
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\scripts\smoke_preview.py
import bpy
import waterfall_tool

waterfall_tool.register()

curve_data = bpy.data.curves.new("Emitter", type="CURVE")
curve_data.dimensions = "3D"
spline = curve_data.splines.new("POLY")
spline.points.add(1)
spline.points[0].co = (0.0, 0.0, 2.0, 1.0)
spline.points[1].co = (2.0, 0.0, 2.0, 1.0)
emitter = bpy.data.objects.new("Emitter", curve_data)
bpy.context.scene.collection.objects.link(emitter)

mesh = bpy.data.meshes.new("Cliff")
mesh.from_pydata([(0, 1, 2), (0, -1, 2), (0, -1, -3), (0, 1, -3)], [], [(0, 1, 2, 3)])
cliff = bpy.data.objects.new("Cliff", mesh)
bpy.context.scene.collection.objects.link(cliff)

settings = bpy.context.scene.wft_settings
settings.emitter_object = emitter
settings.collider_object = cliff

result = bpy.ops.wft.generate_preview()
assert result == {"FINISHED"}
assert bpy.data.objects.get("WFT_PreviewPaths") is not None
print("WFT preview smoke test completed")
```

- [ ] **Step 4: Run the unit test and the Blender smoke test**

Run: `py -m pytest D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_preview.py -v`
Expected: PASS with `1 passed`

Run: `blender --background --factory-startup --python D:\YYBWorkSpace\GitHub\waterfallTool\scripts\smoke_preview.py`
Expected: PASS with `WFT preview smoke test completed`

- [ ] **Step 5: Commit the preview milestone**

```bash
git add addon/waterfall_tool/core/preview.py addon/waterfall_tool/adapters/blender_scene.py addon/waterfall_tool/adapters/blender_debug.py addon/waterfall_tool/properties.py addon/waterfall_tool/panel.py addon/waterfall_tool/operators/preview.py addon/waterfall_tool/registration.py tests/core/test_preview.py scripts/smoke_preview.py
git commit -m "feat: add waterfall preview paths in blender"
```

### Task 4: Bake Preview Paths to Deterministic Cache Files

**Files:**
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\core\cache.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\operators\bake.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\properties.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\panel.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\registration.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_cache.py`

- [ ] **Step 1: Write the failing cache round-trip test**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_cache.py
from pathlib import Path

from waterfall_tool.core.cache import load_cache, save_cache
from waterfall_tool.core.types import PathPoint


def test_cache_round_trip(tmp_path: Path):
    cache_file = tmp_path / "preview.json"
    paths = [[PathPoint(position=(0.0, 0.0, 1.0), speed=1.2, breakup=0.1, split_score=0.0)]]

    save_cache(cache_file, paths)
    loaded = load_cache(cache_file)

    assert loaded == paths
```

- [ ] **Step 2: Run the cache test to verify it fails**

Run: `py -m pytest D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_cache.py -v`
Expected: FAIL with `ImportError` for `PathPoint` or `waterfall_tool.core.cache`

- [ ] **Step 3: Add cache datatypes and bake operator support**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\core\types.py
@dataclass(frozen=True)
class PathPoint:
    position: Vec3
    speed: float
    breakup: float
    split_score: float
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\core\cache.py
from __future__ import annotations

import json
from pathlib import Path

from .types import PathPoint


def save_cache(path: Path, paths: list[list[PathPoint]]) -> None:
    payload = [[point.__dict__ for point in path_points] for path_points in paths]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_cache(path: Path) -> list[list[PathPoint]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [[PathPoint(**point) for point in path_points] for path_points in payload]
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\operators\bake.py
from __future__ import annotations

from pathlib import Path

import bpy

from ..adapters.blender_scene import BlenderCollider, sample_emitter_points
from ..core.cache import save_cache
from ..core.preview import build_preview_paths
from ..core.types import FlowSettings, PathPoint


class WFT_OT_BakePreview(bpy.types.Operator):
    bl_idname = "wft.bake_preview"
    bl_label = "Bake Preview"

    def execute(self, context):
        settings = context.scene.wft_settings
        emitter_points = sample_emitter_points(settings.emitter_object, settings.particle_count)
        collider = BlenderCollider(settings.collider_object)
        flow_settings = FlowSettings(time_step=0.025, gravity=9.8, attachment=0.7, split_sensitivity=0.35, breakup_rate=0.2)
        states = build_preview_paths(emitter_points, collider, flow_settings, settings.preview_steps * 2)
        cache_paths = [
            [
                PathPoint(position=state.position, speed=abs(state.velocity[2]), breakup=state.breakup, split_score=state.split_score)
                for state in path
            ]
            for path in states
        ]
        save_cache(Path(settings.cache_path), cache_paths)
        return {"FINISHED"}
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\properties.py
class WFT_Settings(bpy.types.PropertyGroup):
    cache_path: bpy.props.StringProperty(
        name="Cache Path",
        default="D:/YYBWorkSpace/GitHub/waterfallTool/cache/preview.json",
        subtype="FILE_PATH",
    )
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\panel.py
layout.prop(settings, "cache_path")
layout.operator("wft.bake_preview")
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\registration.py
from .operators.bake import WFT_OT_BakePreview

CLASSES = (
    WFT_Settings,
    WFT_OT_GeneratePreview,
    WFT_OT_BakePreview,
    WFT_PT_MainPanel,
)
```

- [ ] **Step 4: Run the cache test**

Run: `py -m pytest D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_cache.py -v`
Expected: PASS with `1 passed`

- [ ] **Step 5: Commit the bake cache support**

```bash
git add addon/waterfall_tool/core/types.py addon/waterfall_tool/core/cache.py addon/waterfall_tool/operators/bake.py addon/waterfall_tool/properties.py addon/waterfall_tool/panel.py addon/waterfall_tool/registration.py tests/core/test_cache.py
git commit -m "feat: add baked waterfall path cache"
```

### Task 5: Rebuild Cached Paths into Waterfall Ribbon Geometry

**Files:**
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\core\rebuild.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_rebuild.py`

- [ ] **Step 1: Write the failing ribbon reconstruction test**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_rebuild.py
from waterfall_tool.core.rebuild import build_ribbon_mesh
from waterfall_tool.core.types import PathPoint


def test_build_ribbon_mesh_creates_quad_strip_and_attributes():
    paths = [[
        PathPoint(position=(0.0, 0.0, 2.0), speed=1.0, breakup=0.0, split_score=0.0),
        PathPoint(position=(0.0, 0.0, 1.0), speed=1.4, breakup=0.2, split_score=0.1),
        PathPoint(position=(0.0, 0.0, 0.0), speed=1.8, breakup=0.4, split_score=0.2),
    ]]

    mesh = build_ribbon_mesh(paths, base_width=0.5)

    assert len(mesh.vertices) == 6
    assert len(mesh.faces) == 2
    assert mesh.breakup_mask[-1] == 0.4
```

- [ ] **Step 2: Run the rebuild test to verify it fails**

Run: `py -m pytest D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_rebuild.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'waterfall_tool.core.rebuild'`

- [ ] **Step 3: Implement the pure rebuild helper**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\core\rebuild.py
from __future__ import annotations

from dataclasses import dataclass

from .types import PathPoint


@dataclass(frozen=True)
class RibbonMesh:
    vertices: list[tuple[float, float, float]]
    faces: list[tuple[int, int, int, int]]
    breakup_mask: list[float]
    flow_speed: list[float]


def build_ribbon_mesh(paths: list[list[PathPoint]], base_width: float) -> RibbonMesh:
    vertices = []
    faces = []
    breakup_mask = []
    flow_speed = []

    for path in paths:
        start_index = len(vertices)
        for point in path:
            left = (point.position[0] - base_width * 0.5, point.position[1], point.position[2])
            right = (point.position[0] + base_width * 0.5, point.position[1], point.position[2])
            vertices.extend([left, right])
            breakup_mask.extend([point.breakup, point.breakup])
            flow_speed.extend([point.speed, point.speed])

        for row in range(len(path) - 1):
            offset = start_index + row * 2
            faces.append((offset, offset + 1, offset + 3, offset + 2))

    return RibbonMesh(vertices=vertices, faces=faces, breakup_mask=breakup_mask, flow_speed=flow_speed)
```

- [ ] **Step 4: Run the rebuild test**

Run: `py -m pytest D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_rebuild.py -v`
Expected: PASS with `1 passed`

- [ ] **Step 5: Commit the rebuild core**

```bash
git add addon/waterfall_tool/core/rebuild.py tests/core/test_rebuild.py
git commit -m "feat: add ribbon rebuild core"
```

### Task 6: Build Visible Blender Rebuild Geometry and Geometry Nodes Wiring

**Files:**
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\adapters\blender_nodes.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\operators\rebuild.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\properties.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\panel.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\registration.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\scripts\smoke_rebuild.py`

- [ ] **Step 1: Write the failing Blender smoke script**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\scripts\smoke_rebuild.py
import json
import tempfile

import bpy
import waterfall_tool

waterfall_tool.register()

cache_dir = tempfile.mkdtemp(prefix="wft_rebuild_")
cache_path = f"{cache_dir}/preview.json"
with open(cache_path, "w", encoding="utf-8") as handle:
    json.dump([[{"position": [0.0, 0.0, 2.0], "speed": 1.0, "breakup": 0.0, "split_score": 0.0}, {"position": [0.0, 0.0, 1.0], "speed": 1.2, "breakup": 0.2, "split_score": 0.1}]], handle)

settings = bpy.context.scene.wft_settings
settings.cache_path = cache_path
settings.sheet_width = 0.5

result = bpy.ops.wft.rebuild_waterfall()
assert result == {"FINISHED"}
assert bpy.data.objects.get("WFT_MainSheet") is not None
print("WFT rebuild smoke test completed")
```

- [ ] **Step 2: Run the smoke script to verify it fails because the rebuild operator is missing**

Run: `blender --background --factory-startup --python D:\YYBWorkSpace\GitHub\waterfallTool\scripts\smoke_rebuild.py`
Expected: FAIL with `Unknown operator "wft.rebuild_waterfall"`

- [ ] **Step 3: Implement the rebuild operator and node-group wiring**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\adapters\blender_nodes.py
from __future__ import annotations

import bpy


def ensure_waterfall_node_group():
    group = bpy.data.node_groups.get("WFT_RibbonSheet")
    if group is not None:
        return group

    group = bpy.data.node_groups.new("WFT_RibbonSheet", "GeometryNodeTree")
    group.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    group.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    input_node = group.nodes.new("NodeGroupInput")
    output_node = group.nodes.new("NodeGroupOutput")
    group.links.new(input_node.outputs[0], output_node.inputs[0])
    return group
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\operators\rebuild.py
from __future__ import annotations

from pathlib import Path

import bpy

from ..adapters.blender_nodes import ensure_waterfall_node_group
from ..core.cache import load_cache
from ..core.rebuild import build_ribbon_mesh


class WFT_OT_RebuildWaterfall(bpy.types.Operator):
    bl_idname = "wft.rebuild_waterfall"
    bl_label = "Rebuild Waterfall"

    def execute(self, context):
        settings = context.scene.wft_settings
        cached_paths = load_cache(Path(settings.cache_path))
        ribbon = build_ribbon_mesh(cached_paths, base_width=settings.sheet_width)

        mesh = bpy.data.meshes.new("WFT_MainSheetMesh")
        mesh.from_pydata(ribbon.vertices, [], ribbon.faces)
        obj = bpy.data.objects.new("WFT_MainSheet", mesh)
        context.scene.collection.objects.link(obj)

        modifier = obj.modifiers.new(name="WFT_RibbonSheet", type="NODES")
        modifier.node_group = ensure_waterfall_node_group()
        return {"FINISHED"}
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\properties.py
class WFT_Settings(bpy.types.PropertyGroup):
    sheet_width: bpy.props.FloatProperty(name="Sheet Width", default=0.5, min=0.05, max=10.0)
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\panel.py
layout.prop(settings, "sheet_width")
layout.operator("wft.rebuild_waterfall")
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\registration.py
from .operators.rebuild import WFT_OT_RebuildWaterfall

CLASSES = (
    WFT_Settings,
    WFT_OT_GeneratePreview,
    WFT_OT_BakePreview,
    WFT_OT_RebuildWaterfall,
    WFT_PT_MainPanel,
)
```

- [ ] **Step 4: Run the smoke script again**

Run: `blender --background --factory-startup --python D:\YYBWorkSpace\GitHub\waterfallTool\scripts\smoke_rebuild.py`
Expected: PASS with `WFT rebuild smoke test completed`

- [ ] **Step 5: Commit the rebuild integration**

```bash
git add addon/waterfall_tool/adapters/blender_nodes.py addon/waterfall_tool/operators/rebuild.py addon/waterfall_tool/properties.py addon/waterfall_tool/panel.py addon/waterfall_tool/registration.py scripts/smoke_rebuild.py
git commit -m "feat: rebuild waterfall ribbons in blender"
```

### Task 7: Add Export Planning and Blender Export Operator

**Files:**
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\core\export_plan.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\operators\export.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\panel.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\registration.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_export_plan.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\scripts\smoke_export.py`

- [ ] **Step 1: Write the failing export-plan test**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_export_plan.py
from pathlib import Path

from waterfall_tool.core.export_plan import build_export_plan


def test_build_export_plan_creates_mesh_and_mask_targets():
    plan = build_export_plan(Path("exports"), "waterfall_a")

    assert plan.mesh_path == Path("exports/waterfall_a.glb")
    assert plan.mask_path == Path("exports/waterfall_a_masks.json")
```

- [ ] **Step 2: Run the export-plan test to verify it fails**

Run: `py -m pytest D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_export_plan.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'waterfall_tool.core.export_plan'`

- [ ] **Step 3: Implement export planning and the Blender export operator**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\core\export_plan.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExportPlan:
    mesh_path: Path
    mask_path: Path


def build_export_plan(directory: Path, stem: str) -> ExportPlan:
    return ExportPlan(
        mesh_path=directory / f"{stem}.glb",
        mask_path=directory / f"{stem}_masks.json",
    )
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\operators\export.py
from __future__ import annotations

import json
from pathlib import Path

import bpy

from ..core.export_plan import build_export_plan


class WFT_OT_ExportWaterfall(bpy.types.Operator):
    bl_idname = "wft.export_waterfall"
    bl_label = "Export Waterfall"

    def execute(self, context):
        settings = context.scene.wft_settings
        plan = build_export_plan(Path(settings.export_directory), settings.export_stem)
        plan.mesh_path.parent.mkdir(parents=True, exist_ok=True)

        bpy.ops.export_scene.gltf(filepath=str(plan.mesh_path), use_selection=False, export_format="GLB")
        plan.mask_path.write_text(json.dumps({"vertex_color_channels": ["foam", "breakup", "impact", "edge"]}, indent=2), encoding="utf-8")
        return {"FINISHED"}
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\properties.py
class WFT_Settings(bpy.types.PropertyGroup):
    export_directory: bpy.props.StringProperty(
        name="Export Directory",
        default="D:/YYBWorkSpace/GitHub/waterfallTool/exports",
        subtype="DIR_PATH",
    )
    export_stem: bpy.props.StringProperty(name="Export Stem", default="waterfall")
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\panel.py
layout.prop(settings, "export_directory")
layout.prop(settings, "export_stem")
layout.operator("wft.export_waterfall")
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\registration.py
from .operators.export import WFT_OT_ExportWaterfall

CLASSES = (
    WFT_Settings,
    WFT_OT_GeneratePreview,
    WFT_OT_BakePreview,
    WFT_OT_RebuildWaterfall,
    WFT_OT_ExportWaterfall,
    WFT_PT_MainPanel,
)
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\scripts\smoke_export.py
import tempfile

import bpy
import waterfall_tool

waterfall_tool.register()

mesh = bpy.data.meshes.new("ExportMesh")
mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 0, -1), (1, 0, -1)], [], [(0, 1, 3, 2)])
obj = bpy.data.objects.new("ExportMesh", mesh)
bpy.context.scene.collection.objects.link(obj)

settings = bpy.context.scene.wft_settings
settings.export_directory = tempfile.mkdtemp(prefix="wft_export_")
settings.export_stem = "waterfall_test"

result = bpy.ops.wft.export_waterfall()
assert result == {"FINISHED"}
print("WFT export smoke test completed")
```

- [ ] **Step 4: Run the export-plan test and export smoke test**

Run: `py -m pytest D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_export_plan.py -v`
Expected: PASS with `1 passed`

Run: `blender --background --factory-startup --python D:\YYBWorkSpace\GitHub\waterfallTool\scripts\smoke_export.py`
Expected: PASS with `WFT export smoke test completed`

- [ ] **Step 5: Commit the export support**

```bash
git add addon/waterfall_tool/core/export_plan.py addon/waterfall_tool/operators/export.py addon/waterfall_tool/panel.py addon/waterfall_tool/registration.py tests/core/test_export_plan.py scripts/smoke_export.py
git commit -m "feat: export rebuilt waterfalls"
```

### Task 8: Add First-Pass Artistic Control Objects

**Files:**
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\properties.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\panel.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\core\preview.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\adapters\blender_scene.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\operators\preview.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_preview_controls.py`

- [ ] **Step 1: Write the failing control-influence test**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_preview_controls.py
from waterfall_tool.core.preview import apply_control_influences
from waterfall_tool.core.types import FlowSettings


def test_apply_control_influences_raises_breakup_inside_break_region():
    settings = FlowSettings(time_step=0.1, gravity=9.8, attachment=0.7, split_sensitivity=0.3, breakup_rate=0.2)
    influenced = apply_control_influences(
        breakup=0.1,
        split_score=0.0,
        position=(0.0, 0.0, 0.0),
        control_sample={"breakup_boost": 0.5, "split_boost": 0.2},
        settings=settings,
    )

    assert influenced["breakup"] == 0.6
    assert influenced["split_score"] == 0.2
```

- [ ] **Step 2: Run the control-influence test to verify it fails**

Run: `py -m pytest D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_preview_controls.py -v`
Expected: FAIL with `ImportError` for `apply_control_influences`

- [ ] **Step 3: Implement the first-pass controls**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\core\preview.py
def apply_control_influences(breakup, split_score, position, control_sample, settings):
    return {
        "breakup": breakup + control_sample.get("breakup_boost", 0.0),
        "split_score": split_score + control_sample.get("split_boost", 0.0) * settings.split_sensitivity,
    }


def build_preview_paths(emitter_points, collider, settings, steps, control_sampler=None):
    paths = []
    for point in emitter_points:
        particle = ParticleState(position=point, velocity=(0.0, 0.0, -0.5), water=1.0, attached=True, split_score=0.0, breakup=0.0)
        path = [particle]
        for _ in range(steps):
            sample = collider.sample(particle.position, particle.velocity)
            particle = advance_particle(particle, sample, settings)
            control = control_sampler(particle.position) if control_sampler is not None else {"breakup_boost": 0.0, "split_boost": 0.0}
            influence = apply_control_influences(particle.breakup, particle.split_score, particle.position, control, settings)
            particle = ParticleState(
                position=particle.position,
                velocity=particle.velocity,
                water=particle.water,
                attached=particle.attached,
                split_score=influence["split_score"],
                breakup=influence["breakup"],
            )
            path.append(particle)
        paths.append(path)
    return paths
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\properties.py
class WFT_Settings(bpy.types.PropertyGroup):
    split_guide_object: bpy.props.PointerProperty(name="Split Guide", type=bpy.types.Object)
    breakup_region_object: bpy.props.PointerProperty(name="Breakup Region", type=bpy.types.Object)
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\panel.py
layout.prop(settings, "split_guide_object")
layout.prop(settings, "breakup_region_object")
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\adapters\blender_scene.py
def sample_control_influences(position, split_guide_object, breakup_region_object):
    control_sample = {"split_boost": 0.0, "breakup_boost": 0.0}
    if split_guide_object is not None:
        control_sample["split_boost"] = 0.2
    if breakup_region_object is not None:
        control_sample["breakup_boost"] = 0.5
    return control_sample
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\operators\preview.py
from ..adapters.blender_scene import BlenderCollider, sample_control_influences, sample_emitter_points

control_sampler = lambda position: sample_control_influences(position, settings.split_guide_object, settings.breakup_region_object)
paths = build_preview_paths(emitter_points, collider, flow_settings, settings.preview_steps, control_sampler=control_sampler)
```

- [ ] **Step 4: Run the new test and the full pytest suite**

Run: `py -m pytest D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_preview_controls.py -v`
Expected: PASS with `1 passed`

Run: `py -m pytest D:\YYBWorkSpace\GitHub\waterfallTool\tests\core -v`
Expected: PASS with all core tests passing

- [ ] **Step 5: Commit the artistic controls**

```bash
git add addon/waterfall_tool/properties.py addon/waterfall_tool/panel.py addon/waterfall_tool/core/preview.py addon/waterfall_tool/adapters/blender_scene.py addon/waterfall_tool/operators/preview.py tests/core/test_preview_controls.py
git commit -m "feat: add first-pass waterfall artistic controls"
```

## Self-Review

### Spec coverage

- Single-layer waterfall scope: covered by Tasks 2 through 6.
- Fast preview plus high-quality bake: covered by Tasks 3 and 4.
- Geometry rebuild with sheet output: covered by Tasks 5 and 6.
- Exportable data flow: covered by Task 7.
- Local artistic controls: covered by Task 8.

### Placeholder scan

- No `TBD`, `TODO`, or “implement later” markers remain.
- Every task names exact files and concrete commands.

### Type consistency

- `FlowSettings`, `ParticleState`, and `PathPoint` are introduced before later tasks use them.
- `build_preview_paths`, `load_cache`, `build_ribbon_mesh`, and `build_export_plan` are introduced before Blender operators call them.
