import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from select_exp194_nested_inference_gate import applies, percentile


def test_percentile_linear_interpolation():
    assert percentile([0.0, 10.0, 20.0], 0.25) == 5.0
    assert percentile([0.0, 10.0, 20.0], 0.5) == 10.0


def test_rule_application():
    feature = {"x": 0.5}
    assert applies({"label": "always_base"}, feature) is False
    assert applies({"label": "always_gap"}, feature) is True
    assert applies({"label": "x_le_q50", "feature": "x", "operator": "le", "threshold": 0.5}, feature) is True
