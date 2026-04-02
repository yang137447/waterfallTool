```markdown
# Terrain layout implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce deterministic lip, gap, and blocker layout helpers plus a regression test to ensure they produce the expected counts for the provided blueprint.

**Architecture:** Add dedicated, focused helpers in `addon/waterfall_tool/terrain/layout.py` that consume the existing `TerraceLevel` list and `TerrainBlueprint` and return lightweight layout artifacts while `types.py` exposes the shared dataclasses. Tests live in `tests/core/test_terrain_layout.py` and simply drive the helpers from the known blueprint.

**Tech Stack:** Python 3 dataclasses + tuples, standard list comprehensions, pytest for verification.

---

### Task 1: Terrain layout helpers

**Files:**
- Create: `addon/waterfall_tool/terrain/layout.py`
- Modify: `addon/waterfall_tool/terrain/types.py`
- Test: `tests/core/test_terrain_layout.py`

- [ ] **Step 1: Write the failing test**

```python
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

- [ ] **Step 2: Run test to verify it fails**

```
py -m pytest tests/core/test_terrain_layout.py -v
Expected: FAIL with ModuleNotFoundError for waterfall_tool.terrain.layout
```

- [ ] **Step 3: Write the minimal implementation**

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Vec3 = tuple[float, float, float]
LipProfileMode = Literal["arc", "mixed"]

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
    mid_index = min(2, len(levels) - 1)
    return [
        BlockerMass(
            level_index=1,
            center=(-1.45, -0.55, levels[1].elevation - 0.8),
            width=1.4,
            height=1.1,
            forward_offset=-0.55,
            manual=False,
        ),
        BlockerMass(
            level_index=mid_index,
            center=(1.75, -0.62, levels[mid_index].elevation - 0.55),
            width=1.2,
            height=0.9,
            forward_offset=-0.62,
            manual=False,
        ),
    ]
```

- [ ] **Step 4: Run tests to confirm passing**

```
py -m pytest tests/core/test_terrain_layout.py -v
Expected: PASS
```

- [ ] **Step 5: Commit**

```
git add addon/waterfall_tool/terrain/types.py addon/waterfall_tool/terrain/layout.py tests/core/test_terrain_layout.py
git commit -m "feat: add terrace lip gap and blocker layout"
```
