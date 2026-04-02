from pathlib import Path

from waterfall_tool.core.cache import load_cache, save_cache
from waterfall_tool.core.types import PathPoint


def test_cache_round_trip(tmp_path: Path):
    cache_file = tmp_path / "preview.json"
    paths = [[PathPoint(position=(0.0, 0.0, 1.0), speed=1.2, breakup=0.1, split_score=0.0)]]

    save_cache(cache_file, paths)
    loaded = load_cache(cache_file)

    assert loaded == paths
