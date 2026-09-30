from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_exp192_chunks import chunked


def test_chunks_are_sorted_bounded_and_complete():
    values = ["c", "a", "e", "b", "d"]
    chunks = chunked(values, 2)
    assert chunks == [["a", "b"], ["c", "d"], ["e"]]
    assert [value for chunk in chunks for value in chunk] == sorted(values)


def test_duplicate_rejected():
    try:
        chunked(["a", "a"], 2)
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate accepted")
