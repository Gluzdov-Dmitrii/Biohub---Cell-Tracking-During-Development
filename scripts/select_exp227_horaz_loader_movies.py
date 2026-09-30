"""Choose source44 train movies at the observed low/high graph-density ends from metadata only."""

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "work/horaz_development_20260922/exp227/loader_preload_dev_20260927"
REPORT = ROOT / "reports/exp227_horaz_loader_movie_selection_20260927.json"
SOURCE_MANIFEST_SHA = "455cc9d546b1ea0f05e9674f9513800c70bf8faf851f8cb303397d27af1129f5"


def main() -> None:
    assert not REPORT.exists()
    source_bytes = (STAGE / "source44_manifest.json").read_bytes()
    assert hashlib.sha256(source_bytes).hexdigest() == SOURCE_MANIFEST_SHA
    rows = json.loads(source_bytes)["train"]
    assert len(rows) == 63 and all(row["dataset_id"].startswith("44b6_") for row in rows)
    source = """import json
from pathlib import Path
rows = ROWS
result = []
for row in rows:
    geff = Path(row['geff_path'])
    image = Path(row['zarr_path'])
    node_meta = json.loads((geff/'nodes/ids/zarr.json').read_text())
    image_meta = json.loads((image/'0/zarr.json').read_text())
    node_count = int(node_meta['shape'][0])
    image_shape = [int(v) for v in image_meta['shape']]
    assert len(image_shape) == 4 and image_meta['data_type'] == 'uint16'
    assert node_count > 0 and image_shape[0] > 0
    result.append({'dataset_id': row['dataset_id'], 'node_count': node_count,
                   'image_shape': image_shape, 'image_dtype': image_meta['data_type'],
                   'mean_nodes_per_frame_upper_proxy': node_count/image_shape[0]})
print(json.dumps(result))
""".replace("ROWS", repr(rows))
    process = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "nsu-quadro", "python3 -"],
        input=source, text=True, capture_output=True, timeout=120, check=True,
    )
    counts = json.loads(process.stdout)
    assert len(counts) == 63
    ordered = sorted(counts, key=lambda row: (row["mean_nodes_per_frame_upper_proxy"], row["dataset_id"]))
    selected = [ordered[0], ordered[-1]]
    selected_ids = [row["dataset_id"] for row in selected]
    assert len(set(selected_ids)) == 2
    estimated_preload_bytes = sum(
        row["image_shape"][0] * row["image_shape"][1] *
        ((row["image_shape"][2] + 3) // 4) * ((row["image_shape"][3] + 3) // 4) * 2
        for row in selected
    )
    assert estimated_preload_bytes < 1 * 2**30
    receipt = {"status": "PASS_SOURCE44_LOADER_MOVIE_SELECTION_METADATA_ONLY",
               "source_manifest_sha256": SOURCE_MANIFEST_SHA,
               "candidate_count": len(counts), "selected": selected,
               "selected_ids_sparse_then_dense": selected_ids,
               "estimated_preload_bytes": estimated_preload_bytes,
               "density_basis": "GEFF nodes/ids shape divided by Zarr time dimension; source44 train metadata only",
               "target6bba_access": False}
    REPORT.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
