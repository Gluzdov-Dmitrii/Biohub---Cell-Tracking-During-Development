"""Build the EXP027 independent-pretraining LB candidate.

The base notebook supplies the already-audited runtime graph contract.  This
builder changes the model artifact to the independently trained Zebrahub-
initialized checkpoint and fails closed if that artifact is absent.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "kaggle_notebooks/exp092_finetuned_d4_offline/finetuned_d4.ipynb"
OUTPUT_DIR = ROOT / "kaggle_notebooks/exp027_zebrahub_gold_public"
OUTPUT = OUTPUT_DIR / "zebrahub_gold_public.ipynb"
METADATA = OUTPUT_DIR / "kernel-metadata.json"
EXPECTED_SOURCE_SHA256 = "d746494acc5bc98eb1d7ee fc777675d8b9e02954ff26273a0cf4e891c2518dcc".replace(" ", "")
ARTIFACT_SLUG = "biohub-exp027-zebrahub-finetuned-44b6-v1"
WEIGHT_PATH = f"/kaggle/input/datasets/dmitriigluzdov/{ARTIFACT_SLUG}/edge_predictor_best_full5.pth"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    source_sha = sha256(SOURCE)
    if source_sha != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"Reviewed EXP092 source drift: {source_sha}")

    notebook = json.loads(SOURCE.read_text(encoding="utf-8"))
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            cell["outputs"] = []
            cell["execution_count"] = None
            source = "".join(cell["source"]) if isinstance(cell["source"], list) else str(cell["source"])
            source = source.replace(
                'EXPERIMENT_TAG = "selected_61_calibrated_graph_d4_edge_tta"',
                'EXPERIMENT_TAG = "EXP027_zebrahub_init_44b6_full5_d4"',
            )
            source = source.replace(
                'os.environ["BIOHUB_USE_DEEPCENTER_VETO"] = \'0\'',
                'os.environ["BIOHUB_USE_DEEPCENTER_VETO"] = \'0\'\n'
                'os.environ["BIOHUB_OUTPUT_DIVISION_GEOMETRY_FILTER"] = "1"',
            )
            old_override = '''# === OUR WEIGHT OVERRIDE ===
OUR_W = Path('/kaggle/input/datasets/muqiu/biohub-ft-weights-v1/edge_predictor_finetune_ft48.pth')
if OUR_W.exists():
    import shutil as _sh
    _sh.copy(OUR_W, REPO_DIR / WEIGHTS_RELATIVE)
    print('Using OUR finetuned weights')'''
            new_override = f'''# === EXP027 INDEPENDENT WEIGHT OVERRIDE ===
OUR_WEIGHT_CANDIDATES = [
    Path("{WEIGHT_PATH}"),
    Path("/kaggle/input/{ARTIFACT_SLUG}/edge_predictor_best_full5.pth"),
]
OUR_W = next((path for path in OUR_WEIGHT_CANDIDATES if path.exists()), None)
if OUR_W is None:
    raise FileNotFoundError(
        "EXP027 checkpoint is required; refusing to fall back to the parent weight. "
        f"Checked: {{OUR_WEIGHT_CANDIDATES}}"
    )
import shutil as _sh
# The support artifact may materialize ``weights`` as a symlink into the
# read-only /kaggle/input mount. Remove only that working-tree symlink before
# creating a writable target; never mutate the attached artifact.
_weights_root = REPO_DIR / "weights"
if _weights_root.is_symlink():
    _weights_root.unlink()
_target_weight = REPO_DIR / WEIGHTS_RELATIVE
_target_weight.parent.mkdir(parents=True, exist_ok=True)
_sh.copy(OUR_W, _target_weight)
print("Using EXP027 Zebrahub-initialized weights:", OUR_W)
assert _target_weight.stat().st_size == OUR_W.stat().st_size'''
            if old_override in source:
                source = source.replace(old_override, new_override)
            if isinstance(cell["source"], list):
                cell["source"] = source.splitlines(keepends=True)
            else:
                cell["source"] = source
        elif cell["cell_type"] == "markdown":
            cell.pop("outputs", None)
            cell.pop("execution_count", None)

    notebook["cells"].insert(
        0,
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# EXP027: independent Zebrahub initialization — GOLD_PUBLIC candidate\n",
                "This candidate keeps the audited dynamic runtime test-set inference and graph/output contract, "
                "but replaces the parent model with a checkpoint initialized from an independent Zebrahub dataset "
                "and fine-tuned on the frozen 44b6 pilot. The checkpoint is required and the notebook fails closed "
                "if it is missing; it never reads a frozen public submission.csv.\n\n",
                "Evidence and limitations are recorded in the attached EXP027 receipt: the available local fold is "
                "within-embryo diagnostic only, so this is a public-track probe rather than PRIVATE_ROBUST evidence.\n",
            ],
        },
    )
    kaggle_meta = notebook.setdefault("metadata", {}).setdefault("kaggle", {})
    kaggle_meta["isGpuEnabled"] = True
    kaggle_meta["isInternetEnabled"] = False

    # Kaggle's notebook serializer canonicalizes markdown ``source`` lists to
    # strings.  Match that representation locally so the guarded submit helper
    # can prove byte identity with the exact source stored for the tested
    # kernel version instead of silently accepting normalization drift.
    for cell in notebook["cells"]:
        if cell.get("cell_type") == "markdown" and isinstance(cell.get("source"), list):
            cell["source"] = "".join(cell["source"])

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(notebook, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    METADATA.write_text(
        json.dumps(
            {
                "id": "dmitriigluzdov/biohub-exp027-zebrahub-gold-public",
                "title": "Biohub EXP027 Zebrahub GOLD PUBLIC",
                "code_file": OUTPUT.name,
                "language": "python",
                "kernel_type": "notebook",
                "is_private": True,
                "enable_gpu": True,
                "enable_tpu": False,
                "enable_internet": False,
                "keywords": ["biology", "gpu", "independent-pretraining"],
                "dataset_sources": [
                    "dmitriigluzdov/biohub-exp027-zebrahub-finetuned-44b6-v1",
                    "pilkwang/pilkwang-public-dataset-for-notebooks-figures",
                    "pilkwang/biohub-deepcenter-unet3d-center-prior-v1",
                    "muhanqiu/biohub-ft-weights-v1",
                    "pilkwang/biohub-tracking-support-pack-50ep-v1",
                ],
                "kernel_sources": [],
                "competition_sources": ["biohub-cell-tracking-during-development"],
                "model_sources": [],
                "machine_shape": "NvidiaTeslaT4",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), f"EXP027:cell{index}", "exec")

    print(json.dumps({
        "status": "PASS_EXP027_BUILD",
        "source_sha256": source_sha,
        "output_sha256": sha256(OUTPUT),
        "weight_sha256": "082d3882ad183892b3bb7541ecbb1383670eef5ba474d110af b58ffef7f77583".replace(" ", ""),
        "internet": False,
        "dynamic_runtime_test_inference": True,
        "fallback_to_parent_weight": False,
    }, indent=2))


if __name__ == "__main__":
    main()
