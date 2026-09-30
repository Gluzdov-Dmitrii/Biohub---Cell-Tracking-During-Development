import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


spec = importlib.util.spec_from_file_location("exp225_audit", Path(__file__).parents[1] / "scripts/exp225_output_audit.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

SHAPES = {"hidden_unknown_9": (3, 4, 5, 6), "another_hidden_id": (1, 2, 2, 2)}


def node(dataset, node_id, t=0, z=1, y=1, x=1):
    return [0, dataset, "node", node_id, t, z, y, x, -1, -1]


def edge(source, target):
    return [0, "hidden_unknown_9", "edge", -1, -1, -1, -1, -1, source, target]


def valid_rows():
    return [node("hidden_unknown_9", 10), node("hidden_unknown_9", 20, 1),
            node("hidden_unknown_9", 30, 1), edge(10, 20), edge(10, 30),
            node("another_hidden_id", 10)]


def write_csv(tmp_path, rows, columns=None):
    path = tmp_path / "submission.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(audit.EXP225_COLUMNS if columns is None else columns)
        for i, row in enumerate(rows):
            writer.writerow([i, *row[1:]])
    return path


def test_dynamic_unknown_ids_division_and_no_edge_dataset(tmp_path):
    rows = valid_rows()
    rows[0][5] = "1.0"
    result = audit.audit_submission(write_csv(tmp_path, rows), SHAPES)
    assert result["rows"] == 6 and result["nodes"] == 4 and result["edges"] == 2
    assert result["submission_sha256"] == hashlib.sha256((tmp_path / "submission.csv").read_bytes()).hexdigest()
    assert result["per_dataset"]["hidden_unknown_9"]["division_nodes"] == 1
    assert result["per_dataset"]["another_hidden_id"]["isolated_nodes"] == 1
    assert result["per_dataset"]["another_hidden_id"]["maximum_in_degree"] == 0


def test_edge_before_nodes_and_large_exact_id(tmp_path):
    rows = valid_rows()
    rows[0][3] = str(2**53 + 1)
    rows[3][8] = rows[4][8] = str(2**53 + 1)
    rows = rows[3:5] + rows[:3] + rows[5:]
    assert audit.audit_submission(write_csv(tmp_path, rows), SHAPES)["edges"] == 2


@pytest.mark.parametrize("column,value,error", [
    (4, 3, "out of runtime bounds"), (5, 4, "out of runtime bounds"),
    (6, 5, "out of runtime bounds"), (7, 6, "out of runtime bounds"),
    (5, -1, "out of runtime bounds"), (5, "NaN", "finite integer"),
    (5, "Infinity", "finite integer"), (5, "1.5", "finite integer"),
    (3, "10.000000000000001", "finite integer"),
    (8, 0, "node sentinel"), (3, -1, "negative or duplicate"),
    (2, "other", "unknown row_type"), (1, "public_frozen_id", "unknown runtime dataset"),
])
def test_rejects_bad_node_fields(tmp_path, column, value, error):
    rows = valid_rows()
    rows[0][column] = value
    with pytest.raises(ValueError, match=error):
        audit.audit_submission(write_csv(tmp_path, rows), SHAPES)


@pytest.mark.parametrize("change,error", [
    (lambda rows: rows.append(edge(10, 999)), "orphan"),
    (lambda rows: rows.append(edge(10, 20)), "duplicate edge"),
    (lambda rows: rows.extend([node("hidden_unknown_9", 40), edge(40, 20)]), "in-degree"),
    (lambda rows: rows.extend([node("hidden_unknown_9", 40, 1), edge(10, 40)]), "out-degree"),
    (lambda rows: rows.append(edge(20, 30)), "consecutive frames"),
    (lambda rows: rows.append(node("hidden_unknown_9", 10)), "duplicate node"),
    (lambda rows: rows[3].__setitem__(3, 0), "edge sentinel"),
    (lambda rows: rows[3].__setitem__(8, -1), "negative edge endpoint"),
    (lambda rows: rows.pop(), "without any nodes"),
])
def test_rejects_graph_and_dataset_contract_failures(tmp_path, change, error):
    rows = valid_rows()
    change(rows)
    with pytest.raises(ValueError, match=error):
        audit.audit_submission(write_csv(tmp_path, rows), SHAPES)


def test_wrong_columns_and_noncontiguous_ids(tmp_path):
    with pytest.raises(ValueError, match="columns"):
        audit.audit_submission(write_csv(tmp_path, valid_rows(), list(reversed(audit.EXP225_COLUMNS))), SHAPES)
    path = write_csv(tmp_path, valid_rows())
    text = path.read_text().replace("0,hidden", "8,hidden", 1)
    path.write_text(text)
    with pytest.raises(ValueError, match="contiguous"):
        audit.audit_submission(path, SHAPES)


def test_runtime_discovers_actual_shapes_and_writes_receipt(tmp_path, monkeypatch):
    work = tmp_path / "work"
    test = tmp_path / "runtime_test"
    work.mkdir()
    test.mkdir()
    for dataset in SHAPES:
        (test / (dataset + ".zarr")).mkdir()
    write_csv(work, valid_rows())
    opened = []

    def open_group(path, mode):
        assert mode == "r"
        opened.append(Path(path).stem)
        return {"0": SimpleNamespace(shape=SHAPES[Path(path).stem])}

    monkeypatch.setitem(sys.modules, "zarr", SimpleNamespace(open_group=open_group))
    monkeypatch.setenv("BIOHUB_P26_TEST_SETTING", "resolved")
    result = audit.run_exp225_output_audit(test, work, source_evidence_status="VERIFIED_BY_CALLER")
    saved = json.loads((work / "exp225_runtime_audit.json").read_text())
    assert saved == result
    assert sorted(opened) == sorted(SHAPES)
    assert saved["runtime_shapes"] == {dataset: list(shape) for dataset, shape in SHAPES.items()}
    assert saved["resolved_biohub_environment"]["BIOHUB_P26_TEST_SETTING"] == "resolved"
    assert saved["source_evidence_status"] == "VERIFIED_BY_CALLER"
    nested = work / "nested"
    nested.mkdir()
    (nested / "submission.csv").write_text("duplicate")
    with pytest.raises(ValueError, match="exactly one root"):
        audit.run_exp225_output_audit(test, work)


def test_source_is_appendable_after_statements():
    compile("some_existing_statement = 1\n" + Path(audit.__file__).read_text(), "appended_audit", "exec")
