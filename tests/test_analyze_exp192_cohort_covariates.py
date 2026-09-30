import json
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import analyze_exp192_cohort_covariates as module


def test_standardized_difference_direction():
    assert module.standardized_difference([1.0, 2.0], [3.0, 4.0]) > 0
    assert module.standardized_difference([2.0, 2.0], [2.0, 2.0]) == 0.0


def test_stats_single_value():
    result = module.stats([3.0])
    assert result["median"] == 3.0
    assert result["stdev"] == 0.0
