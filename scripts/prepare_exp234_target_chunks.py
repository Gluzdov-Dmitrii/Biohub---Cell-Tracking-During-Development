"""Freeze EXP234 target inference partitions before source threshold selection."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "reports/exp214_equal_time_plan_20260912.json"
OUTPUT = ROOT / "reports/exp234_target_chunk_assignment_20260926.json"
COHORT_SHA = "001c07019077794c1c33706cba5d0178f464aad07cf985650b2d55c3ebaa72d4"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def partition(names, count):
    ordered = sorted(names, key=lambda name: (hashlib.sha256(
        ("EXP234-target-chunks-v1:" + name).encode()).hexdigest(), name))
    chunks = [sorted(ordered[index::count]) for index in range(count)]
    assert max(map(len, chunks)) <= 15 and min(map(len, chunks)) >= 14
    assert set().union(*map(set, chunks)) == set(names)
    assert sum(map(len, chunks)) == len(names)
    return chunks


def main():
    plan = json.loads(PLAN.read_text())
    target = {source: plan["folds"][source]["target_oof"] for source in ("44b6", "6bba")}
    assert len(target["44b6"]) == 116 and len(target["6bba"]) == 59
    assert all(name.startswith("6bba_") for name in target["44b6"])
    assert all(name.startswith("44b6_") for name in target["6bba"])
    assert not set(target["44b6"]).intersection(target["6bba"])
    result = {"status": "PREREGISTERED_EXP234_TARGET_PARTITIONS_NO_METRICS",
              "experiment": "EXP234", "partition_rule": "SHA256(EXP234-target-chunks-v1:dataset_id), round-robin",
              "plan_sha256": sha(PLAN), "canonical_cohort_manifest_sha256": COHORT_SHA,
              "thresholds_selected": False, "target_labels_read": False,
              "directions": {source: {"target_embryo": "6bba" if source == "44b6" else "44b6",
                                      "movie_count": len(target[source]),
                                      "chunks": partition(target[source], 8 if source == "44b6" else 4)}
                             for source in ("44b6", "6bba")}}
    assert not OUTPUT.exists(), "Assignment is immutable; reconcile existing file"
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "sha256": sha(OUTPUT),
                      "chunks": {s: [len(c) for c in result["directions"][s]["chunks"]]
                                 for s in ("44b6", "6bba")}}))


if __name__ == "__main__":
    main()
