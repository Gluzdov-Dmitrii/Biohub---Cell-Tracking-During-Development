"""Prepare EXP218: enable adaptive short-track rescue on target6bba public graph."""
import copy
import datetime
import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh

LOCAL = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
DATE = "20260915"
REMOTE_CODE = REMOTE + "/code/exp218_short_track_rescue_v1_20260915"
REMOTE_INPUT = REMOTE + "/code/exp218_short_track_rescue_inputs_20260915"
EXP214_PLAN_SHA = "cba8b54042cdb701fa7945f4521eb3ed335f5fc186fa32e803bbaef6ee6ad899"
GPU_A = "GPU-61c0078d-a4a6-37a2-3aba-0378e7794c46"
GPU_B = "GPU-04efb7bd-1f45-38cd-4a13-c79b6aeaa002"
OVERRIDES = [
    "BIOHUB_ADAPTIVE_SHORT_TRACK_RESCUE=1",
    "BIOHUB_SHORT_TRACK_RESCUE_MIN_LEN=4",
    "BIOHUB_SHORT_TRACK_RESCUE_MIN_MEAN_EDGE_PROB=0.88",
    "BIOHUB_SHORT_TRACK_RESCUE_MAX_MEAN_EDGE_DIST_UM=3.0",
    "BIOHUB_SHORT_TRACK_RESCUE_MAX_NODES_FRAC=0.012",
    "BIOHUB_SHORT_TRACK_RESCUE_MAX_NODES_ABS=120",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json_once(path: Path, payload: dict) -> dict:
    text = json.dumps(payload, indent=2) + "\n"
    if path.exists():
        current = json.loads(path.read_text())
        if json.dumps(current, sort_keys=True) != json.dumps(payload, sort_keys=True):
            raise AssertionError(f"Existing file differs: {path}")
        return current
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(text)
    return payload


def remove_flag(arguments: list[str], flag: str) -> list[str]:
    cleaned = []
    index = 0
    while index < len(arguments):
        if arguments[index] == flag:
            index += 2
            continue
        cleaned.append(arguments[index])
        index += 1
    return cleaned


def set_argument(arguments: list[str], flag: str, value: str) -> None:
    arguments[arguments.index(flag) + 1] = value


def preregister() -> dict:
    payload = {
        "experiment": "EXP218",
        "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "stage": "short_track_rescue_target6bba",
        "track": "PRIVATE_ROBUST_DIAGNOSTIC_NO_POST",
        "parent": {
            "experiment": "EXP214 gapfix",
            "arm": "90/60 public graph paired175",
            "score": 0.7427291486246141,
            "target6bba_score": 0.7318060132031643,
            "target44b6_score": 0.8052068737218,
        },
        "evidence": {
            "exp216_public_endpoint_fraction": 0.573127,
            "exp216_public_target6bba_edge_fn": 16043,
            "exp216_public_target6bba_endpoint_fraction": 0.568784,
            "exp217_full_source44_regressed": True,
        },
        "hypothesis": (
            "A conservative adaptive short-track rescue can recover high-confidence "
            "target6bba endpoint components removed by the public graph's short-track "
            "filter, while strict mean edge probability, distance, and node-count caps "
            "avoid the coarse-count regression seen in EXP198."
        ),
        "overrides": OVERRIDES,
        "candidate_dataflow": (
            "Run five source44b6 -> target6bba public inference shards from runtime zarr "
            "images without target labels. Reuse the frozen EXP214 target44b6 public shards. "
            "Only after all candidate receipts pass no-metric gates, open labels once through "
            "score_exp214_paired.py on the exact 175 movies."
        ),
        "promotion_gate": (
            "Promote only if full175 candidate-baseline delta is positive, target6bba improves, "
            "edge FP does not grow enough to dominate endpoint FN reductions, and no graph/hash "
            "gate fails."
        ),
        "submission_authority": "none",
    }
    return write_json_once(LOCAL / "reports/exp218_short_track_rescue_preregistration_20260915.json", payload)


def stage_remote_code() -> dict:
    public_source = (LOCAL / "scripts/run_exp214_public_fold.py").read_text()
    remote = r'''
import hashlib
import json
import shutil
from pathlib import Path

root = Path(__ROOT__)
code = Path(__CODE__)
inp = Path(__INPUT__)
assert not code.exists(), "Existing EXP218 code dir; reconcile before retry"
assert not inp.exists(), "Existing EXP218 input dir; reconcile before retry"
shutil.copytree(root / "code/exp214_inference_v8_20260914", code, symlinks=True)
inp.mkdir(parents=True)
(code / "run_exp214_public_fold.py").write_text(__PUBLIC_SOURCE__)
manifest_path = code / "code_manifest.json"
manifest = json.loads(manifest_path.read_text())
manifest["run_exp214_public_fold.py"] = hashlib.sha256((code / "run_exp214_public_fold.py").read_bytes()).hexdigest()
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
receipt = {
    "status": "PASS_EXP218_CODE_STAGED",
    "code": str(code),
    "input": str(inp),
    "base_code": str(root / "code/exp214_inference_v8_20260914"),
    "run_exp214_public_fold_sha256": manifest["run_exp214_public_fold.py"],
    "override_capability": "--override-env BIOHUB_*",
    "target_labels_read": False,
}
print(json.dumps(receipt))
'''.replace("__ROOT__", repr(REMOTE)).replace("__CODE__", repr(REMOTE_CODE)).replace(
        "__INPUT__", repr(REMOTE_INPUT)
    ).replace("__PUBLIC_SOURCE__", repr(public_source))
    return ssh("nsu-quadro", "python3 -", remote)


def build_configs() -> list[dict]:
    configs = []
    for index in range(5):
        tag = f"44b6_{index:02}"
        base_path = LOCAL / f"reports/exp214_gapfix_paired_new90_{tag}_config_20260914.json"
        config = json.loads(base_path.read_text())
        arguments = remove_flag(list(config["arguments"]), "--reuse-manifest")
        run = REMOTE + f"/runs/exp218_short_track_rescue_{tag}_20260915"
        gpu, cpu = (GPU_A, "0-7") if index in (0, 2, 4) else (GPU_B, "8-15")
        config.update(
            experiment="EXP218",
            lease_id=f"biohub-exp218-short-track-rescue-{tag}-20260915",
            token=f"exp218-short-track-rescue-{tag}",
            gpu=gpu,
            cpu_affinity=cpu,
            code=REMOTE_CODE,
            run=run,
            script="run_exp214_public_fold.py",
            scope=(
                "EXP218 target6bba public graph only: enable conservative adaptive "
                "short-track rescue; no target metrics or POST during inference."
            ),
        )
        set_argument(arguments, "--output", run + "/output")
        for override in OVERRIDES:
            arguments.extend(["--override-env", override])
        config["arguments"] = arguments
        path = LOCAL / f"reports/exp218_short_track_rescue_{tag}_config_20260915.json"
        write_json_once(path, config)
        configs.append({"tag": tag, "path": str(path), "sha256": sha(path)})
    return configs


def build_manifest() -> dict:
    baseline = json.loads((LOCAL / "reports/exp214_gapfix_new90_manifest_20260914.json").read_text())
    assert baseline["training_plan_sha256"] == EXP214_PLAN_SHA
    manifest = {
        "training_plan_sha256": EXP214_PLAN_SHA,
        "movies": baseline["movies"],
        "scope": (
            "EXP218 conservative adaptive short-track rescue versus EXP214 gapfix90 public baseline. "
            "Candidate changes only source44b6 -> target6bba public graph shards; target44b6 "
            "source6bba shards are reused unchanged from the baseline."
        ),
        "overrides": OVERRIDES,
        "arms": {},
    }
    baseline_public = copy.deepcopy(baseline["arms"]["public"])
    manifest["arms"]["baseline_gapfix90_public"] = copy.deepcopy(baseline_public)
    candidate = []
    replaced = 0
    reused = 0
    for part in baseline_public:
        if all(movie.startswith("6bba_") for movie in part["movies"]):
            tag = f"44b6_{replaced:02}"
            candidate.append(
                {
                    "receipt": REMOTE + f"/runs/exp218_short_track_rescue_{tag}_20260915/output/inference_receipt.json",
                    "csv": REMOTE + f"/runs/exp218_short_track_rescue_{tag}_20260915/output/submission.csv",
                    "movies": part["movies"],
                }
            )
            replaced += 1
        else:
            candidate.append(part)
            reused += 1
    assert replaced == 5 and reused == 3
    manifest["arms"]["candidate_short_track_rescue_public"] = candidate
    return write_json_once(LOCAL / "reports/exp218_short_track_rescue_manifest_20260915.json", manifest)


def stage_remote_manifest(manifest: dict) -> dict:
    source = (
        "import json\n"
        "from pathlib import Path\n"
        f"out=Path({REMOTE_INPUT!r})\n"
        "out.mkdir(parents=True, exist_ok=True)\n"
        f"payload={manifest!r}\n"
        "text=json.dumps(payload, indent=2)+'\\n'\n"
        "path=out/'manifest.json'\n"
        "assert not path.exists() or path.read_text()==text\n"
        "path.write_text(text)\n"
        "print(json.dumps({'status':'PASS_EXP218_MANIFEST_STAGED','path':str(path),'arms':list(payload['arms'])}))\n"
    )
    return ssh("nsu-quadro", "python3 -", source)


def main() -> None:
    preregistration = preregister()
    code = stage_remote_code()
    write_json_once(LOCAL / "reports/exp218_short_track_rescue_code_staging_20260915.json", code)
    configs = build_configs()
    manifest = build_manifest()
    remote_manifest = stage_remote_manifest(manifest)
    result = {
        "status": "PASS_EXP218_SHORT_TRACK_RESCUE_PREPARED",
        "preregistration_experiment": preregistration["experiment"],
        "code": code,
        "configs": configs,
        "manifest": str(LOCAL / "reports/exp218_short_track_rescue_manifest_20260915.json"),
        "remote_manifest": remote_manifest,
        "target_labels_read": False,
        "kaggle_post": False,
    }
    write_json_once(LOCAL / "reports/exp218_short_track_rescue_prepare_20260915.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
