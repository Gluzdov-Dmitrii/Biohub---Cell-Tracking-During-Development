"""Estimate source44 preload array bytes from image metadata without image reads."""

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "work/horaz_development_20260922/exp227/loader_preload_dev_20260927/source44_manifest.json"
RECEIPT = ROOT / "reports/exp227_source44_preload_footprint_20260927.json"
MANIFEST_SHA = "455cc9d546b1ea0f05e9674f9513800c70bf8faf851f8cb303397d27af1129f5"


def main():
    assert not RECEIPT.exists()
    raw = MANIFEST.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == MANIFEST_SHA
    records = json.loads(raw)["train"]
    assert len(records) == 63 and all(row["dataset_id"].startswith("44b6_") for row in records)
    source = """import json
from pathlib import Path
rows = RECORDS
results=[]
for row in rows:
    meta=json.loads((Path(row['zarr_path'])/'0/zarr.json').read_text())
    assert meta['data_type']=='uint16'
    t,z,y,x=[int(v) for v in meta['shape']]
    result={'dataset_id':row['dataset_id'],'shape':[t,z,y,x],
            'preload_bytes':t*z*((y+3)//4)*((x+3)//4)*2}
    results.append(result)
print(json.dumps(results))
""".replace("RECORDS", repr(records))
    process = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "nsu-quadro", "python3 -"],
        input=source, text=True, capture_output=True, timeout=120, check=True,
    )
    items = json.loads(process.stdout)
    assert len(items) == 63 and len({row["dataset_id"] for row in items}) == 63
    total = sum(row["preload_bytes"] for row in items)
    result = {"status": "PASS_EXP227_SOURCE44_PRELOAD_METADATA_ESTIMATE",
              "source_manifest_sha256": MANIFEST_SHA, "movie_count": 63,
              "downsample": [1, 4, 4], "dtype": "uint16",
              "total_array_bytes": total,
              "minimum_array_bytes": min(row["preload_bytes"] for row in items),
              "maximum_array_bytes": max(row["preload_bytes"] for row in items),
              "cap_bytes": 8 * 1024**3,
              "under_option_cap": total < 8 * 1024**3,
              "metadata_only": True, "target6bba_access": False,
              "movies": items}
    RECEIPT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "movies"}))


if __name__ == "__main__":
    main()
