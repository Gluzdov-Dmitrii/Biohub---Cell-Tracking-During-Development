import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from select_source_centroid_radius import select


def _result(path: Path, scores: dict[str, float]) -> None:
    path.write_text(
        json.dumps(
            {
                "status": "PASS_FIXED_INTENSITY_CENTROID_FAMILY",
                "summary_by_arm": {arm: {"score": score} for arm, score in scores.items()},
                "per_movie_by_arm": {
                    arm: [{"dataset": "a"}, {"dataset": "b"}] for arm in scores
                },
            }
        ),
        encoding="utf-8",
    )


def test_selects_best_radius_and_decodes_it(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    order = ["translation", "intensity_centroid_r2_5_5", "intensity_centroid_r1_3_3"]
    _result(source, dict(zip(order, [0.7, 0.72, 0.71])))
    result = select(source, order)
    assert result["selected_arm"] == "intensity_centroid_r2_5_5"
    assert result["selected_radius_zyx_voxels"] == [2, 5, 5]
    assert abs(result["selected_delta_vs_translation"] - 0.02) < 1e-12


def test_ties_fall_back_to_translation(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    order = ["translation", "intensity_centroid_r2_5_5"]
    _result(source, {order[0]: 0.7, order[1]: 0.7})
    result = select(source, order)
    assert result["selected_arm"] == "translation"
    assert result["selected_radius_zyx_voxels"] is None
