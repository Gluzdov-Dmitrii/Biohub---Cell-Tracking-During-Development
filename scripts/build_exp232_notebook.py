"""Build the full, runtime-selecting P26 derivative for a clean Kaggle run."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path

from build_exp225_notebook import (
    DEFAULT_SOURCE, bound_serialized_coordinates, code, markdown, source,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "kaggle_notebooks/exp232_p26_runtime_selection"
NAME = "biohub-exp232-p26-runtime-selection.ipynb"
KERNEL = "dmitriigluzdov/biohub-exp232-p26-runtime-selection"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    upstream = json.loads(DEFAULT_SOURCE.read_text(encoding="utf-8"))
    originals = [source(cell) for cell in upstream["cells"]]
    assert len(originals) == 12
    cells = [markdown("""# EXP232 · P26 with runtime postprocess selection

This notebook starts from [P26](https://www.kaggle.com/code/zhehaoliang/biohub-p26-o01-exact-public-0947). It runs the two pretrained temporal models and DeepCenter on the **current competition test Zarr volumes**, then builds and audits the tracking graph. The input is never a saved public submission.

Unlike EXP225, this version retains P26's original train-proxy validator and its seven-candidate postprocess sweep. The sweep selects a configuration using visible train labels and reserializes the current test inference. That selection is useful as a public-LB experiment but is **not honest unseen-embryo OOF**. The only inference change from upstream is clipping rounded output coordinates to the actual runtime image bounds. Public score is unknown until this exact version is submitted.

Run top to bottom with Internet off and T4 ×2. The final cell verifies a single root `submission.csv`, dataset IDs, coordinate bounds, and graph invariants. The Kaggle submission itself is a separate guarded action.
""")]
    descriptions = [
        "Environment and original P26 defaults. Configuration is read below, before any model inference.",
        "Original configuration sanity checks and diagnostic labels.",
        "Find the runtime competition test path and read physical/graph parameters.",
        "Install offline support wheels; pin the inference repository and model artifacts by hash.",
        "Discover current test movies and run the pretrained temporal models on their images.",
        "Build detections and links, apply physical graph repairs, then write the first test CSV. Only CSV coordinate rounding is bounded.",
        "Audit candidate retention, topology, and source provenance before proxy selection.",
        "Select disjoint visible train movies and infer their graphs for the proxy. These are train labels, not private validation.",
        "Define matching and proxy metrics for the visible validation movies.",
        "Evaluate the base configuration on the visible train subset.",
        "Compare seven postprocess variants, apply the margin rule, reserialize the same test inference, and validate the selected graph.",
        "Print the resolved pipeline, weights, and validator state so the executed mode is visible.",
    ]
    for i, text in enumerate(originals):
        if i == 5:
            text = bound_serialized_coordinates(text)
        cells.append(markdown(f"## {i + 1}. {descriptions[i]}"))
        cells.append(code(text, upstream_cell=i))
    audit = (ROOT / "scripts/exp225_output_audit.py").read_text(encoding="utf-8")
    cells.append(markdown("## Final output audit\n\nThis independently reads runtime Zarr shapes and checks the sole root CSV. It does not supply a quality estimate."))
    cells.append(code(audit, role="audit_definition"))
    cells.append(code("EXP232_OUTPUT_AUDIT = run_exp225_output_audit(\n    TEST_DIR, WORKING_DIR,\n    source_evidence_status='P26 original inference and runtime train-proxy selection; serializer bound fix; no honest OOF',\n)\nprint(json.dumps(EXP232_OUTPUT_AUDIT, indent=2, sort_keys=True))\n", role="run_audit"))
    for i, cell in enumerate(cells):
        cell["id"] = f"exp232-{i:03d}"
        if cell["cell_type"] == "code":
            compile(source(cell), f"exp232_cell_{i}", "exec")
    for i in range(12):
        revised = source(next(c for c in cells if c.get("metadata", {}).get("upstream_cell") == i))
        if i != 5:
            assert revised == originals[i], i
        else:
            old, new = ast.parse(originals[i]).body, ast.parse(revised).body
            assert len(old) == len(new)
            changed = [a.name for a, b in zip(old, new) if ast.dump(a, include_attributes=False) != ast.dump(b, include_attributes=False)]
            assert changed == ["write_test_submission"], changed
    metadata = copy.deepcopy(upstream.get("metadata", {}))
    metadata.pop("papermill", None)
    metadata["title"] = "Biohub EXP232 - P26 Runtime Selection"
    metadata["exp232_provenance"] = {
        "upstream_kernel": "zhehaoliang/biohub-p26-o01-exact-public-0947",
        "upstream_sha256": sha(DEFAULT_SOURCE),
        "original_cells_preserved": [i for i in range(12) if i != 5],
        "modified_function": "write_test_submission",
        "train_proxy_selection": True,
        "honest_oof_for_public_weights": False,
    }
    notebook = {"cells": cells, "metadata": metadata, "nbformat": 4, "nbformat_minor": 5}
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / NAME
    path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    kernel = json.loads((ROOT / "kaggle_notebooks/exp225_p26_research/kernel-metadata.json").read_text())
    kernel.update(id=KERNEL, title=metadata["title"], code_file=NAME)
    (OUT / "kernel-metadata.json").write_text(json.dumps(kernel, indent=2) + "\n", encoding="utf-8")
    receipt = {"status": "PASS_STATIC_BUILD_NO_INFERENCE", "kernel": KERNEL,
               "notebook_sha256": sha(path), "upstream_sha256": sha(DEFAULT_SOURCE),
               "preserved_original_cells": [i for i in range(12) if i != 5],
               "serializer_bounds_fix": True, "runtime_train_selection": True,
               "code_cells": sum(c["cell_type"] == "code" for c in cells)}
    (OUT / "build_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
