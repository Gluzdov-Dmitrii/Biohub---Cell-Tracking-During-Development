from __future__ import annotations

import ast
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "outputs" / "research" / "exp207_edge_feature_tta8"
PARENT = EXP / "predict_unet_transformer_parent.py"
CANDIDATE = EXP / "predict_unet_transformer_d4_optional_feature_tta.py"


def test_only_the_tta_block_changes_from_the_frozen_parent() -> None:
    parent = PARENT.read_text(encoding="utf-8")
    candidate = CANDIDATE.read_text(encoding="utf-8")
    parent_start = parent.index("        # Detection TTA:")
    candidate_start = candidate.index("        # Eight-view D4 TTA")
    parent_end = parent.index("        blended_det_logits = None", parent_start)
    candidate_end = candidate.index("        blended_det_logits = None", candidate_start)
    assert parent[:parent_start] == candidate[:candidate_start]
    assert parent[parent_end:] == candidate[candidate_end:]
    ast.parse(candidate)


def test_candidate_has_one_optional_feature_arm_and_fixed_eight_view_detection() -> None:
    source = CANDIDATE.read_text(encoding="utf-8")
    assert source.count('os.environ.get("BIOHUB_EDGE_FEATURE_TTA", "0")') == 1
    assert "for rotation in (1, 3):" in source
    assert "imgs_transpose = imgs.transpose(-1, -2)" in source
    assert "imgs_antitranspose = torch.rot90(imgs, 1" in source
    assert "if num_views != 8:" in source
    assert "det_logits[f] = det_logits[f] / num_views" in source
    assert "unet_out = unet_acc / num_views" in source


def test_all_inverse_maps_used_by_candidate_restore_the_original_grid() -> None:
    value = torch.arange(2 * 3 * 4 * 5, dtype=torch.int64).reshape(2, 3, 4, 5)
    restored = [value.flip(dims).flip(dims) for dims in [(-1,), (-2,), (-2, -1)]]
    restored.extend(
        torch.rot90(torch.rot90(value, rotation, dims=(-2, -1)), -rotation, dims=(-2, -1))
        for rotation in (1, 3)
    )
    restored.append(value.transpose(-1, -2).transpose(-1, -2))
    antitransformed = torch.rot90(value, 1, dims=(-2, -1)).transpose(-1, -2)
    restored.append(torch.rot90(antitransformed.transpose(-1, -2), -1, dims=(-2, -1)))
    assert len(restored) == 7
    assert all(torch.equal(item, value) for item in restored)
