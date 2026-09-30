"""Prepare the D3-S14 hidden-compatible weak tie-break candidate."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def replace_assignment(lines: list[str], prefix: str, replacement: str) -> list[str]:
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            lines[index] = replacement
            return lines
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    lines.append(replacement)
    return lines


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: prepare_s14_weak_tiebreak.py OUTPUT_DIR")

    output_dir = Path(sys.argv[1])
    source_path = Path("outputs/research/frontier_20260904/arnav0940e/biohub-940e.ipynb")
    output_dir.mkdir(parents=True, exist_ok=True)

    notebook = json.loads(source_path.read_text(encoding="utf-8"))
    cells = notebook["cells"]

    config = "".join(cells[0]["source"]).splitlines(keepends=True)
    config = replace_assignment(config, "BIOHUB_PRESET =", "BIOHUB_PRESET = 'd3_s14_weak_learned_tiebreak'\n")
    config = replace_assignment(
        config,
        "BIOHUB_SCORE_AXIS =",
        "BIOHUB_SCORE_AXIS = 'D3-S14: registered-motion ambiguity resolved with a fixed 10% learned tie-break'\n",
    )
    config = replace_assignment(config, 'os.environ["BIOHUB_MOTION_RELINK_TIGHT_UM"]', 'os.environ["BIOHUB_MOTION_RELINK_TIGHT_UM"] = "7.0"\n')
    config = replace_assignment(config, 'os.environ["BIOHUB_MOTION_RELINK_RELAXED_UM"]', 'os.environ["BIOHUB_MOTION_RELINK_RELAXED_UM"] = "7.0"\n')
    config = replace_assignment(config, 'os.environ["BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT"]', 'os.environ["BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT"] = "0.0"\n')
    config = replace_assignment(config, 'os.environ["BIOHUB_MOTION_RELINK_LEARNED_BONUS"]', 'os.environ["BIOHUB_MOTION_RELINK_LEARNED_BONUS"] = "0.1"\n')
    config = replace_assignment(config, 'os.environ["BIOHUB_OUTPUT_MOTION_RELINK"]', 'os.environ["BIOHUB_OUTPUT_MOTION_RELINK"] = "1"\n')
    cells[0]["source"] = config

    guard = "".join(cells[1]["source"]).splitlines(keepends=True)
    marker = '    "BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT": 0.15,\n'
    if marker in guard:
        insert_at = guard.index(marker) + 1
        guard[insert_at:insert_at] = [
            '    "BIOHUB_MOTION_RELINK_TIGHT_UM": 7.0,\n',
            '    "BIOHUB_MOTION_RELINK_RELAXED_UM": 7.0,\n',
            '    "BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT": 0.0,\n',
            '    "BIOHUB_MOTION_RELINK_LEARNED_BONUS": 0.1,\n',
        ]
    cells[1]["source"] = guard

    pipeline = "".join(cells[2]["source"]).splitlines(keepends=True)
    pipeline = replace_assignment(
        pipeline,
        "EXPERIMENT_TAG =",
        'EXPERIMENT_TAG = "d3_s14_weak_learned_tiebreak"\n',
    )
    cells[2]["source"] = pipeline

    notebook.setdefault("metadata", {}).setdefault("kaggle", {})["title"] = (
        "Biohub Exp128 D3 S14 Weak Learned Tiebreak"
    )
    notebook.setdefault("metadata", {})["codex"] = {
        "candidate_tag": "EXP128 D3-S14 PRIVATE_ROBUST weak learned tie-break",
        "parent_source": str(source_path),
        "mechanism": "registered motion with fixed 10% learned ambiguity tie-break",
        "hidden_test_dataflow": "dynamic competition test/*.zarr inference",
    }

    notebook_path = output_dir / "weak_learned_tiebreak.ipynb"
    notebook_path.write_text(
        json.dumps(notebook, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    metadata = json.loads(
        Path("outputs/research/frontier_20260904/arnav0940e/kernel-metadata.json").read_text(
            encoding="utf-8"
        )
    )
    metadata.pop("id_no", None)
    metadata.update(
        {
            "id": "dmitriigluzdov/biohub-exp128-d3-s14-weak-learned-tiebreak",
            "title": "Biohub Exp128 D3 S14 Weak Learned Tiebreak",
            "code_file": notebook_path.name,
            "is_private": True,
        }
    )
    (output_dir / "kernel-metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(notebook_path)


if __name__ == "__main__":
    main()
