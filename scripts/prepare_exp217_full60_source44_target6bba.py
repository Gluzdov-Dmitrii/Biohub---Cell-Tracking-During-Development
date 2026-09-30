"""Prepare EXP217: test EXP215 full-source44 primary on target6bba OOF.

This stages one new source44b6 bundle and five target6bba paired inference
configs. Target44b6 graph shards are intentionally reused from the frozen
EXP214 gapfix90 baseline in the later scoring manifest.
"""
import copy
import datetime
import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh

LOCAL = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
DATE = "20260915"
REMOTE_INPUT = REMOTE + "/code/exp217_full60_source44_target6bba_inputs_20260915"
EXP214_PLAN_SHA = "cba8b54042cdb701fa7945f4521eb3ed335f5fc186fa32e803bbaef6ee6ad899"
EXP215_PLAN_SHA = "99258515deb4906af43c0231432adeedfb5819077b1e03460e40b424a121e5fe"
EXP215_BEST_SHA = "d7bc45e5151842263e0b008bf152adc26105cf6e76b7722c46fe38a8e79ce3b4"
EXP215_STATUS_SHA = "285f6d8dd2c847a90779fc72320079543842c34bcd0190c9482ce86d1df57aa0"
EXP215_SOURCE_SCORE = 0.9480773840263902
GPU_A = "GPU-61c0078d-a4a6-37a2-3aba-0378e7794c46"
GPU_B = "GPU-04efb7bd-1f45-38cd-4a13-c79b6aeaa002"


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


def without_reuse_manifest(arguments: list[str]) -> list[str]:
    cleaned = []
    index = 0
    while index < len(arguments):
        if arguments[index] == "--reuse-manifest":
            index += 2
            continue
        cleaned.append(arguments[index])
        index += 1
    return cleaned


def set_argument(arguments: list[str], flag: str, value: str) -> None:
    arguments[arguments.index(flag) + 1] = value


def preregister() -> dict:
    payload = {
        "experiment": "EXP217",
        "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "stage": "full60_source44_target6bba",
        "track": "PRIVATE_ROBUST_DIAGNOSTIC_NO_POST",
        "parent": {
            "experiment": "EXP214 gapfix",
            "arm": "90/60 public graph paired175",
            "score": 0.7427291486246141,
            "target6bba_score": 0.7318060132031643,
            "target44b6_score": 0.8052068737218,
        },
        "hypothesis": (
            "Replacing only the source44b6 primary detector/linker checkpoint "
            "with the EXP215 full-cache source-selected epoch59 checkpoint "
            "improves target6bba OOF versus the EXP214 gapfix90 baseline. "
            "Target44b6 shards, secondary checkpoints, center checkpoints, "
            "candidate graph code and metric code remain fixed."
        ),
        "source_only_signal": {
            "exp215_best_sha256": EXP215_BEST_SHA,
            "selected_epoch": 59,
            "source_selection_score": EXP215_SOURCE_SCORE,
            "target_labels_opened": False,
        },
        "candidate_dataflow": (
            "Run paired public/local graph inference for the five source44b6 "
            "movie shards only, using runtime zarr images and no target labels. "
            "After all five receipts and existing target44b6 baseline receipts "
            "pass SHA gates, open labels once through score_exp214_paired.py."
        ),
        "promotion_gate": (
            "Promote only if the paired full175 score improves without a "
            "target6bba regression and without a material target44b6 artifact "
            "from the reused baseline side."
        ),
        "submission_authority": "none",
    }
    path = LOCAL / "reports/exp217_full60_source44_target6bba_preregistration_20260915.json"
    if path.exists():
        return json.loads(path.read_text())
    return write_json_once(path, payload)


def stage_remote_bundle() -> dict:
    source = r'''
import copy
import hashlib
import json
from pathlib import Path

root = Path(ROOT)
out = Path(REMOTE_INPUT)
out.mkdir(parents=True, exist_ok=True)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

parent_bundle_path = root / "code/exp214_eval90_inputs_20260913/44b6_bundle.json"
old = json.loads(parent_bundle_path.read_text())
assert old["source_embryo"] == "44b6"
assert old["training_plan_sha256"] == EXP214_PLAN_SHA
for role in ("secondary", "center"):
    assert sha(old[role]["path"]) == old[role]["sha256"], role

parent = root / "runs/exp213_refit44b6_s2026_p01_20260912/output"
status_path = parent / "status.json"
history_path = parent / "history.json"
status = json.loads(status_path.read_text())
history = json.loads(history_path.read_text())
assert status["target_data_opened"] is False
assert status["contract"]["fold"] == "44b6"
assert status["contract"]["seed"] == 2026
assert status["contract"]["plan_sha256"] == EXP215_PLAN_SHA
assert status["epoch"] >= 60
assert status["best_sha256"] == EXP215_BEST_SHA
assert sha(parent / "edge_predictor_best.pth") == EXP215_BEST_SHA
assert sha(status_path) == EXP215_STATUS_SHA
selected = max(history, key=lambda row: row["selection_score"])
assert selected["epoch"] == 59
assert abs(float(selected["selection_score"]) - EXP215_SOURCE_SCORE) < 1e-12

bundle = copy.deepcopy(old)
bundle["purpose"] = "EXP217_FULL60_SOURCE44_TARGET6BBA_COMPARISON"
bundle["primary"] = {
    "path": str(parent / "edge_predictor_best.pth"),
    "sha256": EXP215_BEST_SHA,
    "actual_training_plan_sha256": EXP215_PLAN_SHA,
    "source_status_sha256": EXP215_STATUS_SHA,
    "seed": 2026,
    "selected_epoch": 59,
    "source_selection_score": EXP215_SOURCE_SCORE,
    "source_only_selection": True,
    "total_epochs": 60,
    "parent_exp215_status": status["status"],
}
bundle["scope"] = (
    "Only the source44b6 primary checkpoint changes to EXP215 full-cache "
    "epoch59. Secondary60, center, graph policy, movie cohort and scoring "
    "contract remain matched to EXP214 gapfix90."
)
bundle["exp217_parent_bundle_sha256"] = sha(parent_bundle_path)
for role in ("primary", "secondary", "center"):
    assert sha(bundle[role]["path"]) == bundle[role]["sha256"], role

def write_exact(path, payload):
    text = json.dumps(payload, indent=2) + "\n"
    path = Path(path)
    if path.exists():
        assert path.read_text() == text, str(path)
    else:
        path.write_text(text)

bundle_path = out / "44b6_bundle.json"
write_exact(bundle_path, bundle)
receipt = {
    "status": "PASS_EXP217_FULL60_SOURCE44_BUNDLE_STAGED",
    "bundle": str(bundle_path),
    "bundle_sha256": sha(bundle_path),
    "parent_bundle_sha256": bundle["exp217_parent_bundle_sha256"],
    "primary_sha256": EXP215_BEST_SHA,
    "primary_source_status_sha256": EXP215_STATUS_SHA,
    "training_plan_sha256": EXP214_PLAN_SHA,
    "actual_primary_training_plan_sha256": EXP215_PLAN_SHA,
    "target_labels_read": False,
}
write_exact(out / "bundle_receipt.json", receipt)
print(json.dumps(receipt))
'''.replace("ROOT", repr(REMOTE)).replace("REMOTE_INPUT", repr(REMOTE_INPUT)).replace(
        "EXP214_PLAN_SHA", repr(EXP214_PLAN_SHA)
    ).replace("EXP215_PLAN_SHA", repr(EXP215_PLAN_SHA)).replace(
        "EXP215_BEST_SHA", repr(EXP215_BEST_SHA)
    ).replace("EXP215_STATUS_SHA", repr(EXP215_STATUS_SHA)).replace(
        "EXP215_SOURCE_SCORE", repr(EXP215_SOURCE_SCORE)
    )
    return ssh("nsu-quadro", "python3 -", source)


def build_configs() -> list[dict]:
    configs = []
    for index in range(5):
        tag = f"44b6_{index:02}"
        base_path = LOCAL / f"reports/exp214_gapfix_paired_new90_{tag}_config_20260914.json"
        config = json.loads(base_path.read_text())
        arguments = without_reuse_manifest(list(config["arguments"]))
        run = REMOTE + f"/runs/exp217_full60_source44_target6bba_{tag}_20260915"
        gpu, cpu = (GPU_A, "0-7") if index in (0, 2, 4) else (GPU_B, "8-15")
        config.update(
            experiment="EXP217",
            lease_id=f"biohub-exp217-full60-source44-{tag}-20260915",
            token=f"exp217-full60-source44-{tag}",
            gpu=gpu,
            cpu_affinity=cpu,
            code=REMOTE + "/code/exp214_inference_v8_20260914",
            run=run,
            scope=(
                "EXP217 replaces only source44b6 primary with EXP215 full-cache "
                "epoch59, target6bba paired predictions only; no metrics or POST."
            ),
        )
        set_argument(arguments, "--bundle", REMOTE_INPUT + "/44b6_bundle.json")
        set_argument(arguments, "--output", run + "/output")
        config["arguments"] = arguments
        path = LOCAL / f"reports/exp217_full60_source44_target6bba_{tag}_config_20260915.json"
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
            "EXP217 full60 source44b6 candidate versus EXP214 gapfix90 baseline. "
            "Candidate changes only the five target6bba source44b6 shards; "
            "target44b6 source6bba shards are reused unchanged from the baseline."
        ),
        "training_epochs": {
            "candidate_source44b6_primary": 60,
            "baseline_source44b6_primary": 90,
            "source6bba_primary_reused": 90,
            "secondary": 60,
        },
        "arms": {},
    }
    for arm in ("public", "local"):
        parts = copy.deepcopy(baseline["arms"][arm])
        manifest["arms"][f"baseline_gapfix90_{arm}"] = copy.deepcopy(parts)
        candidate = []
        replaced = 0
        reused = 0
        for part in parts:
            if all(movie.startswith("6bba_") for movie in part["movies"]):
                tag = f"44b6_{replaced:02}"
                candidate.append(
                    {
                        "receipt": REMOTE
                        + f"/runs/exp217_full60_source44_target6bba_{tag}_20260915/output/{arm}/inference_receipt.json",
                        "csv": REMOTE
                        + f"/runs/exp217_full60_source44_target6bba_{tag}_20260915/output/{arm}/submission.csv",
                        "movies": part["movies"],
                    }
                )
                replaced += 1
            else:
                candidate.append(part)
                reused += 1
        assert replaced == 5 and reused == 3
        manifest["arms"][f"candidate_full60_source44_{arm}"] = candidate
    path = LOCAL / "reports/exp217_full60_source44_target6bba_manifest_20260915.json"
    return write_json_once(path, manifest)


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
        "print(json.dumps({'status':'PASS_EXP217_MANIFEST_STAGED','path':str(path),'arms':list(payload['arms'])}))\n"
    )
    return ssh("nsu-quadro", "python3 -", source)


def main() -> None:
    preregistration = preregister()
    bundle = stage_remote_bundle()
    write_json_once(
        LOCAL / "reports/exp217_full60_source44_target6bba_bundle_receipt_20260915.json",
        bundle,
    )
    configs = build_configs()
    manifest = build_manifest()
    remote_manifest = stage_remote_manifest(manifest)
    result = {
        "status": "PASS_EXP217_FULL60_SOURCE44_TARGET6BBA_PREPARED",
        "preregistration_experiment": preregistration["experiment"],
        "bundle": bundle,
        "configs": configs,
        "manifest": str(LOCAL / "reports/exp217_full60_source44_target6bba_manifest_20260915.json"),
        "remote_manifest": remote_manifest,
        "target_labels_read": False,
        "kaggle_post": False,
    }
    write_json_once(LOCAL / "reports/exp217_full60_source44_target6bba_prepare_20260915.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
