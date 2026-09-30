"""Run the tracking fine-tune with the Quadro-safe math SDPA backend.

The Quadro RTX 6000 path previously failed in fused attention with
``CUDA error: invalid configuration argument``.  Keeping this switch in a
small checked-in launcher makes the remote experiment reproducible and
avoids silently changing the model or its data flow.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import torch


def main() -> None:
    if hasattr(torch.backends.cuda, "enable_flash_sdp"):
        torch.backends.cuda.enable_flash_sdp(False)
        torch.backends.cuda.enable_mem_efficient_sdp(False)
        torch.backends.cuda.enable_math_sdp(True)

    candidates = [
        Path(__file__).resolve().parents[1]
        / "outputs/exp027_zebrahub_runtime_smoke/tracking_repo/scripts/train_unet_transformer.py",
        Path(__file__).resolve().parent
        / "tracking_repo/scripts/train_unet_transformer.py",
        Path.cwd() / "tracking_repo/scripts/train_unet_transformer.py",
    ]
    script = next((candidate for candidate in candidates if candidate.exists()), None)
    if script is None:
        raise FileNotFoundError(
            "Could not locate tracking_repo/scripts/train_unet_transformer.py; "
            f"checked: {candidates}"
        )
    sys.path.insert(0, str(script.parent))
    sys.path.insert(0, str(script.parent.parent / "src"))
    sys.argv = [str(script), *sys.argv[1:]]
    runpy.run_path(str(script), run_name="__main__")


if __name__ == "__main__":
    main()
