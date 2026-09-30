"""Build a local-only immutable EXP227 target116 scorer source bundle.

This command never contacts the cluster, opens target GEFF, or starts a scorer.
Remote staging is a separate future action after the eight-chunk coordinator
has completed and every no-label graph/release gate passes.
"""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "work/exp227_target6bba_scorer_local_v4_20260927"
RECEIPT = ROOT / "reports/exp227_target6bba_scorer_local_prepare_v4_20260927.json"
FINALIZER = ROOT / "scripts/finalize_exp227_target6bba_waitsafe_v3.py"
FINALIZER_SHA = "ac368bdedade09531f7ae7dc0d865792a04b22b44514e4432c307344a4e61dc6"
SOURCE_NAMES = ("score_exp227_target6bba_current_v4.py", "score_exp214_paired.py",
                "score_exp223_official.py", "score_current_metric_lightweight.py",
                "check_current_organizer_metric_runtime.py")
EXTRAS = {
    "exp223_config.json": ROOT / "reports/exp223_official_score_config_v2_20260922.json",
    "assignment.json": ROOT / "reports/exp234_target_chunk_assignment_20260926.json",
    "selection.json": ROOT / "reports/exp227_source_checkpoint_selection_20260927.json",
    "successor_prepare.json": ROOT / "reports/exp227_target6bba_chunk07_waitsafe_v3_local_prepare_20260927.json",
    "successor_stage.json": ROOT / "reports/exp227_target6bba_chunk07_waitsafe_v3_stage_20260927.json",
    "successor_config.json": ROOT / "reports/exp227_target6bba_chunk07_waitsafe_v3_config_20260927.json",
    "baseline_reference.json": ROOT / "outputs/research/exp214_gapfix_score175_20260914/output/new90/metrics.json",
    "image_scale_audit.json": ROOT / "reports/exp234_current_image_scale_audit_20260927.json",
    "current_official/__init__.py": ROOT / "scripts/exp227_current_official_init.py",
    "current_official/metrics.py": ROOT / "work/x138_provenance/official_metric/metrics_pinned.py",
    "current_official/division_metrics.py": ROOT / "work/x138_provenance/official_metric/division_metrics_pinned.py",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expected_files():
    return {**{name: ROOT / "scripts" / name for name in SOURCE_NAMES}, **EXTRAS}


def verify_bundle(path=BUNDLE):
    path = Path(path)
    manifest_path = path / "local_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    assert set(manifest) == set(expected_files())
    assert {item.relative_to(path).as_posix() for item in path.rglob("*") if item.is_file()} == (
        set(manifest) | {"local_manifest.json"})
    for name, digest in manifest.items():
        assert sha(path / name) == digest
        assert sha(expected_files()[name]) == digest
    return sha(manifest_path), manifest


def prepare():
    assert not BUNDLE.exists() and not RECEIPT.exists(), "Existing local bundle requires review"
    assignment = json.loads(EXTRAS["assignment.json"].read_text())
    selection = json.loads(EXTRAS["selection.json"].read_text())
    assert sha(EXTRAS["assignment.json"]) == (
        "9e9f15ad5e3497cd74d3c91b10f19a53686deb8f16412d3b239c7455d9f749f4")
    assert assignment["directions"]["44b6"]["movie_count"] == 116
    assert len(assignment["directions"]["44b6"]["chunks"]) == 8
    assert sha(EXTRAS["successor_prepare.json"]) == (
        "9bae3cfe842e9772aadf07bce8572fc84802ed54af0a84838fad450dfa24e0d8")
    successor = json.loads(EXTRAS["successor_prepare.json"].read_text())
    assert successor["status"] == "PREPARED_EXP227_CHUNK07_WAITSAFE_V3_LOCAL_ONLY"
    assert successor["movies"] == assignment["directions"]["44b6"]["chunks"][7]
    assert successor["identity"]["token"] == "exp227_target6bba_chunk07_v3_20260927"
    assert successor["identity"]["lease_id"] == "exp227-target6bba-chunk07-v3-20260927"
    assert successor["plan_sha256"] == "9e87d40ad89816f171f32bd888e55421531486c86cde9c8af0ba8d196af8031a"
    assert successor["runner_sha256"] == "43e0b87893242d2fcf830d514f184ed3da8485ebebf3d32dee7ace370f0cec35"
    assert successor["remote_staged"] is False and successor["target_labels_read"] is False
    assert sha(EXTRAS["successor_stage.json"]) == (
        "9f27d647ef0f10bb41a228ecebb4b64599b2218d241258a7dc6fc2f59815f08f")
    staged = json.loads(EXTRAS["successor_stage.json"].read_text())
    assert staged["status"] == "STAGED_EXP227_CHUNK07_WAITSAFE_V3_NO_LABELS"
    assert staged["code"] == successor["identity"]["code"]
    assert staged["run"] == successor["identity"]["run"]
    assert staged["lease_id"] == successor["identity"]["lease_id"]
    assert staged["plan_sha256"] == successor["plan_sha256"]
    assert staged["manifest_sha256"] == (
        "b17d5baf85ddde704b863753bea2eaae9e5684405024c17c39aaf69d1c5d7e06")
    assert staged["staged"]["runner_sha256"] == successor["runner_sha256"]
    assert staged["runner_contract"] == successor["actual_runner_contract"]
    assert staged["target_labels_read"] is False
    assert sha(EXTRAS["successor_config.json"]) == (
        "6452ba4a4d41f28068559f940144a141ff4c5ed1bd388183a625f864f580c8db")
    config = json.loads(EXTRAS["successor_config.json"].read_text())
    for key in ("code", "run", "lease_id", "token"):
        assert config[key] == successor["identity"][key]
    assert config["arguments"] == [staged["code"] + "/plan.json", "--plan-sha256",
                                   successor["plan_sha256"]]
    assert sha(FINALIZER) == FINALIZER_SHA and not (
        ROOT / "reports/exp227_target6bba_all116_waitsafe_v3_final_20260927.json").exists()
    assert selection["status"] == "SELECTED_EXP227_SOURCE_ONLY_CHECKPOINT"
    assert selection["selected_epoch"] == 10
    assert selection["checkpoint_sha256"] == (
        "df4ffd355201ae263bf3dfa57593daf9736eda89d5f7f24e9ef142790ba6bd79")
    assert sha(EXTRAS["baseline_reference.json"]) == (
        "c2746b182d061fede4a255056cf177a245ad365485f46ba9f376cd240013b2e5")
    assert sha(EXTRAS["image_scale_audit.json"]) == (
        "7d49f54f6a2bb80c8148cbd2e110c23f24fe8c4dd5fddc363b6755418da87f1c")
    baseline = json.loads(EXTRAS["baseline_reference.json"].read_text())
    target = [r for r in baseline["rows"]["public"] if r["dataset"].startswith("6bba_")]
    assert len(target) == 116 and {r["dataset"] for r in target} == {
        name for group in assignment["directions"]["44b6"]["chunks"] for name in group}
    assert len(baseline["input_hashes"]["public"]) == 8
    assert len([p for p in baseline["input_hashes"]["public"] if "_6bba_" in p["csv"]]) == 3
    assert sha(EXTRAS["current_official/metrics.py"]) == (
        "cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444")
    assert sha(EXTRAS["current_official/division_metrics.py"]) == (
        "0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9")
    BUNDLE.mkdir(parents=True)
    for name, source in expected_files().items():
        (BUNDLE / name).parent.mkdir(parents=True, exist_ok=True)
        (BUNDLE / name).write_bytes(source.read_bytes())
    manifest = {name: sha(BUNDLE / name) for name in sorted(expected_files())}
    (BUNDLE / "local_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    manifest_sha, _ = verify_bundle()
    receipt = {"status": "PREPARED_EXP227_TARGET6BBA_CURRENT_SCORER_V4_LOCAL_ONLY",
               "bundle": str(BUNDLE), "local_manifest_sha256": manifest_sha,
               "source_hashes": manifest,
               "successor_prepare_sha256": sha(EXTRAS["successor_prepare.json"]),
               "successor_stage_sha256": sha(EXTRAS["successor_stage.json"]),
               "successor_config_sha256": sha(EXTRAS["successor_config.json"]),
               "successor_identity": successor["identity"],
               "future_finalizer_source_sha256": sha(FINALIZER),
               "final_all116_receipt_written": False,
               "baseline_metrics_sha256": sha(EXTRAS["baseline_reference.json"]),
               "baseline_target_input_hashes": [p for p in baseline["input_hashes"]["public"]
                                                if "_6bba_" in p["csv"]],
               "baseline_target_rows_sha256": hashlib.sha256(json.dumps(target, sort_keys=True,
                   separators=(",", ":")).encode()).hexdigest(),
               "target_labels_read": False, "remote_stage_created": False,
               "remote_run_created": False, "target_score_computed": False,
               "evidence_class": "leakage-controlled reciprocal evaluation; historically exposed target labels"}
    with RECEIPT.open("x") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    print(json.dumps(prepare()))
