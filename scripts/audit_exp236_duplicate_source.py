"""Read-only audit of repeated source6bba frames and their training labels.

Run with the remote prepost Python environment on nsu-a100. This inspects only
the pinned EXP236 source cohort; it never reads target44b6 data.
"""
import argparse
import filecmp
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
    plan_path = CODE / "plan.json"
    assert sha(plan_path) == PLAN_SHA
    plan = json.loads(plan_path.read_text())
    assert plan["experiment"] == "EXP236" and plan["source_embryo"] == "6bba"
    rows = plan["train"] + plan["inner_validation"]
    assert len(plan["train"]) == 115 and len(plan["inner_validation"]) == 11
    assert len({r["dataset_id"] for r in rows}) == len(rows) == 126
    assert all(r["dataset_id"].startswith("6bba_") for r in rows)
    if args.dataset is not None:
        rows = [row for row in rows if row["dataset_id"] == args.dataset]
        assert len(rows) == 1
    sys.path.insert(0, str(CODE / "horaz/src/src"))
    from datasets import build_window, read_training_graph

    per_movie = []
    inconsistent = []
    for row in rows:
        name = row["dataset_id"]
        zarr_path = Path(row["zarr_path"])
        array_path = zarr_path / "0"
        metadata = json.loads((array_path / "zarr.json").read_text())
        assert metadata["zarr_format"] == 3
        assert metadata["data_type"] == "uint16"
        assert metadata["chunk_grid"]["configuration"]["chunk_shape"] == [1, 64, 256, 256]
        assert metadata["codecs"] == [
            {"name": "bytes", "configuration": {"endian": "little"}},
            {"name": "blosc", "configuration": {"typesize": 2, "cname": "zstd",
                                                   "clevel": 1, "shuffle": "bitshuffle",
                                                   "blocksize": 0}},
        ]
        array = zarr.open(row["zarr_path"], mode="r")["0"]
        assert array.shape[0] == 100
        duplicates = []
        graph = None
        previous = array_path / "c/0/0/0/0"
        assert previous.is_file()
        for t in range(1, array.shape[0]):
            current = array_path / "c" / str(t) / "0/0/0"
            assert current.is_file()
            if filecmp.cmp(previous, current, shallow=False):
                assert np.array_equal(np.asarray(array[t - 1]), np.asarray(array[t]))
                if graph is None:
                    graph = read_training_graph(row["geff_path"])
                window = build_window(graph, t - 1, 2, (1, 1, 1))
                sampled = window is not None
                labels_concordant = True
                if sampled:
                    before, after = window.coords
                    transition = window.targets[0]
                    labels_concordant = (torch.equal(before, after) and
                                         torch.equal(transition,
                                                     torch.eye(len(before),
                                                               dtype=transition.dtype)))
                item = {"t0": t - 1, "t1": t, "sampled": sampled,
                        "labels_concordant": bool(labels_concordant)}
                duplicates.append(item)
                if sampled and not labels_concordant:
                    inconsistent.append({"dataset": name, **item})
            previous = current
        if duplicates:
            per_movie.append({"dataset": name,
                              "split": "train" if row in plan["train"] else "inner_validation",
                              "duplicates": duplicates})
    receipt = {"status": "PASS_EXP236_SOURCE_DUPLICATE_AUDIT"
               if not inconsistent else "FAIL_EXP236_SOURCE_DUPLICATE_AUDIT",
               "evidence_class": "source-only image/annotation consistency audit, not OOF",
               "plan_sha256": PLAN_SHA, "movies_scanned": len(rows),
               "duplicate_detection": "exact_adjacent_compressed_chunk_bytes_with_pinned_deterministic_zstd_bitshuffle_codec; positive_pairs_decoded_exactly",
               "movies_with_duplicates": len(per_movie),
               "duplicate_pairs": sum(len(r["duplicates"]) for r in per_movie),
               "inconsistent_sampled_pairs": inconsistent,
               "per_movie": per_movie, "target_data_opened": False}
    print(json.dumps(receipt))
    if inconsistent:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
