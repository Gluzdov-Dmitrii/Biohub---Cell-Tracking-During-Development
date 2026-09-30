"""Re-run verified real-Zebrahub training with a division-positive loss.

The base training program is hash-pinned. This runner applies a small audited
source transformation: resume the complete model, freeze visual detection,
train only the temporal transformer for one epoch, and upweight true daughter
edges without changing the negative background as strongly.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise RuntimeError({"anchor_count": source.count(old), "anchor": old[:120]})
    return source.replace(old, new, 1)
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-script", type=Path, required=True)
    parser.add_argument("--base-sha256", required=True)
    parser.add_argument("--initializer", type=Path, required=True)
    parser.add_argument("--initializer-sha256", required=True)
    parser.add_argument("--training-repo", type=Path, required=True)
    parser.add_argument("--compile-only", action="store_true")
    args = parser.parse_args()

    if sha(args.base_script) != args.base_sha256:
        raise RuntimeError("base pretraining script hash mismatch")
    if sha(args.initializer) != args.initializer_sha256:
        raise RuntimeError("initializer hash mismatch")

    source = args.base_script.read_text(encoding="utf-8")
    source = replace_once(source, "EPOCHS = 12", "EPOCHS = 1")
    source = replace_once(
        source,
        'REPO = WORK / "tracking_repo"\nif REPO.exists():\n    shutil.rmtree(REPO)\nshutil.copytree(SUPPORT / "repo", REPO)',
        'REPO = Path(os.environ["BIOHUB_TRAINING_REPO"])\n'
        'if not (REPO / "scripts/train_unet_transformer.py").is_file():\n'
        '    raise FileNotFoundError(REPO)',
    )
    source = replace_once(
        source,
        "from train_unet_transformer import (",
        "import train_unet_transformer as trainer_module\n"
        "from train_unet_transformer import (",
    )
    source = replace_once(
        source,
        "import torch\nimport torch.nn as nn",
        "import torch\n"
        "torch.backends.cuda.enable_flash_sdp(False)\n"
        "torch.backends.cuda.enable_mem_efficient_sdp(False)\n"
        "torch.backends.cuda.enable_math_sdp(True)\n"
        "import torch.nn as nn",
    )
    source = replace_once(
        source,
        "random.seed(SEED)\nnp.random.seed(SEED)",
        '''def division_positive_loss(logits, target):
    active_rows = target.sum(dim=1) > 0
    active_cols = target.sum(dim=0) > 0
    mask = active_rows.unsqueeze(1) | active_cols.unsqueeze(0)
    if not mask.any():
        return torch.tensor(0.0, requires_grad=True, device=logits.device)
    probs = torch.softmax(logits, dim=0)
    bce = torch.nn.functional.binary_cross_entropy(probs, target, reduction="none")
    p_t = probs * target + (1 - probs) * (1 - target)
    loss = ((1 - p_t) ** 2) * bce
    division_rows = target.sum(dim=1) > 1
    weight = torch.ones_like(loss)
    weight[division_rows] = 2.0
    positive_division = division_rows.unsqueeze(1) & (target > 0)
    weight[positive_division] = 8.0
    return (loss * weight)[mask].mean()


trainer_module.compute_loss = division_positive_loss

random.seed(SEED)
np.random.seed(SEED)''',
    )
    source = replace_once(
        source,
        ").to(device)\nif torch.cuda.device_count() > 1:",
        f''').to(device)
state = torch.load({str(args.initializer)!r}, map_location="cpu", weights_only=True)
missing, unexpected = model.load_state_dict(state, strict=False)
if missing or unexpected:
    raise RuntimeError({{"missing": missing, "unexpected": unexpected}})
for parameter in model.unet.parameters():
    parameter.requires_grad_(False)
for parameter in model.detect_head.parameters():
    parameter.requires_grad_(False)
_original_model_train = model.train
def _transformer_only_train(mode=True):
    result = _original_model_train(mode)
    if mode:
        model.unet.eval()
        model.detect_head.eval()
    return result
model.train = _transformer_only_train
if torch.cuda.device_count() > 1:''',
    )
    source = replace_once(
        source,
        "optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)",
        "optimizer = torch.optim.AdamW(model.transformer.parameters(), lr=2e-5)",
    )
    os.environ["BIOHUB_TRAINING_REPO"] = str(args.training_repo)
    sys.argv = [str(args.base_script)]
    compiled = compile(source, str(args.base_script) + ":EXP157", "exec")
    if args.compile_only:
        print(hashlib.sha256(source.encode("utf-8")).hexdigest())
        return
    exec(compiled, {"__name__": "__main__", "__file__": str(args.base_script)})


if __name__ == "__main__":
    main()
