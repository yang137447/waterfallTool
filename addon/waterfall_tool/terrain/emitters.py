from __future__ import annotations

from .types import GapSegment, LipCurveDraft, SuggestedEmitter


def _subtract_gap_segments(
    segments: list[tuple[float, float]], gaps: list[GapSegment]
) -> list[tuple[float, float]]:
    if not gaps:
        return segments

    sorted_gaps = sorted(gaps, key=lambda gap: gap.start_ratio)
    filtered: list[tuple[float, float]] = []
    for segment_start, segment_end in segments:
        current = segment_start
        for gap in sorted_gaps:
            overlap_start = max(segment_start, gap.start_ratio)
            overlap_end = min(segment_end, gap.end_ratio)
            if overlap_end <= overlap_start:
                continue
            if current < overlap_start:
                filtered.append((current, overlap_start))
            current = max(current, overlap_end)
        if current < segment_end:
            filtered.append((current, segment_end))
    return filtered


def build_suggested_emitters(lips: list[LipCurveDraft], gaps: list[GapSegment]) -> list[SuggestedEmitter]:
    emitters: list[SuggestedEmitter] = []
    for lip in lips:
        lip_gaps = [gap for gap in gaps if gap.level_index == lip.level_index]
        segments = _subtract_gap_segments(list(lip.continuity_segments), lip_gaps) if lip_gaps else [(0.0, 1.0)]
        for start_ratio, end_ratio in segments:
            if end_ratio <= start_ratio:
                continue
            start_index = int((len(lip.points) - 1) * start_ratio)
            end_index = max(start_index + 1, int((len(lip.points) - 1) * end_ratio))
            end_index = min(end_index, len(lip.points) - 1)
            if start_index >= len(lip.points) - 1:
                continue
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
    if not emitters:
        raise ValueError("No suggested emitters were provided")
    return sorted(emitters, key=lambda emitter: (-emitter.strength, emitter.level_index))[0]


def choose_handoff_emitter_name(object_names: list[str], emitters: list[SuggestedEmitter]) -> str:
    chosen = choose_handoff_emitter(emitters)
    chosen_index = emitters.index(chosen)
    return object_names[chosen_index]
