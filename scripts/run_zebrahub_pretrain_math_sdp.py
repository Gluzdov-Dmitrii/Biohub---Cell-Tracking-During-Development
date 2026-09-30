"""Run the pinned Zebrahub pretraining script on older CUDA GPUs.

Some PyTorch 2.6 SDPA kernels fail with ``invalid configuration argument`` on
the Quadro RTX 6000 for the very large batch-of-short-sequences layout used by
the temporal attention block.  The math SDPA path is slower but compatible and
keeps the model definition unchanged.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import torch


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: run_zebrahub_pretrain_math_sdp.py PRETRAIN_SCRIPT")
    if torch.cuda.is_available():
        torch.backends.cuda.enable_flash_sdp(False)
        torch.backends.cuda.enable_mem_efficient_sdp(False)
        torch.backends.cuda.enable_math_sdp(True)
    runpy.run_path(str(Path(sys.argv[1]).resolve()), run_name="__main__")


if __name__ == "__main__":
    main()
