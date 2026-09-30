"""Build a local-only immutable EXP227 target116 scorer source bundle.

This command never contacts the cluster, opens target GEFF, or starts a scorer.
Remote staging is a separate future action after the eight-chunk coordinator
has completed and every no-label graph/release gate passes.
"""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "work/exp227_target6bba_scorer_local_v2_20260927"
RECEIPT = ROOT / "reports/exp227_target6bba_scorer_local_prepare_v2_20260927.json"
SOURCE_NAMES = ("score_exp227_target6bba_official.py", "score_exp214_paired.py",
                "score_exp223_official.py")
EXTRAS = {
    "exp223_config.json": ROOT / "reports/exp223_official_score_config_v2_20260922.json",
    "assignment.json": ROOT / "reports/exp234_target_chunk_assignment_20260926.json",
    "selection.json": ROOT / "reports/exp227_source_checkpoint_selection_20260927.json",
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
    assert selection["status"] == "SELECTED_EXP227_SOURCE_ONLY_CHECKPOINT"
    assert selection["selected_epoch"] == 10
    assert selection["checkpoint_sha256"] == (
        "df4ffd355201ae263bf3dfa57593daf9736eda89d5f7f24e9ef142790ba6bd79")
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
    receipt = {"status": "PREPARED_EXP227_TARGET6BBA_SCORER_LOCAL_ONLY",
               "bundle": str(BUNDLE), "local_manifest_sha256": manifest_sha,
               "source_hashes": manifest,
               "target_labels_read": False, "remote_stage_created": False,
               "remote_run_created": False, "target_score_computed": False,
               "evidence_class": "leakage-controlled reciprocal evaluation; historically exposed target labels"}
    with RECEIPT.open("x") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    print(json.dumps(prepare()))
