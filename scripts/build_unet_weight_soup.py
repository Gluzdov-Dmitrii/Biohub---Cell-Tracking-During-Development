"""Build an audited U-Net-only weight soup from aligned full-model checkpoints."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import torch


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def unwrap(value: object) -> dict[str, torch.Tensor]:
    if isinstance(value, dict) and "model" in value:
        value = value["model"]
    if not isinstance(value, dict) or not value:
        raise TypeError("checkpoint is not a non-empty state dict")
    if not all(isinstance(key, str) and torch.is_tensor(tensor) for key, tensor in value.items()):
        raise TypeError("checkpoint contains a non-string key or non-tensor value")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary", type=Path, required=True)
    parser.add_argument("--donor", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--donor-weight", type=float, default=0.5)
    args = parser.parse_args()
    if not 0.0 < args.donor_weight < 1.0:
        parser.error("--donor-weight must be strictly between 0 and 1")

    primary = unwrap(torch.load(args.primary, map_location="cpu", weights_only=True))
    donor = unwrap(torch.load(args.donor, map_location="cpu", weights_only=True))
    if list(primary) != list(donor):
        raise ValueError("checkpoint key order/set mismatch")

    output: dict[str, torch.Tensor] = {}
    averaged = 0
    copied_unet_buffers = 0
    copied_non_unet = 0
    for key, left in primary.items():
        right = donor[key]
        if left.shape != right.shape or left.dtype != right.dtype:
            raise ValueError(
                f"tensor mismatch for {key}: {left.shape}/{left.dtype} vs {right.shape}/{right.dtype}"
            )
        if key.startswith("unet.") and left.is_floating_point():
            mixed = left.float().mul(1.0 - args.donor_weight).add(
                right.float(), alpha=args.donor_weight
            )
            output[key] = mixed.to(dtype=left.dtype)
            averaged += 1
        else:
            output[key] = left.clone()
            if key.startswith("unet."):
                copied_unet_buffers += 1
            else:
                copied_non_unet += 1
    if averaged == 0 or copied_non_unet == 0:
        raise RuntimeError("unexpected checkpoint namespaces")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    if temporary.exists() or args.output.exists():
        raise FileExistsError("refusing to overwrite soup checkpoint")
    torch.save(output, temporary)
    temporary.replace(args.output)
    receipt = {
        "status": "PASS_ALIGNED_UNET_WEIGHT_SOUP_BUILD",
        "primary": str(args.primary),
        "primary_sha256": sha256(args.primary),
        "donor": str(args.donor),
        "donor_sha256": sha256(args.donor),
        "donor_weight": args.donor_weight,
        "total_tensors": len(output),
        "averaged_floating_unet_tensors": averaged,
        "copied_nonfloating_unet_buffers": copied_unet_buffers,
        "copied_primary_non_unet_tensors": copied_non_unet,
        "output": str(args.output),
        "output_bytes": args.output.stat().st_size,
        "output_sha256": sha256(args.output),
    }
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
