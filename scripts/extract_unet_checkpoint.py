"""Extract the UNet part from a full edge-predictor checkpoint.

The community Zebrahub pretraining checkpoint contains both the image UNet and
the node transformer under ``unet.*`` and ``transformer.*`` keys.  The existing
competition fine-tuner accepts an UNet-only state dict, so this small explicit
conversion keeps the transfer auditable instead of silently loading zero
pretrained layers with ``strict=False``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import torch


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    state = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    if not isinstance(state, dict):
        raise TypeError(f"Expected state dict, got {type(state).__name__}")
    unet = {key.removeprefix("unet."): value for key, value in state.items() if key.startswith("unet.")}
    if not unet or any(key.startswith("unet.") for key in unet):
        raise ValueError("Unexpected UNet key layout")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(unet, args.output)
    receipt = {
        "source": str(args.checkpoint),
        "source_sha256": sha256(args.checkpoint),
        "output": str(args.output),
        "output_sha256": sha256(args.output),
        "keys": len(unet),
        "purpose": "competition fine-tune initialization; no LB submission authority",
    }
    receipt_path = args.output.with_suffix(".receipt.json")
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
