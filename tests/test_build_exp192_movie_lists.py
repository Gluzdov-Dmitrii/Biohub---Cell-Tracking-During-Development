from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_exp192_movie_lists import derive


def test_direction_lists_are_exact_and_suffix_names():
    payload = {
        "missing": {
            "movies": [f"44b6_{i:08x}" for i in range(59)]
            + [f"6bba_{i:08x}" for i in range(116)]
        }
    }
    result = derive(payload)
    assert len(result["44b6_target"]) == 59
    assert len(result["6bba_target"]) == 116
    assert all(name.endswith(".zarr") for values in result.values() for name in values)
