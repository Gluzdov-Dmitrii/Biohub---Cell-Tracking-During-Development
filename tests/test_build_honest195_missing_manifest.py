from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_honest195_missing_manifest import PUBLIC_TWINS, build_manifest


def test_exact_cohort_and_missing_file_selection():
    movies = list(PUBLIC_TWINS)
    movies += [f"44b6_{index:08x}" for index in range(69)]
    movies += [f"6bba_{index + 1000:08x}" for index in range(126)]
    assert len(set(movies)) == 199
    inventory = []
    for movie in movies:
        inventory.extend(
            [
                {"name": f"train/{movie}.zarr/zarr.json", "bytes": 10},
                {"name": f"train/{movie}.geff/data", "bytes": 20},
            ]
        )
    existing = set(list(PUBLIC_TWINS) + sorted(set(movies) - PUBLIC_TWINS)[:20])
    result = build_manifest(inventory, existing)
    assert result["all_train"] == {"movies": 199, "files": 398, "bytes": 5970}
    assert result["honest_evaluation"]["movies"] == 195
    assert len(result["already_verified"]["movies"]) == 20
    assert len(result["missing"]["movies"]) == 175
    assert result["missing"]["file_count"] == 350
    assert all(not any(twin in row["name"] for twin in PUBLIC_TWINS) for row in result["files"])
