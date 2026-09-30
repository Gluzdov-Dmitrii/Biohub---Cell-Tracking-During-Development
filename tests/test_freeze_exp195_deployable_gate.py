import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from freeze_exp195_deployable_gate import percentile


def test_full_development_q75():
    assert percentile(list(range(12)), 0.75) == 8.25
