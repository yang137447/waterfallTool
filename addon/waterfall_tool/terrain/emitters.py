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
                    points=list(lip.points[start_index : end_index + 1]),
                    strength=end_ratio - start_ratio,
                    enabled=True,
                )
            )
    return emitters


def choose_handoff_emitter(emitters: list[SuggestedEmitter]) -> SuggestedEmitter:
    return sorted(emitters, key=lambda emitter: (-emitter.strength, emitter.level_index))[0]
