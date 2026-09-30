"""Build EXP238 local-only source plans and byte manifest; never calls SSH."""

import hashlib
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "work/exp238_source_peak_cache_local_20260927"
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
PREREG = ROOT / "reports/EXP238_SOURCE_PEAK_CACHE_PREREG_20260927.md"
SOURCE_CONFIG = ROOT / "work/source_inner_error_decomposition_v2_20260927/config.json"
SPECS = {
    "source44": {
        "experiment": "EXP227", "source_embryo": "44b6",
        "parent_name": "exp227_source_graph10_v1_20260927",
        "namespace": "exp238_source44_peak_cache_v1_20260927",
        "parent_plan_sha256": "de74ddc3526708d657779d64ba3731d7b8b09cf104a344bd83d1313f00c38349",
        "parent_manifest_sha256": "1f079e658a5dd0b505e469ac2f9251dd4ebc00db9010240742e7a913508832b1",
        "parent_status_sha256": "d445f1858ca5efe9561667a6e21362d753f047bb5bd7d507c209f076193cde7d",
        "score_receipt": "reports/exp227_source_graph10_score_20260927.json",
    },
    "source6": {
        "experiment": "EXP236", "source_embryo": "6bba",
        "parent_name": "exp236_source_graph10_v2_20260927",
        "namespace": "exp238_source6_peak_cache_v1_20260927",
        "parent_plan_sha256": "3633711ba0a3706be43c71907261afa5904db93d26cb1b29fb3dc19294474421",
        "parent_manifest_sha256": "92a9582cbe0f09d34d73865b1d09243971a94815c313a9b2225a7047388db3b2",
        "parent_status_sha256": "de1a4ca38f7d9f470eab6a993322e301b016e05f2175a6407559764633537acf",
        "score_receipt": "reports/exp236_source_graph10_score_20260927.json",
    },
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build() -> dict:
    assert sha(BUNDLE / "base/engine.py") == (
        "4db02fd767ee0e55e4a1ee902fb6ebc2d8683e07c0fe424ee85f7ef906c6dc44")
    assert sha(BUNDLE / "base/detection.py") == (
        "5dfb5c790c50665a5c3f6f46a53e249d92a40a74d860235513a08db0a0153cd3")
    from exp238_patch_horaz import patch_detection, patch_engine
    assert (BUNDLE / "patched/engine.py").read_bytes() == patch_engine((BUNDLE / "base/engine.py").read_bytes())
    assert (BUNDLE / "patched/detection.py").read_bytes() == patch_detection((BUNDLE / "base/detection.py").read_bytes())
    source = json.loads(SOURCE_CONFIG.read_text())
    assert source["status"] == "PREREGISTERED_SOURCE_INNER_DECOMPOSITION_LOCAL_ONLY"
    cohorts = {row["experiment"]: row for row in source["cohorts"]}
    plans = {}
    for cohort, spec in SPECS.items():
        base_plan = BUNDLE / "base" / (spec["experiment"].lower() + "_parent_plan.json")
        assert sha(base_plan) == spec["parent_plan_sha256"]
        original = json.loads(base_plan.read_text())
        row = cohorts[spec["experiment"]]
        assert row["source_embryo"] == spec["source_embryo"]
        assert row["verified_source_score_receipt_sha256"] == sha(ROOT / spec["score_receipt"])
        assert original["code"] == REMOTE + "/code/" + spec["parent_name"]
        assert original["output"] == REMOTE + "/runs/" + spec["parent_name"] + "/output"
        hashes = {item["dataset"]: item for item in row["graph_hashes"]}
        assert [item["dataset"] for item in original["movies"]] == row["ids"]
        movies = []
        for item in original["movies"]:
            dataset = item["dataset"]
            assert item["shape"] == [100, 64, 256, 256]
            movies.append({**item, "graph_csv_sha256": hashes[dataset]["csv_sha256"],
                           "graph_receipt_sha256": hashes[dataset]["receipt_sha256"]})
        plan = {
            "experiment": "EXP238_SOURCE_PEAK_CACHE", "cohort": cohort,
            "parent_experiment": spec["experiment"], "source_embryo": spec["source_embryo"],
            "parent_code_name": spec["parent_name"], "parent_run_name": spec["parent_name"],
            "parent_code": original["code"], "parent_run": original["output"].removesuffix("/output"),
            "parent_plan_sha256": spec["parent_plan_sha256"],
            "parent_manifest_sha256": spec["parent_manifest_sha256"],
            "parent_status_sha256": spec["parent_status_sha256"],
            "source_score_receipt_sha256": row["verified_source_score_receipt_sha256"],
            "source_manifest_sha256": original["source_manifest_sha256"],
            "checkpoint": original["checkpoint"],
            "checkpoint_sha256": original["checkpoint_sha256"],
            "data_root": original["data_root"],
            "code": REMOTE + "/code/" + spec["namespace"],
            "run": REMOTE + "/runs/" + spec["namespace"],
            "movies": movies, "floor": 0.075,
            "max_peaks_per_frame": 16384, "max_peaks_per_movie": 1000000,
            "max_peak_payload_bytes_all19": 228000000,
            "peak_dtype_itemsize": 12, "downsample_zyx": [1, 4, 4],
            "prereg_sha256": sha(PREREG),
            "patched_engine_sha256": sha(BUNDLE / "patched/engine.py"),
            "patched_detection_sha256": sha(BUNDLE / "patched/detection.py"),
            "runner_sha256": sha(ROOT / "scripts/run_exp238_peak_cache.py"),
            "source_labels_read": False, "target_data_opened": False,
        }
        destination = BUNDLE / cohort
        destination.mkdir(exist_ok=True)
        shutil.copyfile(base_plan, destination / "exp238_parent_plan.json")
        write_json(destination / "exp238_plan.json", plan)
        plans[cohort] = {"plan_sha256": sha(destination / "exp238_plan.json"),
                         "parent_plan_sha256": sha(destination / "exp238_parent_plan.json"),
                         "movies": len(movies)}
    paths = [BUNDLE / "base/engine.py", BUNDLE / "base/detection.py",
             BUNDLE / "base/exp227_parent_plan.json", BUNDLE / "base/exp236_parent_plan.json",
             BUNDLE / "patched/engine.py", BUNDLE / "patched/detection.py",
             ROOT / "scripts/exp238_patch_horaz.py", ROOT / "scripts/run_exp238_peak_cache.py",
             ROOT / "scripts/build_exp238_peak_cache_local.py",
             ROOT / "scripts/stage_exp238_peak_cache.py",
             ROOT / "scripts/launch_exp238_peak_cache.py",
             ROOT / "tests/test_exp238_source_peak_cache.py",
             PREREG, SOURCE_CONFIG]
    paths += [BUNDLE / cohort / name for cohort in SPECS
              for name in ("exp238_plan.json", "exp238_parent_plan.json")]
    manifest = {str(path.relative_to(ROOT)).replace("\\", "/"): sha(path) for path in paths}
    write_json(BUNDLE / "local_bundle_manifest.json", manifest)
    return {"status": "PREPARED_EXP238_LOCAL_ONLY", "plans": plans,
            "local_bundle_manifest_sha256": sha(BUNDLE / "local_bundle_manifest.json"),
            "remote_stage": False, "gpu_request": False, "labels_read": False}


def main() -> None:
    print(json.dumps(build(), sort_keys=True))


if __name__ == "__main__":
    main()
