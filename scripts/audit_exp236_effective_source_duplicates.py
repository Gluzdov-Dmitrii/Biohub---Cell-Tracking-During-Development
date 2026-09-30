"""Audit adjacent source6bba frames at Horaz's exact loader downsampling."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import torch
import zarr


CODE = Path("/home/scientists/gluz_d_s/kaggle/projects/"
            "biohub-cell-tracking-during-development/code/"
            "exp236_horaz_source6bba_block01_20260927")
PLAN_SHA = "d75ffd601e0e8409976fd74a854d704f598f758bd250c4d552d985dda475a1c5"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=None)
    args = parser.parse_args()
    assert sha(CODE / "plan.json") == PLAN_SHA
    plan = json.loads((CODE / "plan.json").read_text())
    assert plan["experiment"] == "EXP236" and plan["source_embryo"] == "6bba"
    recipe = json.loads((CODE / "horaz/resolved_config.json").read_text())
    downsample = tuple(recipe["downsample"])
    assert downsample == (1, 4, 4) and recipe["window_size"] == 2
    rows = plan["train"] + plan["inner_validation"]
    assert len(plan["train"]) == 115 and len(plan["inner_validation"]) == 11
    assert len({row["dataset_id"] for row in rows}) == 126
    assert all(row["dataset_id"].startswith("6bba_") for row in rows)
    if args.dataset is not None:
        rows = [row for row in rows if row["dataset_id"] == args.dataset]
        assert len(rows) == 1
    sys.path.insert(0, str(CODE / "horaz/src/src"))
    from datasets import build_window, read_training_graph

    per_movie = []
    inconsistent = []
    sampled_duplicate_count = 0
    for row in rows:
        array = zarr.open(row["zarr_path"], mode="r")["0"]
        assert array.shape == (100, 64, 256, 256) and str(array.dtype) == "uint16"
        images = np.asarray(array[:, ::downsample[0], ::downsample[1],
                                  ::downsample[2]], dtype=np.float32)
        assert images.shape == (100, 64, 64, 64)
        repeated = np.all(images[1:] == images[:-1], axis=(1, 2, 3))
        times = (np.flatnonzero(repeated) + 1).tolist()
        if not times:
            continue
        graph = read_training_graph(row["geff_path"])
        pairs = []
        for t in times:
            window = build_window(graph, int(t) - 1, 2, downsample)
            sampled = window is not None
            concordant = True
            if sampled:
                sampled_duplicate_count += 1
                before, after = window.coords
                transition = window.targets[0]
                concordant = (torch.equal(before, after) and
                              torch.equal(transition,
                                          torch.eye(len(before), dtype=transition.dtype)))
            item = {"t0": int(t) - 1, "t1": int(t), "sampled": sampled,
                    "labels_concordant": bool(concordant)}
            pairs.append(item)
            if sampled and not concordant:
                inconsistent.append({"dataset": row["dataset_id"], **item})
        per_movie.append({"dataset": row["dataset_id"],
                          "split": "train" if row in plan["train"] else "inner_validation",
                          "pairs": pairs})
    receipt = {"status": "AUDITED_EXP236_EFFECTIVE_SOURCE_DUPLICATES",
               "evidence_class": "source-only loader-view image/annotation audit; not OOF",
               "plan_sha256": PLAN_SHA,
               "resolved_config_sha256": sha(CODE / "horaz/resolved_config.json"),
               "downsample": list(downsample), "window_size": 2,
               "movies_scanned": len(rows),
               "movies_with_duplicates": len(per_movie),
               "duplicate_pairs": sum(len(row["pairs"]) for row in per_movie),
               "sampled_duplicate_pairs": sampled_duplicate_count,
               "inconsistent_sampled_pairs": inconsistent,
               "per_movie": per_movie, "target_data_opened": False}
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
