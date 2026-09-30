"""Build the EXP209 reconstructed-graph scorer bundle locally, without labels.

This script copies pinned sources and writes a reviewable immutable manifest.
It does not stage, launch, import a metric, or open a GEFF tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPERIMENT = "EXP209_RECONSTRUCTED_CURRENT_SCORER_V1"
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
RECON_NAME = "exp209_current_metric_reconstruction_v1_20260927"
SCORE_NAME = "exp209_reconstructed_current_scorer_v1_20260927"
RECON_BUNDLE_SHA = "cdf49fad597f1dcc47e65d841cc894ed2be439f45f4bfe1838e790b390c8a311"
RECON_CONTRACT_SHA = "3860dce507c02b49386414a26c51071f6ff993e8b49476dc46e2b232973e8dd0"
RECON_GATE_SHA = "8379ffc4435b01d0a8b7c90087302001b0b7738914e84fdd0286b888e8ff32f1"
HISTORICAL_RESULT_SHA = "bcc57aeef14a9419daab17ca10398774d229f499926f53176948eab331c05e0c"
SOURCES = {
    "score_exp209_reconstructed_current_v1.py": ("scripts/score_exp209_reconstructed_current_v1.py", None),
    "verify_exp209_reconstruction_graphs_v1.py": ("scripts/verify_exp209_reconstruction_graphs_v1.py",
        "2bf0b5cb536d76bab57bfddf3033b749a5af5871bfc8cb265d426b16a60f03d2"),
    "run_exp209_reconstruction_chunk_v1.py": ("scripts/run_exp209_reconstruction_chunk_v1.py",
        "8bebdbdf27b94a254efe40d3d9db60241841c2b3c98370a765aee758b7f31597"),
    "score_exp214_paired.py": ("scripts/score_exp214_paired.py",
        "04cf48b737980ae8a1c2d9cecbcf2e07d92cf53cab18ad9ef0787506fd4417c4"),
    "score_exp223_official.py": ("scripts/score_exp223_official.py",
        "3341f8675ab641aba7e92733730463633ded92505cc6d1b66acbe5237e56dab4"),
    "score_current_metric_lightweight.py": ("scripts/score_current_metric_lightweight.py",
        "d37e986e59ace5f10e363e058784b0b03ea19919823cd3941707514ad04034b0"),
    "check_current_organizer_metric_runtime.py": ("scripts/check_current_organizer_metric_runtime.py",
        "616d26d5986e312b57f32f39d1fdb90684961c00eb14e1a44df7fe4ba19494c2"),
    "legacy_official/__init__.py": ("outputs/research/support_pack/repo/src/biohub_tracking/__init__.py",
        "26a18d8da84e40da73281a48ebc3017d847a2e57431ab63e8629d2109e6e8571"),
    "legacy_official/metrics.py": ("outputs/research/support_pack/repo/src/biohub_tracking/metrics.py",
        "31baf45b54c78f68bab4f65dd8f4b38bca702abb644171c6df7c46cdeef55d83"),
    "legacy_official/division_metrics.py": ("outputs/research/support_pack/repo/src/biohub_tracking/division_metrics.py",
        "d1cf1e0a43009d02174f1699ce2aa28458a2220ac4b521731d3bcf31cf8c76be"),
    "current_official/__init__.py": ("work/exp236_target44b6_scorer_local_v2_20260927/current_official/__init__.py",
        "de33668aee4fd1822a11989b432a7ba6c4b36fd2993ec8f564a63d427cde05de"),
    "current_official/metrics.py": ("work/x138_provenance/official_metric/metrics_pinned.py",
        "cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444"),
    "current_official/division_metrics.py": ("work/x138_provenance/official_metric/division_metrics_pinned.py",
        "0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9"),
}


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def require(value: bool, reason: str) -> None:
    if not value:
        raise ValueError(reason)


def prepare(workspace: Path, destination: Path) -> dict:
    workspace = workspace.resolve()
    require(destination.is_absolute() and not destination.exists(),
            "scorer bundle destination must be new and absolute")
    recon = workspace / "work/exp209_current_metric_reconstruction_v1_local_20260927/bundle"
    require(sha(recon / "bundle_manifest.json") == RECON_BUNDLE_SHA,
            "local reconstruction bundle manifest changed")
    require(sha(recon / "contract.json") == RECON_CONTRACT_SHA,
            "local reconstruction contract changed")
    contract = json.loads((recon / "contract.json").read_text(encoding="utf-8"))
    require(contract["run_root"] == f"{REMOTE}/runs/{RECON_NAME}" and
            contract["code_dir"] == f"{REMOTE}/code/{RECON_NAME}" and
            contract["data_root"] == f"{REMOTE}/data/honest195_missing/train",
            "reconstruction remote namespace/data root changed")
    historical = recon / "historical_result.json"
    require(sha(historical) == HISTORICAL_RESULT_SHA,
            "archived EXP209 selected result changed")
    original = json.loads(historical.read_text(encoding="utf-8"))
    require(original["status"] == "PASS_FROZEN_CONFIRMATION_ASSEMBLY" and
            len(original["directions"]["forward"]["selected_rows"]) == 116 and
            len(original["directions"]["reverse"]["selected_rows"]) == 59,
            "archived EXP209 selected-row cohort changed")

    payloads = {}
    for name, (relative, expected) in SOURCES.items():
        source = workspace / relative
        data = source.read_bytes()
        digest = sha_bytes(data)
        require(expected is None or digest == expected, f"source SHA changed: {relative}")
        payloads[name] = (data, digest)
    destination.mkdir(parents=True, exist_ok=False)
    rows = []
    for name, (data, digest) in payloads.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        rows.append({"name": name, "sha256": digest, "bytes": len(data)})
    config = {
        "experiment": EXPERIMENT,
        "reconstruction_run_root": contract["run_root"],
        "reconstruction_code_dir": contract["code_dir"],
        "reconstruction_contract": f"{contract['code_dir']}/contract.json",
        "reconstruction_bundle_manifest_sha256": RECON_BUNDLE_SHA,
        "reconstruction_contract_sha256": RECON_CONTRACT_SHA,
        "reconstruction_gate_sha256": RECON_GATE_SHA,
        "scorer_code_dir": f"{REMOTE}/code/{SCORE_NAME}",
        "output": f"{REMOTE}/runs/{SCORE_NAME}",
        "environment_python": f"{REMOTE}/envs/current-organizer-py311-e13cf-v1/bin/python",
        "metric_repo_commit": "075fc5f5a52d11077f9dc2b074644618f26939e2",
        "current_metrics_sha256": "cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444",
        "current_division_sha256": "0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9",
        "tracksdata_commit": "e13cf379b5127deeb8301ce56410fda35b5a3cf9",
        "historical_exp209_score": 0.6815218332750073,
        "original_final_graph_hashes_available": False,
        "evidence_class": "leakage-controlled reciprocal evaluation; historically exposed target labels",
    }
    config_data = (json.dumps(config, indent=2, sort_keys=True) + "\n").encode("utf-8")
    (destination / "config.json").write_bytes(config_data)
    rows.append({"name": "config.json", "sha256": sha_bytes(config_data), "bytes": len(config_data)})
    manifest = {"experiment": EXPERIMENT, "status": "PREPARED_LOCAL_ONLY_NO_LABELS",
                "files": sorted(rows, key=lambda row: row["name"])}
    manifest_data = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    (destination / "bundle_manifest.json").write_bytes(manifest_data)
    return {"status": "PREPARED_EXP209_RECONSTRUCTED_SCORER_V1_LOCAL_ONLY",
            "bundle": str(destination),
            "bundle_manifest_sha256": sha_bytes(manifest_data),
            "config_sha256": sha_bytes(config_data),
            "source_hashes": {row["name"]: row["sha256"] for row in rows},
            "reconstruction_gate_sha256": RECON_GATE_SHA,
            "historical_exp209_selected_rows_sha256": HISTORICAL_RESULT_SHA,
            "target_geff_opened": False, "metric_executed": False,
            "remote_stage_created": False, "remote_run_created": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    require(not args.receipt.exists(), "local preparation receipt already exists")
    result = prepare(args.workspace, args.destination)
    args.receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"],
                      "bundle_manifest_sha256": result["bundle_manifest_sha256"],
                      "config_sha256": result["config_sha256"]}))


if __name__ == "__main__":
    main()
