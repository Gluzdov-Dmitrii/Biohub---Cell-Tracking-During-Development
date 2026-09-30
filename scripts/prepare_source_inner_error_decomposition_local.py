"""Seal the local-only EXP227/EXP236 source-inner decomposition bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "work/source_inner_error_decomposition_20260927"
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
METRIC_SOURCE = ROOT / "work/exp234_current_organizer_v1/tracking_cellmot_official"
METRIC_SHAS = {
    "__init__.py": "7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6",
    "metrics.py": "cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444",
    "division_metrics.py": "0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9",
}
IMAGE_AUDIT_SHA = "7d49f54f6a2bb80c8148cbd2e110c23f24fe8c4dd5fddc363b6755418da87f1c"
EXP227_IDS = (
    "44b6_996155de", "44b6_c50204e0", "44b6_c96cfa10", "44b6_551a5dba",
    "44b6_90724892", "44b6_f28707c6", "44b6_deabac95", "44b6_341df25f",
)
EXP236_IDS = (
    "6bba_372c8cb8", "6bba_67ebd073", "6bba_76db78c1",
    "6bba_786893ac", "6bba_825bd1c6", "6bba_a5e926bb",
    "6bba_b329af44", "6bba_b693381b", "6bba_bb9f20c3",
    "6bba_f20478e9", "6bba_f4ae811c",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def cohort(experiment: str, ids: tuple[str, ...]) -> dict:
    stem = experiment.lower()
    score_path = ROOT / f"reports/{stem}_source_graph10_score_20260927.json"
    verified = json.loads(score_path.read_text())
    prepare = read(f"reports/{stem}_source_graph10_scorer_prepare_20260927.json")
    assert verified["status"] == f"VERIFIED_{experiment}_SOURCE10_OFFICIAL"
    assert verified["rows"] == len(ids)
    assert verified["result_sha256"] and verified["gate_sha256"]
    assert prepare["config"]["checkpoint_sha256"] == verified["checkpoint_sha256"]
    assert prepare["config"]["inference_run"].startswith(REMOTE + "/runs/")
    assert prepare["config"]["data_dir"] == REMOTE + "/data/exp213_source_view_20260912"
    if experiment == "EXP227":
        prior = read("reports/exp227_source10_fixed_node_attribution_20260927.json")
        assert prior["source_score"] == verified["source_score"]
        assert [row["dataset"] for row in prior["inputs"]["rows"]] == list(ids)
        hashes = [{"dataset": row["dataset"], "csv_sha256": row["graph_csv_sha256"],
                   "receipt_sha256": row["graph_receipt_sha256"]}
                  for row in prior["inputs"]["rows"]]
        labels = {row["dataset"]: row["gt_geff_tree_sha256"]
                  for row in prior["inputs"]["rows"]}
        assert all(row["gt_files"] == 21 for row in prior["inputs"]["rows"])
        assert prepare["stage"]["manifest_sha256"] == prior["inputs"]["scorer_manifest_sha256"]
        assert prepare["stage"]["score_config_sha256"] == prior["inputs"]["score_config_sha256"]
        expected_status = "PASS_EXP227_SOURCE_GRAPH10_OFFICIAL"
    else:
        hashes = prepare["preflight"]["hashes"]
        labels = {}  # no prior individual source6bba GEFF digests are in the sealed scorer receipt
        assert [row["dataset"] for row in hashes] == list(ids)
        assert hashes == prepare["config"]["inference_graph_hashes"]
        expected_status = "PASS_EXP236_SOURCE_GRAPH10_OFFICIAL"
    return {
        "experiment": experiment,
        "source_embryo": "44b6" if experiment == "EXP227" else "6bba",
        "ids": list(ids),
        "verified_source_score_receipt_sha256": sha(score_path),
        "source_scorer_prepare_receipt_sha256": sha(ROOT / f"reports/{stem}_source_graph10_scorer_prepare_20260927.json"),
        "legacy_source_score": verified["source_score"],
        "score_status": expected_status,
        "checkpoint_sha256": verified["checkpoint_sha256"],
        "scorer_code": prepare["stage"]["code"],
        "scorer_run": str(PurePosixPath(prepare["config"]["output"]).parent),
        "scorer_manifest_sha256": prepare["stage"]["manifest_sha256"],
        "scorer_config_sha256": prepare["stage"]["score_config_sha256"],
        "graph_run": prepare["config"]["inference_run"],
        "graph_hashes": hashes,
        "score_result_sha256": verified["result_sha256"],
        "score_gate_sha256": verified["gate_sha256"],
        "geff_tree_hashes": labels,
    }


def main() -> None:
    assert (BUNDLE / "audit_source_inner.py").is_file()
    output_package = BUNDLE / "tracking_cellmot_official"
    output_package.mkdir(exist_ok=True)
    for name, digest in METRIC_SHAS.items():
        source = METRIC_SOURCE / name
        assert sha(source) == digest
        shutil.copyfile(source, output_package / name)
    helper = ROOT / "scripts/check_current_organizer_metric_runtime.py"
    shutil.copyfile(helper, BUNDLE / helper.name)
    image_audit = ROOT / "reports/exp234_current_image_scale_audit_20260927.json"
    assert sha(image_audit) == IMAGE_AUDIT_SHA
    shutil.copyfile(image_audit, BUNDLE / image_audit.name)

    config = {
        "status": "PREREGISTERED_SOURCE_INNER_DECOMPOSITION_LOCAL_ONLY",
        "source_only": True,
        "organizer_commit": "075fc5f5a52d11077f9dc2b074644618f26939e2",
        "tracksdata_commit": "e13cf379b5127deeb8301ce56410fda35b5a3cf9",
        "output": REMOTE + "/runs/source_inner_error_decomposition_v1_20260927/output",
        "cohorts": [cohort("EXP227", EXP227_IDS), cohort("EXP236", EXP236_IDS)],
    }
    assert set(config["cohorts"][0]["ids"]).isdisjoint(config["cohorts"][1]["ids"])
    (BUNDLE / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    files = ["audit_source_inner.py", "config.json", helper.name, image_audit.name]
    files += [f"tracking_cellmot_official/{name}" for name in METRIC_SHAS]
    manifest = {"status": "SEALED_SOURCE_INNER_ERROR_DECOMPOSITION_LOCAL_ONLY",
                "files": {name: sha(BUNDLE / name) for name in files}}
    (BUNDLE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"bundle": str(BUNDLE), "manifest_sha256": sha(BUNDLE / "manifest.json"),
                      "files": len(files), "source_movies": sum(len(c["ids"]) for c in config["cohorts"])},
                     indent=2))


if __name__ == "__main__":
    main()
