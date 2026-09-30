import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_exp195_confirmation_result import apply_policy, merge_chunks


def test_frozen_threshold_boundary_is_inclusive():
    assert apply_policy(0.08, 0.08) is True
    assert apply_policy(0.081, 0.08) is False


def test_merge_rejects_duplicate_movies(tmp_path):
    payload = {"per_movie_by_arm": {"x": [{"dataset": "44b6_a.zarr"}]}, "telemetry": [{"dataset": "44b6_a.zarr"}]}
    paths = []
    for index in range(2):
        path = tmp_path / f"{index}.json"
        path.write_text(json.dumps(payload))
        paths.append(path)
    with pytest.raises(ValueError, match="duplicate"):
        merge_chunks(paths)
