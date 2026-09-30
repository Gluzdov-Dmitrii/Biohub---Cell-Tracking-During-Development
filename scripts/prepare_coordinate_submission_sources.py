"""Create candidate-specific Kaggle notebook wrappers for EXP060/061."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    out_dir = Path(sys.argv[1])
    selected = sys.argv[2]
    tag = sys.argv[3]
    kernel_id = sys.argv[4]
    title = sys.argv[5]

    metadata_path = out_dir / "kernel-metadata.json"
    notebook_path = out_dir / "coordinate_frontier_submission.ipynb"

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["id"] = kernel_id
    metadata["title"] = title
    metadata["code_file"] = notebook_path.name
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    notebook.setdefault("metadata", {}).setdefault("kaggle", {})["title"] = title
    notebook.setdefault("metadata", {}).setdefault("codex", {})["candidate_tag"] = tag
    notebook["cells"].append(
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Select exactly one pre-registered candidate as the root submission.\n",
                f"_candidate_path = Path('/kaggle/working/{selected}')\n",
                "if not _candidate_path.is_file():\n",
                "    raise FileNotFoundError(f'Missing selected candidate: {_candidate_path}')\n",
                "shutil.copy2(_candidate_path, SUBMISSION_PATH)\n",
                f"print('SELECTED_CANDIDATE: {tag}; root={{SUBMISSION_PATH}}')\n",
                "_selected_sha = _frontier_sha(SUBMISSION_PATH)\n",
                "print(f'SELECTED_CANDIDATE_SHA256: {_selected_sha}')\n",
            ],
        }
    )
    notebook_path.write_text(
        json.dumps(notebook, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"prepared {tag}: {notebook_path}")


if __name__ == "__main__":
    main()
