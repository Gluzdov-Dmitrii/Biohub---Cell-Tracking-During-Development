"""Read-only EXP209 current-organizer rescore readiness audit.

This script deliberately has no label reader or scoring path.  EXP209's
historical result archive retained metric rows, not the 175 final prediction
graphs.  A CPU rescore must not reconstruct those graphs and call the result a
replay of the sealed experiment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


ARCHIVE = Path("outputs/research/exp209_selected_centroid_confirmation_20260912")
HISTORICAL_RESULT = ARCHIVE / "forward_plus_exp191_confirmation.json"
HISTORICAL_RECEIPT = Path("reports/exp209_selected_centroid_confirmation_result_20260912.json")
BASELINE_ROWS = Path("reports/exp214_frozen_exp209_baseline_rows_20260912.json")
CLEANUP_RECEIPT = Path("reports/exp209_completion_cleanup_receipt_20260912.json")
SOURCE44 = Path("outputs/research/exp130_official24_private_first/trainer_44b6_source.json")
SOURCE6BBA = Path(
    "outputs/research/exp130_official24_private_first/exp137_remote_artifacts/trainer_6bba_source.json"
)
METRICS = Path("work/x138_provenance/official_metric/metrics_pinned.py")
DIVISION = Path("work/x138_provenance/official_metric/division_metrics_pinned.py")
TRACKSDATA_DIRECT_URL = Path(
    "work/x138_provenance/official_metric/venv/Lib/site-packages/"
    "tracksdata-0.1.0rc11.dist-info/direct_url.json"
)
DEFAULT_RECEIPT = Path("reports/exp209_current_metric_rescore_readiness_20260927.json")

PINNED_SHA = {
    "manifest": "1d9bd5c800958d9fa0d5de8982fc12afcaf6d9e776ccd995408033f1c67eff8a",
    "historical_result": "bcc57aeef14a9419daab17ca10398774d229f499926f53176948eab331c05e0c",
    "historical_receipt": "c021e4fb1c901bc46a1c20f83fcd3b32997ddc65b25cc40462a0332c55e0bc6a",
    "baseline_rows": "02553492856899dff558f949991f0df8435eacd37c7d6634f9ed76bfb762cb8e",
    "cleanup_receipt": "b88366b14548c52b213d176b8df7d668c5b0095df60620f66284747f63739101",
    "source44_manifest": "296d307f9ff174ce3d3db9bc77b8b12c2674178b8b09598fed129574c4b458a4",
    "source6bba_manifest": "5eb0c0426c8b2cc5331c4e2ea0b34e79d3caf48e8eef822def89c69da0b11b0b",
    "metrics": "cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444",
    "division": "0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9",
}
PINNED_TRACKSDATA_COMMIT = "e13cf379b5127deeb8301ce56410fda35b5a3cf9"
HISTORICAL_SCORE = 0.6815218332750073
EXPECTED_COUNTS = {"forward": 116, "reverse": 59}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class GateError(ValueError):
    """An input failed a prerequisite before any label access."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise GateError(reason)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pinned_file(root: Path, relative: Path, expected_sha: str) -> Path:
    path = root / relative
    require(path.is_file(), f"missing pinned file: {relative.as_posix()}")
    require(sha256(path) == expected_sha, f"pinned SHA mismatch: {relative.as_posix()}")
    return path


def json_file(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def audit_archive(archive: Path, manifest_sha: str) -> dict[str, str]:
    manifest = archive / "SHA256SUMS"
    require(manifest.is_file(), "missing EXP209 SHA256SUMS")
    require(sha256(manifest) == manifest_sha, "EXP209 SHA256SUMS pin mismatch")
    entries: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  \./([^/\\]+)", line)
        require(match is not None, "malformed or nonlocal EXP209 manifest entry")
        expected, name = match.groups()
        require(name not in entries and name != "SHA256SUMS", "duplicate/recursive EXP209 manifest entry")
        path = archive / name
        require(path.is_file(), f"missing EXP209 archive entry: {name}")
        require(sha256(path) == expected, f"EXP209 archive entry SHA mismatch: {name}")
        entries[name] = expected
    require(len(entries) == 38, f"EXP209 archive expected 38 entries; found {len(entries)}")
    actual = {p.name for p in archive.iterdir() if p.is_file()} - {"SHA256SUMS"}
    require(actual == set(entries), "EXP209 archive has unsealed or missing files")
    return entries


def canonical_id(value: str) -> str:
    require(isinstance(value, str), "dataset identifier is not a string")
    movie = value.removesuffix(".zarr")
    require(re.fullmatch(r"(?:44b6|6bba)_[0-9a-f]{8}", movie) is not None, f"invalid movie ID: {value}")
    return movie


def selected_ids(result: dict[str, Any], counts: dict[str, int] = EXPECTED_COUNTS) -> dict[str, list[str]]:
    ids: dict[str, list[str]] = {}
    for direction, prefix in (("forward", "6bba"), ("reverse", "44b6")):
        rows = result["directions"][direction]["selected_rows"]
        values = [canonical_id(row["dataset"]) for row in rows]
        require(len(values) == counts[direction], f"EXP209 {direction} count mismatch")
        require(len(set(values)) == len(values), f"EXP209 {direction} duplicate movie")
        require(all(value.startswith(prefix + "_") for value in values), f"EXP209 {direction} embryo mismatch")
        ids[direction] = values
    require(not (set(ids["forward"]) & set(ids["reverse"])), "EXP209 direction overlap")
    return ids


def audit_source_split(source: Any, index: int, source_prefix: str, targets: list[str]) -> dict[str, Any]:
    require(isinstance(source, list) and len(source) > index, "missing source trainer split")
    split = source[index]
    require(isinstance(split, dict) and set(split) >= {"train", "test"}, "malformed source trainer split")
    train = [canonical_id(value) for value in split["train"]]
    validation = [canonical_id(value) for value in split["test"]]
    require(len(train) == 10 and len(validation) == 2, "unexpected source train/validation count")
    require(len(set(train + validation)) == 12, "duplicate source train/validation ID")
    require(all(value.startswith(source_prefix + "_") for value in train + validation), "source split embryo mismatch")
    require(not set(train + validation).intersection(targets), "source/target movie ID overlap")
    require(all(not value.startswith(source_prefix + "_") for value in targets), "source/target embryo overlap")
    return {"train_count": 10, "checkpoint_validation_count": 2, "source_prefix": source_prefix,
            "target_count": len(targets), "embryo_prefix_disjoint": True}


def audit(root: Path) -> dict[str, Any]:
    root = root.resolve()
    entries = audit_archive(root / ARCHIVE, PINNED_SHA["manifest"])
    paths = {
        "historical_result": HISTORICAL_RESULT,
        "historical_receipt": HISTORICAL_RECEIPT,
        "baseline_rows": BASELINE_ROWS,
        "cleanup_receipt": CLEANUP_RECEIPT,
        "source44_manifest": SOURCE44,
        "source6bba_manifest": SOURCE6BBA,
        "metrics": METRICS,
        "division": DIVISION,
    }
    documents = {key: pinned_file(root, relative, PINNED_SHA[key]) for key, relative in paths.items()}
    historical = json_file(documents["historical_result"])
    receipt = json_file(documents["historical_receipt"])
    baseline = json_file(documents["baseline_rows"])
    cleanup = json_file(documents["cleanup_receipt"])
    structural = json_file(root / ARCHIVE / "all_chunks_no_metric_gate.json")
    require(structural.get("status") == "PASS_EXP209_ALL_SELECTED_CENTROID_CHUNKS_NO_METRICS", "EXP209 structural status mismatch")
    require(structural.get("movie_count") == 175 and structural.get("direction_counts") == EXPECTED_COUNTS,
            "EXP209 structural cohort mismatch")
    require(not structural.get("scientific_metrics_emitted"), "EXP209 structural gate includes metrics")
    require(historical.get("status") == "PASS_FROZEN_CONFIRMATION_ASSEMBLY", "EXP209 historical result status mismatch")
    score = historical["combined"]["frozen_selected"]["score"]
    require(abs(score - HISTORICAL_SCORE) <= 1e-12, "EXP209 historical score mismatch")
    ids = selected_ids(historical)
    require(receipt.get("status") == "PASS_NEW_POOLED_OOF_FRONTIER", "EXP209 historical receipt status mismatch")
    require(abs(receipt["promoted_policy"]["pooled_oof"] - HISTORICAL_SCORE) <= 1e-12,
            "EXP209 historical receipt score mismatch")
    require(receipt["integrity"]["manifest_sha256"] == PINNED_SHA["manifest"],
            "EXP209 historical receipt manifest mismatch")
    require(cleanup["result_integrity"]["manifest_sha256"] == PINNED_SHA["manifest"],
            "EXP209 cleanup manifest mismatch")
    require(cleanup["result_integrity"]["local_sha256sum_entries_verified"] == 38,
            "EXP209 cleanup entry count mismatch")
    require(baseline["source_sha256"] == PINNED_SHA["historical_result"], "EXP214 frozen row source mismatch")
    require(abs(baseline["score"] - HISTORICAL_SCORE) <= 1e-12, "EXP214 frozen row score mismatch")
    baseline_ids = [canonical_id(row["dataset"]) for row in baseline["rows"]]
    require(len(baseline_ids) == 175 and len(set(baseline_ids)) == 175,
            "EXP214 frozen baseline cohort mismatch")
    require(set(baseline_ids) == set(ids["forward"] + ids["reverse"]),
            "EXP214 frozen row IDs differ from EXP209 selected cohort")
    source_provenance = {
        "forward": audit_source_split(json_file(documents["source44_manifest"]), 0, "44b6", ids["forward"]),
        "reverse": audit_source_split(json_file(documents["source6bba_manifest"]), 1, "6bba", ids["reverse"]),
    }
    direct = root / TRACKSDATA_DIRECT_URL
    require(direct.is_file(), "missing pinned tracksdata installation receipt")
    commit = json_file(direct).get("vcs_info", {}).get("commit_id")
    require(commit == PINNED_TRACKSDATA_COMMIT, "tracksdata commit mismatch")

    # This is the decisive gate: the immutable EXP209 manifest lists only
    # metric-result JSON/log files, with no final graph bytes or graph hash
    # manifest.  It cannot support exact CPU metric replay.
    graph_entries = sorted(name for name in entries if Path(name).suffix.lower() in {".csv", ".parquet", ".feather", ".npz"})
    require(not graph_entries, "unexpected graph-like EXP209 entry requires human inspection")
    return {
        "experiment": "EXP209",
        "date_local": "2026-09-27",
        "purpose": "current-organizer CPU rescore readiness; no score execution",
        "status": "BLOCKED_NO_SEALED_FINAL_GRAPH175",
        "evidence_class": "historical reciprocal embryo-held-out evaluation; historical evaluator only",
        "historical_score_preserved": HISTORICAL_SCORE,
        "historical_rows": 175,
        "historical_forward_rows": 116,
        "historical_reverse_rows": 59,
        "current_organizer_score": None,
        "selected_movie_ids": ids,
        "source_provenance": source_provenance,
        "sealed_result_archive": {
            "path": ARCHIVE.as_posix(), "manifest_sha256": PINNED_SHA["manifest"],
            "entry_count": len(entries), "final_graph_entries": graph_entries,
        },
        "missing_prerequisite": {
            "kind": "original sealed postprocessed EXP209 selected final prediction graphs plus per-graph SHA256s",
            "movie_count": 175,
            "forward_count": 116,
            "reverse_exp191_count": 59,
            "reason": "EXP209 archive and remote run retained score rows/logs, not final graph files or original final-graph hashes",
        },
        "pinned_inputs_sha256": PINNED_SHA,
        "tracksdata_commit": commit,
        "organizer_metric_commit": "075fc5f5a52d11077f9dc2b074644618f26939e2",
        "labels_read": False,
        "remote_action": False,
        "gpu_used": False,
        "kaggle_post": False,
        "rescore_authorized": False,
    }


def write_once(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with os.fdopen(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644), "wb") as out:
        out.write(content)
        out.flush()
        os.fsync(out.fileno())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    result = audit(args.root)
    if not args.no_write:
        write_once(args.root / args.receipt, result)
    print(json.dumps({"status": result["status"], "historical_score": result["historical_score_preserved"],
                      "current_organizer_score": None, "sealed_graph_count": 0,
                      "receipt": None if args.no_write else str(args.root / args.receipt)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
