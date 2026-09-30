"""Narrow source-validation exception for EXP234 detector calibration."""
import os
from pathlib import Path


def validate_scope(bundle, movies):
    names = list(movies)
    assert names and len(names) == len(set(names))
    source = bundle["source_embryo"]
    if bundle.get("evaluation_mode") != "EXP234_SOURCE_THRESHOLD_SELECTION":
        assert all(not name.startswith(source + "_") for name in names), "Target is source embryo"
        return
    assert source in ("44b6", "6bba")
    expected = bundle["source_validation_movies"]
    assert names == expected, "Source-validation cohort differs from frozen allowlist"
    assert all(name.startswith(source + "_") for name in names)
    assert not set(names).intersection(bundle["source_train_movies"])
    assert not set(names).intersection(bundle["center_seen_movies"])
    assert bundle["selection_rule"] == "maximum_official_source_score_tie_baseline_0965"


def reject_label_geff_open(event, values, prediction_root):
    """Permit only this run's generated GEFF predictions during inference."""
    if event != "open" or not values:
        return
    raw = values[0]
    if not isinstance(raw, (str, bytes, os.PathLike)):
        return
    path = Path(os.fsdecode(raw)).resolve()
    if not any(part.lower().endswith(".geff") for part in path.parts):
        return
    if not path.is_relative_to(Path(prediction_root).resolve()):
        raise RuntimeError("EXP234 no label access during inference")


def _self_test():
    base = {"source_embryo": "44b6"}
    validate_scope(base, ["6bba_foo"])
    spec = {**base, "evaluation_mode": "EXP234_SOURCE_THRESHOLD_SELECTION",
            "source_validation_movies": ["44b6_a", "44b6_b"],
            "source_train_movies": ["44b6_train"], "center_seen_movies": ["44b6_center"],
            "selection_rule": "maximum_official_source_score_tie_baseline_0965"}
    validate_scope(spec, ["44b6_a", "44b6_b"])
    invalid = [(spec, ["44b6_a"]), (spec, ["44b6_b", "44b6_a"]),
               (spec, ["44b6_a", "6bba_x"]),
               ({**spec, "source_train_movies": ["44b6_a"]}, ["44b6_a", "44b6_b"]),
               ({**spec, "center_seen_movies": ["44b6_b"]}, ["44b6_a", "44b6_b"]),
               (base, ["44b6_a"])]
    for bundle, movies in invalid:
        try:
            validate_scope(bundle, movies)
        except AssertionError:
            continue
        raise AssertionError("Forbidden source cohort accepted")


if __name__ == "__main__":
    _self_test()
    print("PASS_EXP234_SOURCE_SCOPE")
