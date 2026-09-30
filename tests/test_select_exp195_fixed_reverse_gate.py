import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from select_exp195_fixed_reverse_gate import percentile


def test_q75_is_fit_from_training_values():
    assert percentile([0.0, 1.0, 2.0, 3.0, 4.0], 0.75) == 3.0
