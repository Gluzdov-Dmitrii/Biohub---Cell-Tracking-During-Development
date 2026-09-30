import json
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_exp192_chunk_structure import validate


def metric_payload(status, arms, movies):
    rows = [{"dataset": movie, "edge_tp": 1, "edge_fp": 0, "edge_fn": 0} for movie in movies]
    return {
        "status": status,
        "per_movie_by_arm": {arm: rows for arm in arms},
        "summary_by_arm": {arm: {"edge_tp": len(movies)} for arm in arms},
    }


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


@pytest.mark.parametrize(
    "direction,movies,specifications",
    [
        (
            "forward",
            ["6bba_a.zarr", "6bba_b.zarr"],
            [
                ("base_raw.json", "PASS_FROZEN_REGISTERED_MODEL_EVALUATION", {"registered_hungarian", "registered_weak_hungarian"}),
                ("base_filtered.json", "PASS_CACHED_SHORT_TRACK_FAMILY", {"no_filter", "min8"}),
                ("local_flow.json", "PASS_CACHED_FIXED_LOCAL_FLOW", {"translation", "fixed_local_flow"}),
            ],
        ),
        (
            "reverse",
            ["44b6_a.zarr"],
            [
                ("base_raw.json", "PASS_FROZEN_REGISTERED_MODEL_EVALUATION", {"registered_hungarian", "registered_weak_hungarian"}),
                ("base_filtered.json", "PASS_CACHED_SHORT_TRACK_FAMILY", {"no_filter", "min3"}),
                ("local_flow.json", "PASS_CACHED_FIXED_LOCAL_FLOW", {"translation", "fixed_local_flow"}),
                ("gap.json", "PASS_SYNTHETIC_GAP_EVALUATION", {"registered_hungarian", "synthetic_gap_no_veto", "synthetic_gap_deepcenter"}),
                ("gap_filtered.json", "PASS_CACHED_SELECTED_EDGE_SHORT_TRACKS", {"no_filter", "min6"}),
            ],
        ),
    ],
)
def test_validate_without_metric_disclosure(tmp_path, direction, movies, specifications):
    run = tmp_path / "run"
    write_json(run / "movies.json", {"target_development": movies})
    for name, status, arms in specifications:
        write_json(run / "results" / name, metric_payload(status, arms, movies))
    if direction == "reverse":
        write_json(run / "results" / "gap_cache_reproduction.json", {"status": "PASS_EXACT_CACHED_ARM_REPRODUCTION", "maximum_absolute_error": 0.0})
    result = validate(run, direction)
    assert result["status"] == "PASS_EXP192_CHUNK_STRUCTURE_NO_METRICS"
    assert result["movie_count"] == len(movies)
    assert result["scientific_metrics_emitted"] is False
    assert "summary_by_arm" not in result


def test_rejects_nonfinite_metric(tmp_path):
    run = tmp_path / "run"
    movies = ["6bba_a.zarr"]
    write_json(run / "movies.json", {"target_development": movies})
    raw = metric_payload("PASS_FROZEN_REGISTERED_MODEL_EVALUATION", {"registered_hungarian", "registered_weak_hungarian"}, movies)
    raw["per_movie_by_arm"]["registered_hungarian"][0]["edge_tp"] = math.nan
    write_json(run / "results" / "base_raw.json", raw)
    write_json(run / "results" / "base_filtered.json", metric_payload("PASS_CACHED_SHORT_TRACK_FAMILY", {"no_filter", "min8"}, movies))
    write_json(run / "results" / "local_flow.json", metric_payload("PASS_CACHED_FIXED_LOCAL_FLOW", {"translation", "fixed_local_flow"}, movies))
    with pytest.raises(ValueError, match="non-finite"):
        validate(run, "forward")
