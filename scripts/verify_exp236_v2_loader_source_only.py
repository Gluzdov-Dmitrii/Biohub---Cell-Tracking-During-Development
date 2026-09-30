"""CPU-only real-data smoke for staged EXP236 v2 source window filtering."""
import hashlib
import json
from pathlib import Path
import sys


CODE = Path("/home/scientists/gluz_d_s/kaggle/projects/"
            "biohub-cell-tracking-during-development/code/"
            "exp236_horaz_source6bba_block01_v2_20260927")
MANIFEST_SHA = "b594f5ca6e2c644b151d780546cab140208f08558d1b93b24cef7a576a6e5f4a"
PLAN_SHA = "e525d6f44f45468520fa085836ce4c166f594dbc5d64e79c7e15a10083e5c536"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert sha(CODE / "code_manifest.json") == MANIFEST_SHA
    for name, digest in json.loads((CODE / "code_manifest.json").read_text()).items():
        path = (CODE / name).resolve()
        assert path.is_relative_to(CODE.resolve()) and sha(path) == digest, name
    assert sha(CODE / "plan.json") == PLAN_SHA
    plan = json.loads((CODE / "plan.json").read_text())
    assert plan["source_embryo"] == "6bba" and plan["target_embryo"] == "44b6"
    pair_map_path = CODE / "horaz/src/src/exp236_source_duplicate_pairs.json"
    assert sha(pair_map_path) == plan["source_duplicate_map_sha256"]
    pair_map = json.loads(pair_map_path.read_text())
    sys.path.insert(0, str(CODE / "horaz/src/src"))
    from datasets import build_window, load_video_windows, read_training_graph

    totals = {}
    for split in ("train", "inner_validation"):
        baseline = kept = removed = 0
        for row in plan[split]:
            name = row["dataset_id"]
            assert name.startswith("6bba_")
            graph = read_training_graph(row["geff_path"])
            original = [build_window(graph, t, 2, (1, 4, 4)) for t in range(99)]
            original = [window for window in original if window is not None]
            metadata, windows = load_video_windows(row, 2, (1, 4, 4), None)
            assert metadata.dataset_id == name and windows
            excluded = set(pair_map["duplicate_starts"].get(name, []))
            assert not excluded.intersection(window.time_start for window in windows)
            baseline += len(original)
            kept += len(windows)
            removed += len(original) - len(windows)
        totals[split] = {"movies": len(plan[split]), "baseline_labeled_windows": baseline,
                         "kept_labeled_windows": kept, "removed_labeled_windows": removed}
    assert {split: value["removed_labeled_windows"] for split, value in totals.items()} == (
        plan["removed_sampled_windows_by_split"])
    print(json.dumps({"status": "PASS_EXP236_V2_ALL126_SOURCE_LOADER_CPU",
                      "evidence_class": "source-only loader smoke, no model training or OOF",
                      "manifest_sha256": MANIFEST_SHA, "plan_sha256": PLAN_SHA,
                      "source_duplicate_map_sha256": sha(pair_map_path),
                      "totals": totals, "target_data_opened": False}))


if __name__ == "__main__":
    main()
