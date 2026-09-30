from __future__ import annotations

import json
import time
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi


ROOT = Path(__file__).resolve().parents[1]
INPUT_ROOT = ROOT / "outputs" / "research" / "external_inputs"
OUTPUT = INPUT_ROOT / "pilot_file_manifest_live.json"
COMPETITION = "biohub-cell-tracking-during-development"
CONTRACTS = [
    (INPUT_ROOT / "exp009" / "loeo_44b6_contract.json", 4),
    (INPUT_ROOT / "exp010" / "loeo_6bba_contract.json", 4),
]


def main() -> None:
    stems: list[str] = []
    for contract_path, audit_count in CONTRACTS:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        names = list(contract["checkpoint_validation"])
        names += [name for name in contract["calibration"] if name not in names]
        names += list(contract["audit"][:audit_count])
        stems.extend(Path(name).stem for name in names)
    stems = sorted(set(stems))
    prefixes = tuple(f"train/{stem}" for stem in stems)

    api = KaggleApi()
    api.authenticate()
    token = None
    page_count = 0
    files: list[dict[str, object]] = []
    while True:
        for attempt in range(5):
            try:
                response = api.competition_list_files(COMPETITION, page_token=token, page_size=200)
                break
            except Exception:
                if attempt == 4:
                    raise
                time.sleep(min(2**attempt, 30))
        page_count += 1
        for item in response.files or []:
            name = item.name
            if name.startswith(prefixes):
                files.append({"name": name, "size": int(item.total_bytes)})
        if page_count % 20 == 0:
            print(f"scanned_pages={page_count} matched_files={len(files)}", flush=True)
        token = response.next_page_token
        if not token:
            break

    prefix_counts: dict[str, int] = {}
    for item in files:
        prefix = str(item["name"]).split("/", 1)[0]
        prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
    payload = {
        "competition": COMPETITION,
        "purpose": "EXP063/064 24-movie external pilot; four calibration and four audit movies per holdout",
        "movies": stems,
        "file_count": len(files),
        "total_bytes": sum(int(item["size"]) for item in files),
        "pages_scanned": page_count,
        "prefix_counts": prefix_counts,
        "files": sorted(files, key=lambda item: str(item["name"])),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({key: payload[key] for key in ("file_count", "total_bytes", "pages_scanned")}, indent=2))


if __name__ == "__main__":
    main()
