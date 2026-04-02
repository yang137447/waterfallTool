from __future__ import annotations

from .types import LipCurveDraft


def apply_lip_overrides(auto_lips: list[LipCurveDraft], overrides: dict[int, LipCurveDraft]) -> list[LipCurveDraft]:
    merged: list[LipCurveDraft] = []
    for lip in auto_lips:
        merged.append(overrides.get(lip.level_index, lip))
    return merged
