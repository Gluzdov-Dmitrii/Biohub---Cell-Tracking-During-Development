from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "train_pretrained_feature_daughter_pair",
    ROOT / "scripts/train_pretrained_feature_daughter_pair.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_pretrained_feature_head_is_daughter_swap_invariant():
    torch.manual_seed(160)
    model = MODULE.PretrainedFeaturePairHead().eval()
    parent = torch.randn(11, 32)
    first = torch.randn(11, 32)
    second = torch.randn(11, 32)
    geometry = torch.randn(11, 5)
    with torch.no_grad():
        forward = model(parent, first, second, geometry)
        reverse = model(parent, second, first, geometry)
    torch.testing.assert_close(forward, reverse, rtol=0, atol=0)
