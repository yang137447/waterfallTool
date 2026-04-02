```markdown
# Terrain layout generation design

## Context

Task 1 already established the immutable `TerrainBlueprint` and `TerraceLevel` models along with `build_terrace_levels()`. Task 2 extends that foundation by introducing lightweight surface layout artifacts (lips, gaps, blockers) that populate unit storms without Blender/OpenGL dependencies. The layout helpers need to be deterministic and small, matching the test specification provided in the task description.

## Goals

1. Add pure-Python dataclasses for `LipCurveDraft`, `GapSegment`, and `BlockerMass` inside `types.py`.
2. Implement `build_lip_curves()`, `build_gap_segments()`, and `build_blocker_masses()` inside `layout.py` so they return the fixed data patterns described in the task rather than relying on external randomness or actual geometry.
3. Introduce a regression test (`tests/core/test_terrain_layout.py`) that wires `build_terrace_levels()` with the new helpers and checks that the expected counts/indices of lips, gaps, and blockers match the given static blueprint.

## Approach

### Data structures

- `LipCurveDraft` captures the level index, a 5-point lip profile lifted slightly above/below the level elevation, normalized continuity segments, and an `overridden` flag that stays `False`. The points align to the blueprint's middle Y (axis) coordinate.
- `GapSegment` indexes the second level and always produces the two ranges outlined in the task, with hard-coded depth strengths and no locking.
- `BlockerMass` uses two fixed centers that reference levels 1 and 2 (capped by the number of generated levels) and stores width, height, offset, and `manual=False`.

### Layout helpers

- `build_lip_curves(levels, blueprint)` iterates the validated levels, computes half-width, and stitches the point list exactly as described (multipliers for X and constant Z offsets). Each result uses `axis_points[1]` to align vertically.
- `build_gap_segments(lips, blueprint)` simply returns the two `GapSegment` entries once there are at least two lips; otherwise it returns an empty list for single-level blueprints.
- `build_blocker_masses(levels, lips, gaps, blueprint)` ignores the extra lists aside from guarding for at least two levels, then returns the two `BlockerMass` entries anchored to levels 1 and `min(2, len(levels)-1)`. It uses the level elevations to anchor the Z coordinate as specified in the instructions.

This strategy matches the provided deterministic logic, even though it does not yet react to `gap_frequency` or `blocker_density`.

## Testing

1. Add `tests/core/test_terrain_layout.py` that instantiates the same blueprint from the task description.
2. Call `build_terrace_levels()` and then the three layout helpers.
3. Assert that there are three lips (levels 0–2), two gap segments with the first tied to level 1, and two blockers.
4. Run `py -m pytest tests/core/test_terrain_layout.py -v` as part of verification.

## Risks & Open Questions

- The new layout helpers are intentionally hard-coded. If future work must honor `gap_frequency`/`blocker_density`, this module will need refactoring.
- Because the test uses static offsets, any change to `TerraceLevel` calculations might require synchronizing these helpers.

Please review this spec at `docs/superpowers/specs/2026-04-02-terrain-layout-design.md` and let me know if you would like adjustments before I move into the implementation plan.
```
