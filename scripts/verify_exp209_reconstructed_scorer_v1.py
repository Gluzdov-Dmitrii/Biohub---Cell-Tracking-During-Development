"""Read-only independent completion verifier for the one-shot EXP209 scorer.

The remote probe reads only staged code, reconstruction graphs, controls, logs,
and scorer JSON receipts. It never opens GEFF or executes either metric.
An unfinished run returns RUNNING/SETTLING and creates no verification receipt.
"""

import hashlib
import json
import math
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1] if "__file__" in globals() else None
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
NAME = "exp209_reconstructed_current_scorer_v1_20260927"
CODE = f"{REMOTE}/code/{NAME}"
RUN = f"{REMOTE}/runs/{NAME}"
CONTROL = f"{REMOTE}/runs/.{NAME}.control"
RECON_CODE = f"{REMOTE}/code/exp209_current_metric_reconstruction_v1_20260927"
RECON_RUN = f"{REMOTE}/runs/exp209_current_metric_reconstruction_v1_20260927"
STAGE_INTENT = f"{REMOTE}/code/.{NAME}.stage_intent.json"
STAGE_COMPLETE = f"{REMOTE}/code/.{NAME}.stage_complete.json"
MANIFEST_SHA = "2484dfcacdfb47b2b33d6ab00ff0e9fa58b99943ad23421f5f9de253ff2255fb"
CONFIG_SHA = "d9a060b3d115db817f40fb9f81f8793c524fb112d9efb21b5767ad1ea3399335"
SCORER_SHA = "72e24bc53128c1e35ffe7dc806c74ccf0ad36575b52c5d7753ee60e2b3771b79"
SUPERVISOR_SHA = "e4831efe7d7d76c28f8e77ad3b6306226984bffae52e8de6fda45a9830f11204"
RECON_MANIFEST_SHA = "cdf49fad597f1dcc47e65d841cc894ed2be439f45f4bfe1838e790b390c8a311"
RECON_CONTRACT_SHA = "3860dce507c02b49386414a26c51071f6ff993e8b49476dc46e2b232973e8dd0"
RECON_GATE_SHA = "8379ffc4435b01d0a8b7c90087302001b0b7738914e84fdd0286b888e8ff32f1"
HISTORICAL_ROWS_SHA = "bcc57aeef14a9419daab17ca10398774d229f499926f53176948eab331c05e0c"
LEGACY_METRICS_SHA = "31baf45b54c78f68bab4f65dd8f4b38bca702abb644171c6df7c46cdeef55d83"
LEGACY_DIVISION_SHA = "d1cf1e0a43009d02174f1699ce2aa28458a2220ac4b521731d3bcf31cf8c76be"
CURRENT_METRICS_SHA = "cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444"
CURRENT_DIVISION_SHA = "0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9"
CURRENT_INIT_SHA = "de33668aee4fd1822a11989b432a7ba6c4b36fd2993ec8f564a63d427cde05de"
ORGANIZER_COMMIT = "075fc5f5a52d11077f9dc2b074644618f26939e2"
TRACKSDATA_COMMIT = "e13cf379b5127deeb8301ce56410fda35b5a3cf9"
HISTORICAL_SCORE = 0.6815218332750073
STAGE_RECEIPT_SHA = "1b386b7d454faec04344c93233fd5c01e479953214482671766c8a3ee9e36369"
LAUNCH_RECEIPT_SHA = "8f09dd93bca396879f30f205cced07e3a1516631f25241e29d82fdf518167566"
STAGE_RECEIPT = "reports/exp209_reconstructed_scorer_v1_stage_20260927.json"
LAUNCH_RECEIPT = "reports/exp209_reconstructed_scorer_v1_launch_20260927.json"
VERIFY_RECEIPT = "reports/exp209_reconstructed_scorer_v1_readonly_verify_20260927.json"
OLD_COUNTS = ("edge_tp", "edge_fp", "edge_fn", "division_tp", "division_fp",
              "division_fn", "num_pred_nodes")
OLD_FLOATS = ("node_recall", "total_node_ratio", "edge_jaccard", "adj_edge_jaccard")
ROW_KEYS = {"dataset", *OLD_COUNTS, *OLD_FLOATS}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load(path):
    def invalid(value):
        raise ValueError(f"nonfinite JSON token: {value}")
    return json.loads(Path(path).read_text(encoding="utf-8"), parse_constant=invalid)


def finite_tree(value):
    if isinstance(value, dict):
        return all(finite_tree(item) for item in value.values())
    if isinstance(value, list):
        return all(finite_tree(item) for item in value)
    return not isinstance(value, float) or math.isfinite(value)


def same_number(actual, expected, label):
    require(isinstance(actual, (int, float)) and not isinstance(actual, bool) and
            isinstance(expected, (int, float)) and not isinstance(expected, bool) and
            math.isfinite(float(actual)) and math.isfinite(float(expected)) and
            abs(float(actual) - float(expected)) <= 1e-12,
            f"{label} differs by more than 1e-12")


def compare_historical(archive, replay, ordered):
    """Independently compare actual replay rows and pooled projection to EXP209."""
    reference = []
    for direction, prefix, count in (("forward", "6bba_", 116),
                                     ("reverse", "44b6_", 59)):
        rows = archive["directions"][direction]["selected_rows"]
        require(len(rows) == count, f"archived {direction} row count changed")
        for row in rows:
            require(set(row) == ROW_KEYS and row["dataset"].endswith(".zarr"),
                    "archived EXP209 row fields/suffix changed")
            name = row["dataset"][:-5]
            require(name.startswith(prefix), "archived EXP209 direction changed")
            reference.append({**row, "dataset": name})
    require([row["dataset"] for row in reference] == ordered and
            len(set(ordered)) == 175, "archived EXP209 cohort differs from graphs")
    rows = replay["rows"]
    require(len(rows) == 175 and [row["dataset"] for row in rows] == ordered,
            "historical replay row IDs/order differ from archive")
    for actual, expected in zip(rows, reference):
        name = expected["dataset"]
        require(set(actual) == ROW_KEYS, f"{name}: historical replay fields changed")
        for key in OLD_COUNTS:
            require(type(actual[key]) is int and actual[key] == expected[key],
                    f"{name}/{key}: historical count differs")
        for key in OLD_FLOATS:
            same_number(actual[key], expected[key], f"{name}/{key}")
    archived = archive["combined"]["frozen_selected"]
    summary = replay["summary"]
    projected = {key: summary[key] for key in archived if key in summary}
    for key in ("edge_tp", "edge_fp", "edge_fn"):
        if key in archived:
            projected[key] = sum(row[key] for row in rows)
    require(set(projected) == set(archived) and
            set(replay["archived_comparable_summary"]) == set(archived),
            "historical pooled projection fields changed")
    for key, expected in archived.items():
        claimed = replay["archived_comparable_summary"][key]
        actual = projected[key]
        if key in (*OLD_COUNTS, "n"):
            require(type(actual) is int and actual == expected and
                    type(claimed) is int and claimed == actual,
                    f"historical pooled {key} differs")
        else:
            same_number(actual, expected, f"historical pooled {key}")
            same_number(claimed, actual, f"claimed historical pooled {key}")
    same_number(summary["score"], HISTORICAL_SCORE, "historical pooled score")
    same_number(replay["archived_exp209_score"], HISTORICAL_SCORE,
                "replay archived EXP209 score")


def original_absent(pid, tick):
    stat = Path(f"/proc/{pid}/stat")
    if not stat.is_file():
        return True
    fields = stat.read_text(encoding="utf-8").rsplit(") ", 1)[1].split()
    return fields[0] == "Z" or int(fields[19]) != tick


def group_absent(pid):
    for stat in Path("/proc").glob("[0-9]*/stat"):
        try:
            fields = stat.read_text(encoding="utf-8").rsplit(") ", 1)[1].split()
            if fields[0] != "Z" and int(fields[2]) == pid:
                return False
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    return True


def remote_verify(params):
    """Runs only on remote when transmitted over stdin; no GEFF path is visited."""
    stage, launch = params["stage"], params["launch"]
    require(params["stage_receipt_sha256"] == STAGE_RECEIPT_SHA and
            params["launch_receipt_sha256"] == LAUNCH_RECEIPT_SHA,
            "local receipt SHA pin changed")
    require(stage["status"] == "PASS_EXP209_SCORER_V1_STAGED_NO_RUN" and
            launch["status"] == "STARTED_EXP209_SCORER_V1_CPU_SUPERVISOR" and
            stage["code_dir"] == launch["control_dir"].replace(
                f"/runs/.{NAME}.control", f"/code/{NAME}") == CODE and
            stage["run_root"] == launch["run_root"] == RUN and
            stage["bundle_manifest_sha256"] == launch["bundle_manifest_sha256"] == MANIFEST_SHA and
            stage["config_sha256"] == launch["config_sha256"] == CONFIG_SHA and
            launch["local_stage_receipt_sha256"] == STAGE_RECEIPT_SHA and
            launch["supervisor_sha256"] == SUPERVISOR_SHA and
            launch["control_dir"] == CONTROL and
            stage["labels_read"] is False and stage["metric_executed"] is False and
            stage["gpu_used"] is False and stage["remote_run_created"] is False and
            launch["launcher_geff_opened"] is False and
            launch["launcher_target_metric_executed"] is False and
            launch["gpu_used"] is False,
            "local reviewed stage/launch receipt identity changed")
    control, run, code = Path(CONTROL), Path(RUN), Path(CODE)
    require(control.is_dir() and code.is_dir(), "remote scorer control/code absent")
    completion_path = control / "completion.json"
    if not completion_path.is_file():
        return {"status": "RUNNING_EXP209_SCORER_V1_NO_RESULT_CLAIM",
                "completion_absent": True,
                "worker_identity_alive": not original_absent(
                    launch["worker_pid"], launch["worker_start_tick"]),
                "scorer_output_exists": run.exists()}
    completion = load(completion_path)
    if (not original_absent(launch["supervisor_pid"], launch["supervisor_start_tick"]) or
            not original_absent(launch["worker_pid"], launch["worker_start_tick"]) or
            not group_absent(launch["worker_pid"])):
        return {"status": "SETTLING_EXP209_SCORER_V1_NO_RESULT_CLAIM",
                "completion_sha256": sha(completion_path)}
    if (completion.get("status") != "EXIT0_EXP209_SCORER_V1" or
            completion.get("exit_code") != 0 or completion.get("timed_out") is not False or
            completion.get("worker_absent") is not True):
        return {"status": "FAILED_EXP209_SCORER_V1_NO_VERIFIED_SCORE",
                "completion_sha256": sha(completion_path),
                "completion_status": completion.get("status"),
                "exit_code": completion.get("exit_code"),
                "timed_out": completion.get("timed_out")}
    require(completion["worker_pid"] == launch["worker_pid"] and
            completion["worker_start_tick"] == launch["worker_start_tick"] and
            completion["run_root"] == RUN and
            completion["bundle_manifest_sha256"] == MANIFEST_SHA and
            completion["config_sha256"] == CONFIG_SHA and
            completion["gpu_used"] is False and
            completion["kaggle_post"] is False and
            completion["result_sha256"] is not None,
            "scorer completion fields differ from launch")
    expected_control = {"launch_intent.json", "supervisor.py", "supervisor.log",
                        "worker_intent.json", "worker_started.json", "worker.log",
                        "supervisor_started.json", "completion.json"}
    require({p.name for p in control.iterdir()} == expected_control,
            "scorer control has missing/extra files")
    require(sha(control / "supervisor.py") == SUPERVISOR_SHA and
            sha(control / "launch_intent.json") == launch["remote_launch_intent_sha256"] and
            sha(control / "worker_started.json") == launch["worker_started_sha256"] and
            sha(Path(STAGE_COMPLETE)) == stage["remote_stage_complete_sha256"] and
            sha(Path(STAGE_INTENT)) == stage["remote_stage_intent_sha256"],
            "remote stage/launch/control SHA readback failed")
    intent = load(control / "launch_intent.json")
    started = load(control / "supervisor_started.json")
    worker = load(control / "worker_started.json")
    require(intent["status"] == "LAUNCH_INTENT_EXP209_SCORER_V1_CPU_ONLY" and
            intent["local_stage_receipt_sha256"] == STAGE_RECEIPT_SHA and
            intent["reconstruction_gate_sha256"] == RECON_GATE_SHA and
            intent["labels_read"] is False and intent["gpu_used"] is False and
            started["status"] == "STARTED_EXP209_SCORER_V1_CPU_SUPERVISOR" and
            started["supervisor_pid"] == launch["supervisor_pid"] and
            started["supervisor_start_tick"] == launch["supervisor_start_tick"] and
            started["worker_pid"] == launch["worker_pid"] and
            started["worker_start_tick"] == launch["worker_start_tick"] and
            worker["status"] == "STARTED_EXP209_SCORER_V1_CPU_ONLY" and
            worker["pid"] == launch["worker_pid"] and
            worker["start_tick"] == launch["worker_start_tick"] and
            worker["memory_limit_bytes"] == 32 * 1024**3 and
            worker["wall_timeout_seconds"] == 28800 and
            len(worker["cpu_affinity"]) == 8,
            "remote scorer launch/worker controls differ from reviewed launch")
    manifest_path, config_path = code / "bundle_manifest.json", code / "config.json"
    require(sha(manifest_path) == MANIFEST_SHA and sha(config_path) == CONFIG_SHA and
            sha(code / "score_exp209_reconstructed_current_v1.py") == SCORER_SHA,
            "staged scorer manifest/config/source changed")
    manifest, config = load(manifest_path), load(config_path)
    require(manifest["experiment"] == "EXP209_RECONSTRUCTED_CURRENT_SCORER_V1" and
            len(manifest["files"]) == 14 and config["scorer_code_dir"] == CODE and
            config["output"] == RUN and
            config["reconstruction_gate_sha256"] == RECON_GATE_SHA and
            config["reconstruction_bundle_manifest_sha256"] == RECON_MANIFEST_SHA and
            config["reconstruction_contract_sha256"] == RECON_CONTRACT_SHA and
            config["metric_repo_commit"] == ORGANIZER_COMMIT and
            config["tracksdata_commit"] == TRACKSDATA_COMMIT,
            "staged scorer manifest/config provenance changed")
    actual_files = {p.relative_to(code).as_posix(): sha(p) for p in code.rglob("*")
                    if p.is_file()}
    require(not any(p.is_symlink() for p in code.rglob("*")) and
            actual_files == stage["file_hashes"] and
            len(actual_files) == 15 and
            actual_files["current_official/__init__.py"] == CURRENT_INIT_SHA and
            actual_files["current_official/metrics.py"] == CURRENT_METRICS_SHA and
            actual_files["current_official/division_metrics.py"] == CURRENT_DIVISION_SHA and
            actual_files["legacy_official/metrics.py"] == LEGACY_METRICS_SHA and
            actual_files["legacy_official/division_metrics.py"] == LEGACY_DIVISION_SHA,
            "remote scorer payload hash map changed")
    require(sha(Path(RECON_CODE) / "bundle_manifest.json") == RECON_MANIFEST_SHA,
            "reconstruction source manifest changed")
    contract_path = Path(config["reconstruction_contract"])
    recon_gate_path = Path(RECON_RUN) / "no_metric_gate.json"
    require(contract_path == Path(RECON_CODE) / "contract.json" and
            sha(contract_path) == RECON_CONTRACT_SHA and
            sha(recon_gate_path) == RECON_GATE_SHA,
            "reconstruction contract/graph gate changed")
    contract, reconstruction_gate = load(contract_path), load(recon_gate_path)
    require(contract["code_dir"] == RECON_CODE and
            contract["run_root"] == RECON_RUN and
            reconstruction_gate["status"] == "PASS_EXP209_RECONSTRUCTION175_NO_METRIC_GATE" and
            reconstruction_gate["labels_read"] is False and
            reconstruction_gate["scientific_metrics_emitted"] is False and
            reconstruction_gate["movie_count"] == 175 and
            reconstruction_gate["direction_counts"] == {"forward": 116, "reverse": 59} and
            reconstruction_gate["chunk_count"] == 8,
            "reconstruction graph gate fields changed")
    require(run.is_dir() and {p.name for p in run.iterdir()} ==
            {"no_metric_gate.json", "historical_replay.json", "result.json"},
            "scorer output has missing/extra files or anomaly receipt")
    graph_gate_path = run / "no_metric_gate.json"
    historical_path = run / "historical_replay.json"
    result_path = run / "result.json"
    require(sha(graph_gate_path) == completion["no_metric_gate_sha256"] and
            sha(historical_path) == completion["historical_replay_sha256"] and
            sha(result_path) == completion["result_sha256"],
            "supervisor completion output hashes changed")
    graph_gate, historical, result = load(graph_gate_path), load(historical_path), load(result_path)
    require(finite_tree(graph_gate) and finite_tree(historical) and finite_tree(result),
            "nonfinite scorer output value")
    require(graph_gate["status"] == "PASS_EXP209_RECONSTRUCTED175_INDEPENDENT_NO_METRIC_GATE" and
            graph_gate["labels_read"] is False and
            graph_gate["scientific_metrics_emitted"] is False and
            graph_gate["current_organizer_score"] is None and
            graph_gate["movie_count"] == 175 and
            graph_gate["direction_counts"] == {"forward": 116, "reverse": 59} and
            graph_gate["chunk_count"] == 8 and
            graph_gate["source_telemetry_replay"] == "PASS_ALL175" and
            graph_gate["reconstruction_gate_sha256"] == RECON_GATE_SHA and
            graph_gate["reconstruction_contract_sha256"] == RECON_CONTRACT_SHA and
            graph_gate["reconstruction_bundle_manifest_sha256"] == RECON_MANIFEST_SHA and
            graph_gate["historical_exp209_selected_rows_sha256"] == HISTORICAL_ROWS_SHA and
            graph_gate["sealed_graph_hashes"] == reconstruction_gate["graph_hashes"] and
            graph_gate["control_hashes"] == reconstruction_gate["control_hashes"] and
            graph_gate["isolated_runtime_metadata"]["profile"] == "remote_py311" and
            graph_gate["isolated_runtime_metadata"]["tracksdata_commit"] ==
            TRACKSDATA_COMMIT,
            "scorer durable no-metric graph gate differs from reconstruction")
    sealed = graph_gate["sealed_graph_hashes"]
    ordered = [row["dataset"] for row in sealed]
    require(len(sealed) == len(set(ordered)) == 175 and
            len(graph_gate["reconstructed_source_records"]) == 175 and
            [row["dataset"] for row in graph_gate["reconstructed_source_records"]] == ordered,
            "scorer source replay/graph cohort incomplete")
    graph_map = {name: Path(RECON_RUN) / "chunks" / chunk["name"] / "output" /
                 f"graph__{name}.csv" for chunk in contract["chunks"] for name in chunk["movies"]}
    contract_order = [name for chunk in contract["chunks"] for name in chunk["movies"]]
    require(len(contract["chunks"]) == 8 and contract_order == ordered and
            len(graph_map) == 175, "contract chunk order differs from scorer graph gate")
    for row in sealed:
        name, path = row["dataset"], graph_map[row["dataset"]]
        require(sha(path) == row["csv_sha256"] and
                sha(path.with_suffix(".receipt.json")) == row["receipt_sha256"],
                f"{name}: actual graph/receipt bytes differ from no-metric gate")
    archive_path = Path(contract["historical_result"])
    require(sha(archive_path) == HISTORICAL_ROWS_SHA,
            "archived EXP209 selected rows changed")
    archive = load(archive_path)
    require(historical["status"] == "PASS_EXP209_RECONSTRUCTED_HISTORICAL175_REPLAY_1E12" and
            historical["archived_exp209_selected_rows_sha256"] == HISTORICAL_ROWS_SHA and
            historical["historical_metrics_sha256"] == LEGACY_METRICS_SHA and
            historical["historical_division_sha256"] == LEGACY_DIVISION_SHA and
            historical["no_metric_gate_sha256"] == sha(graph_gate_path) and
            len(historical["label_tree_hashes"]) == 175 and
            set(historical["label_tree_hashes"]) == set(ordered),
            "historical replay receipt provenance changed")
    compare_historical(archive, historical, ordered)
    require(result["status"] == "PASS_EXP209_RECONSTRUCTED175_CURRENT_ORGANIZER_V1" and
            result["evidence_class"] ==
            "leakage-controlled reciprocal evaluation; historically exposed target labels" and
            result["graph_identity"] ==
            "new reconstructed graphs; original final graph byte identity unavailable" and
            result["no_metric_gate_sha256"] == sha(graph_gate_path) and
            result["historical_replay_sha256"] == sha(historical_path) and
            result["historical_replay"] == "PASS_ALL175_FIELDS_AND_POOLED_SCORE_1E12" and
            result["metric_repo_commit"] == ORGANIZER_COMMIT and
            result["current_metrics_sha256"] == CURRENT_METRICS_SHA and
            result["current_division_sha256"] == CURRENT_DIVISION_SHA and
            result["tracksdata_commit"] == TRACKSDATA_COMMIT and
            result["labels_read_only_after_durable_no_metric_gate"] is True and
            result["runtime"]["profile"] == "remote_py311" and
            result["runtime"]["tracksdata_commit"] == TRACKSDATA_COMMIT and
            result["synthetic_contract"]["status"] ==
            "PASS_CURRENT_ORGANIZER_LOCAL_FORK_CONTRACT",
            "current organizer result provenance/gates changed")
    rows = result["rows"]
    require(len(rows) == 175 and [row["dataset"] for row in rows] == ordered and
            result["summary"]["n"] == 175 and
            result["summary"]["n_adj"] == 175 and
            math.isfinite(float(result["summary"]["score"])),
            "current organizer row coverage or pooled score invalid")
    for row, graph in zip(rows, sealed):
        require(set(row) == ROW_KEYS and
                all(type(row[key]) is int and row[key] >= 0 for key in OLD_COUNTS) and
                all(isinstance(row[key], (int, float)) and not isinstance(row[key], bool) and
                    math.isfinite(float(row[key])) for key in OLD_FLOATS) and
                row["num_pred_nodes"] == graph["nodes"],
                f"{graph['dataset']}: current organizer row anomalous")
    worker_lines = (control / "worker.log").read_text(encoding="utf-8").splitlines()
    supervisor_lines = (control / "supervisor.log").read_text(encoding="utf-8").splitlines()
    require(worker_lines and supervisor_lines and
            not any("Traceback" in line or "MemoryError" in line for line in worker_lines) and
            load_last_json(worker_lines)["status"] == result["status"] and
            load_last_json(supervisor_lines)["status"] == completion["status"],
            "scorer/supervisor log final status or anomaly differs")
    same_number(load_last_json(worker_lines)["score"], result["summary"]["score"],
                "worker final score")
    return {"status": "VERIFIED_EXP209_RECONSTRUCTED175_CURRENT_ORGANIZER_V1",
            "evidence_class": result["evidence_class"],
            "graph_identity": result["graph_identity"],
            "historical_replay": "PASS_ALL175_FIELDS_AND_POOLED_SCORE_1E12",
            "historical_score": historical["summary"]["score"],
            "current_score": result["summary"]["score"],
            "rows": 175, "direction_counts": {"forward": 116, "reverse": 59},
            "bundle_manifest_sha256": MANIFEST_SHA, "config_sha256": CONFIG_SHA,
            "reconstruction_gate_sha256": RECON_GATE_SHA,
            "scorer_no_metric_gate_sha256": sha(graph_gate_path),
            "historical_replay_sha256": sha(historical_path),
            "result_sha256": sha(result_path),
            "completion_sha256": sha(completion_path),
            "worker_log_sha256": sha(control / "worker.log"),
            "supervisor_log_sha256": sha(control / "supervisor.log"),
            "worker_absent": True, "timeout": False, "gpu_used": False,
            "geff_read_by_verifier": False, "metric_executed_by_verifier": False,
            "kaggle_post": False}


def load_last_json(lines):
    def invalid(value):
        raise ValueError(f"nonfinite log JSON token: {value}")
    return json.loads(lines[-1], parse_constant=invalid)


def local_parameters():
    require(ROOT is not None, "local verifier root unavailable")
    stage_path, launch_path = ROOT / STAGE_RECEIPT, ROOT / LAUNCH_RECEIPT
    require(sha(stage_path) == STAGE_RECEIPT_SHA and
            sha(launch_path) == LAUNCH_RECEIPT_SHA,
            "reviewed local stage/launch receipt SHA mismatch")
    stage, launch = load(stage_path), load(launch_path)
    require(launch["local_stage_receipt_sha256"] == STAGE_RECEIPT_SHA and
            stage["bundle_manifest_sha256"] == MANIFEST_SHA and
            launch["bundle_manifest_sha256"] == MANIFEST_SHA and
            stage["config_sha256"] == CONFIG_SHA and
            launch["config_sha256"] == CONFIG_SHA,
            "local scorer stage/launch receipt pin mismatch")
    return {"stage": stage, "launch": launch,
            "stage_receipt_sha256": STAGE_RECEIPT_SHA,
            "launch_receipt_sha256": LAUNCH_RECEIPT_SHA}


def probe(host="nsu-quadro"):
    params = local_parameters()
    source = "REMOTE_PARAMETERS = " + repr(params) + "\n" + Path(__file__).read_text(encoding="utf-8")
    result = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
                             host, "env", "PYTHONDONTWRITEBYTECODE=1", "python3", "-"],
                            input=source, text=True,
                            capture_output=True, timeout=900)
    require(result.returncode == 0,
            f"read-only EXP209 remote verifier exit {result.returncode}: {result.stderr[-2500:]}")
    lines = result.stdout.strip().splitlines()
    require(len(lines) == 1, "read-only EXP209 verifier returned ambiguous stdout")
    return json.loads(lines[0])


def write_verified_receipt(value):
    path = ROOT / VERIFY_RECEIPT
    require(not path.exists(), "existing EXP209 verification receipt requires reconciliation")
    data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return path


def main():
    verified = probe()
    if verified["status"] == "VERIFIED_EXP209_RECONSTRUCTED175_CURRENT_ORGANIZER_V1":
        receipt = {**verified,
                   "local_stage_receipt_sha256": STAGE_RECEIPT_SHA,
                   "local_launch_receipt_sha256": LAUNCH_RECEIPT_SHA,
                   "verifier_source_sha256": sha(Path(__file__)),
                   "read_only_remote_probe": True}
        path = write_verified_receipt(receipt)
        print(json.dumps({"status": receipt["status"],
                          "score": receipt["current_score"],
                          "historical_score": receipt["historical_score"],
                          "rows": receipt["rows"], "receipt": str(path)}))
    else:
        print(json.dumps(verified, sort_keys=True))


if __name__ == "__main__":
    if "REMOTE_PARAMETERS" in globals():
        print(json.dumps(remote_verify(REMOTE_PARAMETERS), sort_keys=True))
    else:
        main()
