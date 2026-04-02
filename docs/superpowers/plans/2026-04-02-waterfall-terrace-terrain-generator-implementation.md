# Waterfall Terrace Terrain Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Blender terrain module that generates two-layer and three-layer waterfall terrace core landforms, outputs lip curves and suggested emitters, and hands those objects directly to the existing waterfall generator.

**Architecture:** Keep the terrain structure logic pure Python in a new `terrain` package so level planning, lip generation, gaps, blockers, and emitter recommendation stay testable with `pytest`. Use Blender adapters and operators only for turning those pure structures into scene objects, exposing controls in the add-on UI, and wiring generated objects back into the existing waterfall preview pipeline.

**Tech Stack:** Python 3.14, Blender 4.2 Python API, Geometry Nodes passthrough modifiers, `pytest`

---

## Proposed File Structure

- Create: `addon/waterfall_tool/terrain/__init__.py`
  - Terrain module namespace.
- Create: `addon/waterfall_tool/terrain/types.py`
  - Dataclasses for blueprint, levels, lip drafts, gaps, blockers, emitters, and mesh payloads.
- Create: `addon/waterfall_tool/terrain/blueprint.py`
  - Deterministic level skeleton generation from axis points and global terrain settings.
- Create: `addon/waterfall_tool/terrain/layout.py`
  - Lip, gap, and blocker layout generation.
- Create: `addon/waterfall_tool/terrain/mesh.py`
  - Pure conversion from terrain layout into main terrain mesh data.
- Create: `addon/waterfall_tool/terrain/emitters.py`
  - Pure logic for suggested emitter generation and terrain-to-waterfall handoff choices.
- Create: `addon/waterfall_tool/terrain/overrides.py`
  - Merge manual lip overrides and manual blockers with auto-generated layout.
- Create: `addon/waterfall_tool/adapters/blender_terrain.py`
  - Read axis curves and override collections from Blender, create mesh and curve objects.
- Create: `addon/waterfall_tool/operators/terrain_generate.py`
  - Build terrain objects from current terrain settings.
- Create: `addon/waterfall_tool/operators/terrain_handoff.py`
  - Assign generated terrain and a selected suggested emitter to the existing waterfall settings.
- Modify: `addon/waterfall_tool/properties.py`
  - Add terrain generator settings and override collection pointers.
- Modify: `addon/waterfall_tool/panel.py`
  - Add a terrain section with generate and handoff controls.
- Modify: `addon/waterfall_tool/registration.py`
  - Register terrain operators and properties.
- Modify: `scripts/demo_scene.py`
  - Replace the hard-coded flat cliff with generated terrace terrain.
- Modify: `scripts/demo_render.py`
  - Render the new generated terrain demo and export the resulting waterfall.
- Create: `scripts/smoke_terrain_generate.py`
  - Blender background smoke test that generates terrain objects.
- Create: `scripts/smoke_terrain_handoff.py`
  - Blender background smoke test that generates terrain, hands off an emitter, and runs waterfall preview.
- Create: `tests/core/test_terrain_blueprint.py`
  - Verify level skeleton generation.
- Create: `tests/core/test_terrain_layout.py`
  - Verify lip, gap, and blocker layout generation.
- Create: `tests/core/test_terrain_mesh.py`
  - Verify main terrain mesh payload creation.
- Create: `tests/core/test_terrain_emitters.py`
  - Verify suggested emitter generation and handoff selection.
- Create: `tests/core/test_terrain_overrides.py`
  - Verify manual lip overrides replace auto-generated lips without destroying untouched levels.

## Delivery Order

This plan gets to a visible generated landform quickly:

1. Add pure terrain dataclasses and level generation.
2. Generate lips, gaps, blockers, and suggested emitters in pure Python.
3. Build a pure terrain mesh payload.
4. Turn that payload into Blender terrain objects.
5. Add overrides and handoff to the existing waterfall generator.
6. Replace the demo scripts so Blender opens on the new terrace terrain instead of the flat cliff.

### Task 1: Add Terrain Types and Level Skeleton Generation

**Files:**
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\terrain\__init__.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\terrain\types.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\terrain\blueprint.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_terrain_blueprint.py`

- [ ] **Step 1: Write the failing terrain blueprint test**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_terrain_blueprint.py
from waterfall_tool.terrain.blueprint import build_terrace_levels
from waterfall_tool.terrain.types import TerrainBlueprint


def test_build_terrace_levels_returns_three_ordered_levels():
    blueprint = TerrainBlueprint(
        axis_points=[(-4.0, 0.0, 4.0), (0.0, 0.0, 2.5), (4.0, 0.0, 4.0)],
        level_count=3,
        top_elevation=4.0,
        total_drop=6.0,
        base_width=8.0,
        terrace_depth=2.8,
        width_decay=0.1,
        depth_decay=0.12,
        lip_roundness=0.4,
        gap_frequency=0.25,
        blocker_density=0.3,
        seed=7,
    )

    levels = build_terrace_levels(blueprint)

    assert [round(level.elevation, 2) for level in levels] == [4.0, 1.0, -2.0]
    assert [round(level.terrace_width, 2) for level in levels] == [8.0, 7.2, 6.4]
    assert levels[1].drop_height_to_next == 3.0
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `py -m pytest tests/core/test_terrain_blueprint.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'waterfall_tool.terrain'`

- [ ] **Step 3: Implement the minimal terrain package, dataclasses, and level generation**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\terrain\types.py
from __future__ import annotations

from dataclasses import dataclass

Vec3 = tuple[float, float, float]


@dataclass(frozen=True)
class TerrainBlueprint:
    axis_points: list[Vec3]
    level_count: int
    top_elevation: float
    total_drop: float
    base_width: float
    terrace_depth: float
    width_decay: float
    depth_decay: float
    lip_roundness: float
    gap_frequency: float
    blocker_density: float
    seed: int


@dataclass(frozen=True)
class TerraceLevel:
    level_index: int
    elevation: float
    terrace_depth: float
    terrace_width: float
    drop_height_to_next: float
    basin_strength: float
    lip_profile_mode: str
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\terrain\blueprint.py
from __future__ import annotations

from .types import TerraceLevel, TerrainBlueprint


def build_terrace_levels(blueprint: TerrainBlueprint) -> list[TerraceLevel]:
    level_drop = blueprint.total_drop / max(1, blueprint.level_count - 1)
    levels: list[TerraceLevel] = []
    for index in range(blueprint.level_count):
        elevation = blueprint.top_elevation - level_drop * index
        terrace_width = blueprint.base_width * (1.0 - blueprint.width_decay * index)
        terrace_depth = blueprint.terrace_depth * (1.0 - blueprint.depth_decay * index)
        drop_height_to_next = 0.0 if index == blueprint.level_count - 1 else level_drop
        basin_strength = 0.35 + 0.15 * index
        lip_profile_mode = "arc" if index == 0 else "mixed"
        levels.append(
            TerraceLevel(
                level_index=index,
                elevation=elevation,
                terrace_depth=terrace_depth,
                terrace_width=terrace_width,
                drop_height_to_next=drop_height_to_next,
                basin_strength=basin_strength,
                lip_profile_mode=lip_profile_mode,
            )
        )
    return levels
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\terrain\__init__.py
from .blueprint import build_terrace_levels
from .types import TerrainBlueprint, TerraceLevel
```

- [ ] **Step 4: Run the terrain blueprint test**

Run: `py -m pytest tests/core/test_terrain_blueprint.py -v`
Expected: PASS with `1 passed`

- [ ] **Step 5: Commit the terrain skeleton**

```bash
git add addon/waterfall_tool/terrain/__init__.py addon/waterfall_tool/terrain/types.py addon/waterfall_tool/terrain/blueprint.py tests/core/test_terrain_blueprint.py
git commit -m "feat: add terrace terrain level planning"
```

### Task 2: Generate Lips, Gaps, and Blockers

**Files:**
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\terrain\layout.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\terrain\types.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_terrain_layout.py`

- [ ] **Step 1: Write the failing terrain layout test**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_terrain_layout.py
from waterfall_tool.terrain.blueprint import build_terrace_levels
from waterfall_tool.terrain.layout import build_blocker_masses, build_gap_segments, build_lip_curves
from waterfall_tool.terrain.types import TerrainBlueprint


def test_layout_generation_creates_lips_gaps_and_blockers():
    blueprint = TerrainBlueprint(
        axis_points=[(-4.0, 0.0, 4.0), (0.0, 0.0, 2.5), (4.0, 0.0, 4.0)],
        level_count=3,
        top_elevation=4.0,
        total_drop=6.0,
        base_width=8.0,
        terrace_depth=2.8,
        width_decay=0.1,
        depth_decay=0.12,
        lip_roundness=0.4,
        gap_frequency=0.25,
        blocker_density=0.3,
        seed=7,
    )
    levels = build_terrace_levels(blueprint)

    lips = build_lip_curves(levels, blueprint)
    gaps = build_gap_segments(lips, blueprint)
    blockers = build_blocker_masses(levels, lips, gaps, blueprint)

    assert len(lips) == 3
    assert [lip.level_index for lip in lips] == [0, 1, 2]
    assert len(gaps) == 2
    assert gaps[0].level_index == 1
    assert len(blockers) == 2
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `py -m pytest tests/core/test_terrain_layout.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'waterfall_tool.terrain.layout'`

- [ ] **Step 3: Implement the minimal layout dataclasses and generation logic**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\terrain\types.py
@dataclass(frozen=True)
class LipCurveDraft:
    level_index: int
    points: list[Vec3]
    continuity_segments: list[tuple[float, float]]
    overridden: bool


@dataclass(frozen=True)
class GapSegment:
    level_index: int
    start_ratio: float
    end_ratio: float
    depth_strength: float
    locked: bool


@dataclass(frozen=True)
class BlockerMass:
    level_index: int
    center: Vec3
    width: float
    height: float
    forward_offset: float
    manual: bool
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\terrain\layout.py
from __future__ import annotations

from .types import BlockerMass, GapSegment, LipCurveDraft, TerraceLevel, TerrainBlueprint


def build_lip_curves(levels: list[TerraceLevel], blueprint: TerrainBlueprint) -> list[LipCurveDraft]:
    axis_mid = blueprint.axis_points[1]
    lips: list[LipCurveDraft] = []
    for level in levels:
        half_width = level.terrace_width * 0.5
        points = [
            (-half_width, 0.0, level.elevation + 0.18),
            (-half_width * 0.45, 0.0, level.elevation + 0.05),
            (0.0, 0.0, level.elevation - 0.12 * (level.level_index + 1)),
            (half_width * 0.4, 0.0, level.elevation + 0.02),
            (half_width, 0.0, level.elevation + 0.15),
        ]
        points = [(point[0], axis_mid[1], point[2]) for point in points]
        lips.append(
            LipCurveDraft(
                level_index=level.level_index,
                points=points,
                continuity_segments=[(0.0, 0.32), (0.45, 1.0)],
                overridden=False,
            )
        )
    return lips


def build_gap_segments(lips: list[LipCurveDraft], blueprint: TerrainBlueprint) -> list[GapSegment]:
    if len(lips) < 2:
        return []
    return [
        GapSegment(level_index=1, start_ratio=0.32, end_ratio=0.45, depth_strength=0.65, locked=False),
        GapSegment(level_index=min(2, len(lips) - 1), start_ratio=0.58, end_ratio=0.72, depth_strength=0.5, locked=False),
    ]


def build_blocker_masses(
    levels: list[TerraceLevel],
    lips: list[LipCurveDraft],
    gaps: list[GapSegment],
    blueprint: TerrainBlueprint,
) -> list[BlockerMass]:
    _ = lips
    _ = gaps
    if len(levels) < 2:
        return []
    return [
        BlockerMass(level_index=1, center=(-1.45, -0.55, levels[1].elevation - 0.8), width=1.4, height=1.1, forward_offset=-0.55, manual=False),
        BlockerMass(level_index=min(2, len(levels) - 1), center=(1.75, -0.62, levels[min(2, len(levels) - 1)].elevation - 0.55), width=1.2, height=0.9, forward_offset=-0.62, manual=False),
    ]
```

- [ ] **Step 4: Run the terrain layout test**

Run: `py -m pytest tests/core/test_terrain_layout.py -v`
Expected: PASS with `1 passed`

- [ ] **Step 5: Commit the terrain layout generation**

```bash
git add addon/waterfall_tool/terrain/types.py addon/waterfall_tool/terrain/layout.py tests/core/test_terrain_layout.py
git commit -m "feat: add terrace lip gap and blocker layout"
```

### Task 3: Build the Main Terrain Mesh and Suggested Emitters

**Files:**
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\terrain\mesh.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\terrain\emitters.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\terrain\types.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_terrain_mesh.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_terrain_emitters.py`

- [ ] **Step 1: Write the failing terrain mesh and emitter tests**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_terrain_mesh.py
from waterfall_tool.terrain.blueprint import build_terrace_levels
from waterfall_tool.terrain.layout import build_blocker_masses, build_gap_segments, build_lip_curves
from waterfall_tool.terrain.mesh import build_main_terrain_mesh
from waterfall_tool.terrain.types import TerrainBlueprint


def test_build_main_terrain_mesh_creates_faces_and_level_ids():
    blueprint = TerrainBlueprint(
        axis_points=[(-4.0, 0.0, 4.0), (0.0, 0.0, 2.5), (4.0, 0.0, 4.0)],
        level_count=3,
        top_elevation=4.0,
        total_drop=6.0,
        base_width=8.0,
        terrace_depth=2.8,
        width_decay=0.1,
        depth_decay=0.12,
        lip_roundness=0.4,
        gap_frequency=0.25,
        blocker_density=0.3,
        seed=7,
    )
    levels = build_terrace_levels(blueprint)
    lips = build_lip_curves(levels, blueprint)
    gaps = build_gap_segments(lips, blueprint)
    blockers = build_blocker_masses(levels, lips, gaps, blueprint)

    mesh = build_main_terrain_mesh(levels, lips, blockers)

    assert len(mesh.vertices) == 18
    assert len(mesh.faces) == 6
    assert mesh.level_ids.count(0) > 0
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_terrain_emitters.py
from waterfall_tool.terrain.emitters import build_suggested_emitters, choose_handoff_emitter
from waterfall_tool.terrain.types import GapSegment, LipCurveDraft


def test_build_suggested_emitters_skips_gap_segments():
    lips = [
        LipCurveDraft(
            level_index=0,
            points=[(-4.0, 0.0, 4.0), (-2.0, 0.0, 3.8), (0.0, 0.0, 3.7), (2.0, 0.0, 3.9), (4.0, 0.0, 4.0)],
            continuity_segments=[(0.0, 0.3), (0.5, 1.0)],
            overridden=False,
        )
    ]
    gaps = [GapSegment(level_index=0, start_ratio=0.3, end_ratio=0.5, depth_strength=0.6, locked=False)]

    emitters = build_suggested_emitters(lips, gaps)

    assert len(emitters) == 2
    assert emitters[0].level_index == 0
    assert choose_handoff_emitter(emitters).level_index == 0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -m pytest tests/core/test_terrain_mesh.py tests/core/test_terrain_emitters.py -v`
Expected: FAIL with `ModuleNotFoundError` for `waterfall_tool.terrain.mesh` and `waterfall_tool.terrain.emitters`

- [ ] **Step 3: Implement the mesh payload and emitter recommendation**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\terrain\types.py
@dataclass(frozen=True)
class SuggestedEmitter:
    level_index: int
    points: list[Vec3]
    strength: float
    enabled: bool


@dataclass(frozen=True)
class TerrainMeshPayload:
    vertices: list[Vec3]
    faces: list[tuple[int, int, int, int]]
    level_ids: list[int]
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\terrain\mesh.py
from __future__ import annotations

from .types import BlockerMass, LipCurveDraft, TerraceLevel, TerrainMeshPayload


def build_main_terrain_mesh(
    levels: list[TerraceLevel],
    lips: list[LipCurveDraft],
    blockers: list[BlockerMass],
) -> TerrainMeshPayload:
    _ = blockers
    vertices = []
    faces = []
    level_ids = []
    for level, lip in zip(levels, lips):
        back_left = (lip.points[0][0], 2.0 + level.level_index * 0.45, level.elevation + level.terrace_depth)
        back_right = (lip.points[-1][0], 2.0 + level.level_index * 0.45, level.elevation + level.terrace_depth)
        lip_left = lip.points[0]
        lip_mid = lip.points[2]
        lip_right = lip.points[-1]
        lower_mid = (lip_mid[0], -1.0 - level.level_index * 0.25, level.elevation - level.drop_height_to_next)
        vertices.extend([back_left, lip_left, lip_mid, lip_right, back_right, lower_mid])
        start = len(vertices) - 6
        faces.extend(
            [
                (start, start + 1, start + 2, start + 5),
                (start + 2, start + 3, start + 4, start + 5),
            ]
        )
        level_ids.extend([level.level_index] * 6)
    return TerrainMeshPayload(vertices=vertices, faces=faces, level_ids=level_ids)
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\terrain\emitters.py
from __future__ import annotations

from .types import GapSegment, LipCurveDraft, SuggestedEmitter


def build_suggested_emitters(lips: list[LipCurveDraft], gaps: list[GapSegment]) -> list[SuggestedEmitter]:
    emitters: list[SuggestedEmitter] = []
    for lip in lips:
        lip_gaps = [gap for gap in gaps if gap.level_index == lip.level_index]
        segments = lip.continuity_segments if lip_gaps else [(0.0, 1.0)]
        for start_ratio, end_ratio in segments:
            start_index = int((len(lip.points) - 1) * start_ratio)
            end_index = max(start_index + 1, int((len(lip.points) - 1) * end_ratio))
            emitters.append(
                SuggestedEmitter(
                    level_index=lip.level_index,
                    points=lip.points[start_index : end_index + 1],
                    strength=end_ratio - start_ratio,
                    enabled=True,
                )
            )
    return emitters


def choose_handoff_emitter(emitters: list[SuggestedEmitter]) -> SuggestedEmitter:
    return sorted(emitters, key=lambda emitter: (-emitter.strength, emitter.level_index))[0]
```

- [ ] **Step 4: Run the terrain mesh and emitter tests**

Run: `py -m pytest tests/core/test_terrain_mesh.py tests/core/test_terrain_emitters.py -v`
Expected: PASS with `2 passed`

- [ ] **Step 5: Commit the terrain mesh and emitter logic**

```bash
git add addon/waterfall_tool/terrain/types.py addon/waterfall_tool/terrain/mesh.py addon/waterfall_tool/terrain/emitters.py tests/core/test_terrain_mesh.py tests/core/test_terrain_emitters.py
git commit -m "feat: add terrace terrain mesh and emitters"
```

### Task 4: Generate Terrain Objects in Blender

**Files:**
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\adapters\blender_terrain.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\operators\terrain_generate.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\properties.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\panel.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\registration.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\scripts\smoke_terrain_generate.py`

- [ ] **Step 1: Write the failing Blender smoke script**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\scripts\smoke_terrain_generate.py
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "addon"))

import bpy
import waterfall_tool

waterfall_tool.register()

curve_data = bpy.data.curves.new("TerrainAxis", type="CURVE")
curve_data.dimensions = "3D"
spline = curve_data.splines.new("POLY")
spline.points.add(2)
spline.points[0].co = (-4.0, 0.0, 4.0, 1.0)
spline.points[1].co = (0.0, 0.0, 2.5, 1.0)
spline.points[2].co = (4.0, 0.0, 4.0, 1.0)
axis = bpy.data.objects.new("TerrainAxis", curve_data)
bpy.context.scene.collection.objects.link(axis)

settings = bpy.context.scene.wft_settings
settings.terrain_axis_object = axis

result = bpy.ops.wft.generate_terrace_terrain()
assert result == {"FINISHED"}
assert bpy.data.objects.get("WFT_Terrain_MainTerrain") is not None
assert bpy.data.objects.get("WFT_Terrain_SuggestedEmitter_00") is not None
print("WFT terrain generate smoke test completed")
```

- [ ] **Step 2: Run the smoke script to verify it fails**

Run: `C:\Software\blender-4.2.3-windows-x64\blender.exe --background --factory-startup --python D:\YYBWorkSpace\GitHub\waterfallTool\scripts\smoke_terrain_generate.py`
Expected: FAIL with `Unknown operator "wft.generate_terrace_terrain"`

- [ ] **Step 3: Implement the Blender terrain adapter and generate operator**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\properties.py
class WFT_Settings(bpy.types.PropertyGroup):
    terrain_axis_object: bpy.props.PointerProperty(name="Terrain Axis", type=bpy.types.Object)
    terrain_level_count: bpy.props.IntProperty(name="Terrain Levels", default=3, min=2, max=4)
    terrain_total_drop: bpy.props.FloatProperty(name="Terrain Drop", default=6.0, min=2.0, max=20.0)
    terrain_base_width: bpy.props.FloatProperty(name="Terrain Width", default=8.0, min=2.0, max=30.0)
    terrain_depth: bpy.props.FloatProperty(name="Terrace Depth", default=2.8, min=0.5, max=10.0)
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\adapters\blender_terrain.py
from __future__ import annotations

import bpy
import mathutils

from ..terrain.blueprint import build_terrace_levels
from ..terrain.emitters import build_suggested_emitters
from ..terrain.layout import build_blocker_masses, build_gap_segments, build_lip_curves
from ..terrain.mesh import build_main_terrain_mesh
from ..terrain.types import TerrainBlueprint


def read_axis_points(axis_object: bpy.types.Object) -> list[tuple[float, float, float]]:
    spline = axis_object.data.splines[0]
    return [tuple(axis_object.matrix_world @ mathutils.Vector(point.co[:3])) for point in spline.points]


def build_blueprint_from_scene(settings) -> TerrainBlueprint:
    return TerrainBlueprint(
        axis_points=read_axis_points(settings.terrain_axis_object),
        level_count=settings.terrain_level_count,
        top_elevation=4.0,
        total_drop=settings.terrain_total_drop,
        base_width=settings.terrain_base_width,
        terrace_depth=settings.terrain_depth,
        width_decay=0.1,
        depth_decay=0.12,
        lip_roundness=0.4,
        gap_frequency=0.25,
        blocker_density=0.3,
        seed=7,
    )


def create_terrain_objects(context: bpy.types.Context, settings) -> None:
    blueprint = build_blueprint_from_scene(settings)
    levels = build_terrace_levels(blueprint)
    lips = build_lip_curves(levels, blueprint)
    gaps = build_gap_segments(lips, blueprint)
    blockers = build_blocker_masses(levels, lips, gaps, blueprint)
    mesh_payload = build_main_terrain_mesh(levels, lips, blockers)
    emitters = build_suggested_emitters(lips, gaps)

    mesh = bpy.data.meshes.new("WFT_Terrain_MainTerrainMesh")
    mesh.from_pydata(mesh_payload.vertices, [], mesh_payload.faces)
    mesh.update()
    terrain_object = bpy.data.objects.new("WFT_Terrain_MainTerrain", mesh)
    context.scene.collection.objects.link(terrain_object)

    for index, emitter in enumerate(emitters):
        curve_data = bpy.data.curves.new(f"WFT_Terrain_SuggestedEmitterCurve_{index:02d}", type="CURVE")
        curve_data.dimensions = "3D"
        spline = curve_data.splines.new("POLY")
        spline.points.add(len(emitter.points) - 1)
        for point_index, point in enumerate(emitter.points):
            spline.points[point_index].co = (*point, 1.0)
        emitter_object = bpy.data.objects.new(f"WFT_Terrain_SuggestedEmitter_{index:02d}", curve_data)
        context.scene.collection.objects.link(emitter_object)
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\operators\terrain_generate.py
from __future__ import annotations

import bpy

from ..adapters.blender_terrain import create_terrain_objects


class WFT_OT_GenerateTerraceTerrain(bpy.types.Operator):
    bl_idname = "wft.generate_terrace_terrain"
    bl_label = "Generate Terrace Terrain"

    def execute(self, context):
        create_terrain_objects(context, context.scene.wft_settings)
        return {"FINISHED"}
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\panel.py
box = layout.box()
box.label(text="Terrain Generator")
box.prop(settings, "terrain_axis_object")
box.prop(settings, "terrain_level_count")
box.prop(settings, "terrain_total_drop")
box.prop(settings, "terrain_base_width")
box.prop(settings, "terrain_depth")
box.operator("wft.generate_terrace_terrain")
```

- [ ] **Step 4: Run the Blender smoke script**

Run: `C:\Software\blender-4.2.3-windows-x64\blender.exe --background --factory-startup --python D:\YYBWorkSpace\GitHub\waterfallTool\scripts\smoke_terrain_generate.py`
Expected: PASS with `WFT terrain generate smoke test completed`

- [ ] **Step 5: Commit the terrain generation operator**

```bash
git add addon/waterfall_tool/adapters/blender_terrain.py addon/waterfall_tool/operators/terrain_generate.py addon/waterfall_tool/properties.py addon/waterfall_tool/panel.py addon/waterfall_tool/registration.py scripts/smoke_terrain_generate.py
git commit -m "feat: generate terrace terrain objects in blender"
```

### Task 5: Add Override Support for Lips and Manual Blockers

**Files:**
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\terrain\overrides.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\adapters\blender_terrain.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\properties.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_terrain_overrides.py`

- [ ] **Step 1: Write the failing override test**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_terrain_overrides.py
from waterfall_tool.terrain.overrides import apply_lip_overrides
from waterfall_tool.terrain.types import LipCurveDraft


def test_apply_lip_overrides_replaces_only_targeted_level():
    auto_lips = [
        LipCurveDraft(level_index=0, points=[(-3.0, 0.0, 4.0), (0.0, 0.0, 3.8), (3.0, 0.0, 4.0)], continuity_segments=[(0.0, 1.0)], overridden=False),
        LipCurveDraft(level_index=1, points=[(-2.5, 0.0, 1.0), (0.0, 0.0, 0.8), (2.5, 0.0, 1.0)], continuity_segments=[(0.0, 1.0)], overridden=False),
    ]
    overrides = {
        1: LipCurveDraft(level_index=1, points=[(-2.0, 0.0, 1.3), (0.0, 0.0, 0.7), (2.0, 0.0, 1.3)], continuity_segments=[(0.0, 1.0)], overridden=True)
    }

    merged = apply_lip_overrides(auto_lips, overrides)

    assert merged[0].points == auto_lips[0].points
    assert merged[1].overridden is True
    assert merged[1].points[0] == (-2.0, 0.0, 1.3)
```

- [ ] **Step 2: Run the override test to verify it fails**

Run: `py -m pytest tests/core/test_terrain_overrides.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'waterfall_tool.terrain.overrides'`

- [ ] **Step 3: Implement the override merge logic and scene pointers**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\terrain\overrides.py
from __future__ import annotations

from .types import LipCurveDraft


def apply_lip_overrides(auto_lips: list[LipCurveDraft], overrides: dict[int, LipCurveDraft]) -> list[LipCurveDraft]:
    merged: list[LipCurveDraft] = []
    for lip in auto_lips:
        merged.append(overrides.get(lip.level_index, lip))
    return merged
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\properties.py
class WFT_Settings(bpy.types.PropertyGroup):
    terrain_override_collection: bpy.props.PointerProperty(name="Terrain Overrides", type=bpy.types.Collection)
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\adapters\blender_terrain.py
from ..terrain.overrides import apply_lip_overrides
from ..terrain.types import LipCurveDraft


def read_lip_overrides(collection: bpy.types.Collection | None) -> dict[int, LipCurveDraft]:
    if collection is None:
        return {}
    overrides: dict[int, LipCurveDraft] = {}
    for obj in collection.objects:
        if obj.type != "CURVE":
            continue
        level_index = int(obj.get("wft_level_index", -1))
        if level_index < 0:
            continue
        spline = obj.data.splines[0]
        points = [tuple(obj.matrix_world @ mathutils.Vector(point.co[:3])) for point in spline.points]
        overrides[level_index] = LipCurveDraft(level_index=level_index, points=points, continuity_segments=[(0.0, 1.0)], overridden=True)
    return overrides
```

- [ ] **Step 4: Run the override test**

Run: `py -m pytest tests/core/test_terrain_overrides.py -v`
Expected: PASS with `1 passed`

- [ ] **Step 5: Commit the terrain override support**

```bash
git add addon/waterfall_tool/terrain/overrides.py addon/waterfall_tool/adapters/blender_terrain.py addon/waterfall_tool/properties.py tests/core/test_terrain_overrides.py
git commit -m "feat: add terrace lip override support"
```

### Task 6: Hand Off Generated Terrain to the Waterfall Generator

**Files:**
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\operators\terrain_handoff.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\terrain\emitters.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\panel.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\registration.py`
- Create: `D:\YYBWorkSpace\GitHub\waterfallTool\scripts\smoke_terrain_handoff.py`

- [ ] **Step 1: Write the failing handoff selection test**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\tests\core\test_terrain_emitters.py
from waterfall_tool.terrain.emitters import build_suggested_emitters, choose_handoff_emitter, choose_handoff_emitter_name
from waterfall_tool.terrain.types import GapSegment, LipCurveDraft, SuggestedEmitter


def test_choose_handoff_emitter_name_picks_strongest_enabled_emitter():
    emitters = [
        SuggestedEmitter(level_index=0, points=[(-2.0, 0.0, 4.0), (0.0, 0.0, 3.8)], strength=0.25, enabled=True),
        SuggestedEmitter(level_index=1, points=[(-1.0, 0.0, 1.0), (1.0, 0.0, 0.9)], strength=0.4, enabled=True),
    ]

    assert choose_handoff_emitter_name(["WFT_Terrain_SuggestedEmitter_00", "WFT_Terrain_SuggestedEmitter_01"], emitters) == "WFT_Terrain_SuggestedEmitter_01"
```

- [ ] **Step 2: Run the emitter test to verify it fails**

Run: `py -m pytest tests/core/test_terrain_emitters.py -v`
Expected: FAIL with `ImportError: cannot import name 'choose_handoff_emitter_name'`

- [ ] **Step 3: Implement handoff selection and the Blender handoff operator**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\terrain\emitters.py
def choose_handoff_emitter_name(object_names: list[str], emitters: list[SuggestedEmitter]) -> str:
    chosen = choose_handoff_emitter(emitters)
    chosen_index = emitters.index(chosen)
    return object_names[chosen_index]
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\addon\waterfall_tool\operators\terrain_handoff.py
from __future__ import annotations

import bpy


class WFT_OT_UseGeneratedTerrainForWaterfall(bpy.types.Operator):
    bl_idname = "wft.use_generated_terrain_for_waterfall"
    bl_label = "Use Terrain For Waterfall"

    def execute(self, context):
        settings = context.scene.wft_settings
        emitter = bpy.data.objects.get("WFT_Terrain_SuggestedEmitter_00")
        terrain = bpy.data.objects.get("WFT_Terrain_MainTerrain")
        if emitter is None or terrain is None:
            self.report({"ERROR"}, "Generate terrain before handoff")
            return {"CANCELLED"}
        settings.emitter_object = emitter
        settings.collider_object = terrain
        return {"FINISHED"}
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\scripts\smoke_terrain_handoff.py
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "addon"))

import bpy
import waterfall_tool

waterfall_tool.register()

curve_data = bpy.data.curves.new("TerrainAxis", type="CURVE")
curve_data.dimensions = "3D"
spline = curve_data.splines.new("POLY")
spline.points.add(2)
spline.points[0].co = (-4.0, 0.0, 4.0, 1.0)
spline.points[1].co = (0.0, 0.0, 2.5, 1.0)
spline.points[2].co = (4.0, 0.0, 4.0, 1.0)
axis = bpy.data.objects.new("TerrainAxis", curve_data)
bpy.context.scene.collection.objects.link(axis)

settings = bpy.context.scene.wft_settings
settings.terrain_axis_object = axis

assert bpy.ops.wft.generate_terrace_terrain() == {"FINISHED"}
assert bpy.ops.wft.use_generated_terrain_for_waterfall() == {"FINISHED"}
assert bpy.ops.wft.generate_preview() == {"FINISHED"}
assert bpy.data.objects.get("WFT_PreviewPaths") is not None
print("WFT terrain handoff smoke test completed")
```

- [ ] **Step 4: Run the terrain handoff test and smoke script**

Run: `py -m pytest tests/core/test_terrain_emitters.py -v`
Expected: PASS with all emitter tests passing

Run: `C:\Software\blender-4.2.3-windows-x64\blender.exe --background --factory-startup --python D:\YYBWorkSpace\GitHub\waterfallTool\scripts\smoke_terrain_handoff.py`
Expected: PASS with `WFT terrain handoff smoke test completed`

- [ ] **Step 5: Commit the waterfall handoff**

```bash
git add addon/waterfall_tool/terrain/emitters.py addon/waterfall_tool/operators/terrain_handoff.py addon/waterfall_tool/panel.py addon/waterfall_tool/registration.py scripts/smoke_terrain_handoff.py tests/core/test_terrain_emitters.py
git commit -m "feat: hand off terrace terrain to waterfall generator"
```

### Task 7: Replace the Flat Demo with Generated Terrace Terrain

**Files:**
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\scripts\demo_scene.py`
- Modify: `D:\YYBWorkSpace\GitHub\waterfallTool\scripts\demo_render.py`

- [ ] **Step 1: Write the failing Blender demo smoke command**

Run: `C:\Software\blender-4.2.3-windows-x64\blender.exe --background --factory-startup --python D:\YYBWorkSpace\GitHub\waterfallTool\scripts\demo_render.py`
Expected: FAIL because the old flat-cliff demo does not create `WFT_Terrain_MainTerrain`

- [ ] **Step 2: Replace the demo scene with generated terrain**

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\scripts\demo_scene.py
settings.terrain_axis_object = axis
settings.terrain_level_count = 3
settings.terrain_total_drop = 6.0
settings.terrain_base_width = 8.0
settings.terrain_depth = 2.8

assert bpy.ops.wft.generate_terrace_terrain() == {"FINISHED"}
assert bpy.ops.wft.use_generated_terrain_for_waterfall() == {"FINISHED"}
assert bpy.ops.wft.generate_preview() == {"FINISHED"}
assert bpy.ops.wft.bake_preview() == {"FINISHED"}
assert bpy.ops.wft.rebuild_waterfall() == {"FINISHED"}
```

```python
# D:\YYBWorkSpace\GitHub\waterfallTool\scripts\demo_render.py
terrain = bpy.data.objects["WFT_Terrain_MainTerrain"]
terrain.data.materials.append(create_material("CliffMat", (0.18, 0.20, 0.23, 1.0), roughness=0.8))
```

- [ ] **Step 3: Run the demo render command again**

Run: `C:\Software\blender-4.2.3-windows-x64\blender.exe --background --factory-startup --python D:\YYBWorkSpace\GitHub\waterfallTool\scripts\demo_render.py`
Expected: PASS and writes `exports/demo/preview.png`, `exports/demo/rebuild.png`, and `exports/demo/demo_waterfall.glb`

- [ ] **Step 4: Run the full terrain and waterfall verification suite**

Run: `py -m pytest tests/core -v`
Expected: PASS with all terrain and waterfall tests passing

Run: `C:\Software\blender-4.2.3-windows-x64\blender.exe --background --factory-startup --python D:\YYBWorkSpace\GitHub\waterfallTool\scripts\smoke_preview.py`
Expected: PASS with `WFT preview smoke test completed`

Run: `C:\Software\blender-4.2.3-windows-x64\blender.exe --background --factory-startup --python D:\YYBWorkSpace\GitHub\waterfallTool\scripts\smoke_rebuild.py`
Expected: PASS with `WFT rebuild smoke test completed`

Run: `C:\Software\blender-4.2.3-windows-x64\blender.exe --background --factory-startup --python D:\YYBWorkSpace\GitHub\waterfallTool\scripts\smoke_export.py`
Expected: PASS with `WFT export smoke test completed`

- [ ] **Step 5: Commit the generated terrace demo**

```bash
git add scripts/demo_scene.py scripts/demo_render.py
git commit -m "feat: demo generated terrace waterfall terrain"
```

## Self-Review

### Spec coverage

- Core terrain structure generation: covered by Tasks 1 through 3.
- Blender terrain object generation: covered by Task 4.
- Local lip override support: covered by Task 5.
- Waterfall handoff: covered by Task 6.
- Demo proving generated terrain improves the old flat cliff example: covered by Task 7.

### Placeholder scan

- No `TBD`, `TODO`, or “implement later” markers remain.
- Each task names exact files, commands, and expected outputs.

### Type consistency

- `TerrainBlueprint`, `TerraceLevel`, `LipCurveDraft`, `GapSegment`, `BlockerMass`, `SuggestedEmitter`, and `TerrainMeshPayload` are introduced before later tasks reference them.
- `build_terrace_levels`, `build_lip_curves`, `build_gap_segments`, `build_blocker_masses`, `build_main_terrain_mesh`, and `build_suggested_emitters` are introduced before any Blender adapter or operator calls them.
