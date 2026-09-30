"""Receipt-backed identity, output audit, and one-shot guarded LB submission."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
COMP = "biohub-cell-tracking-during-development"
CASES = {
    "232": {
        "kernel": "dmitriigluzdov/biohub-exp232-p26-runtime-selection",
        "directory": "kaggle_notebooks/exp232_p26_runtime_selection",
        "description": "EXP232 P26 RUNTIME PROXY SWEEP GOLD_PUBLIC SLOT1 20260924",
        "track": "GOLD_PUBLIC", "slot": 1,
        "parent": "P26 zhehaoliang v1 public .947; EXP225 fixed-tight55 .946",
        "hypothesis": "Original P26 train-proxy sweep can recover or improve its selected public graph over EXP225 frozen tight55 while maintaining dynamic test inference.",
        "dataflow": "Runtime competition test Zarr -> pinned P26 dual temporal models/DeepCenter -> graph repairs -> visible-train proxy selection -> reserialize current test graph -> one root CSV.",
        "gate": "Clean offline version, source SHA parity, exact runtime IDs and graph audit; public score must exceed EXP225 .946 to promote. No private-robust claim.",
    },
    "233": {
        "kernel": "dmitriigluzdov/biohub-exp233-own-frontier90-notebook",
        "directory": "kaggle_notebooks/exp233_own_frontier90_notebook",
        "description": "EXP233 OWN FRONTIER90 NOTEBOOK PRIVATE_ROBUST SLOT3 20260924",
        "track": "PRIVATE_ROBUST", "slot": 3,
        "parent": "Our EXP219 ref public .922; reciprocal embryo paired development .7427291486",
        "hypothesis": "The verified owned reciprocal-fold bundle yields a reproducible, mechanism-diverse production notebook for the final two-model portfolio.",
        "dataflow": "Runtime competition test Zarr -> SHA-pinned owned EXP219 folds, one source per movie -> temporal inference/linker -> graph assembly -> one root CSV.",
        "gate": "Clean offline version, manifest/model SHA, exact runtime IDs and graph audit; public score must reproduce EXP219 .922 within evaluation tolerance. Unknown-embryo routing remains unvalidated.",
    },
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def save(work: Path, name: str, payload: dict) -> dict:
    work.mkdir(parents=True, exist_ok=True)
    payload = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(), **payload}
    (work / name).write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    return payload


def api_client():
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()
    return api


def identity(api, case: dict, work: Path) -> dict:
    from submit_code_file_once import get_current_kernel, validate_remote_kernel_identity
    remote = get_current_kernel(api, case["kernel"])
    meta = remote.metadata
    local_dir = ROOT / case["directory"]
    local_meta = json.loads((local_dir / "kernel-metadata.json").read_text(encoding="utf-8"))
    local_path = local_dir / local_meta["code_file"]
    local = json.loads(local_path.read_text(encoding="utf-8"))
    downloaded = json.loads(remote.blob.source)
    cells = lambda notebook: [(cell["cell_type"], "".join(cell["source"])) for cell in notebook["cells"]]
    assert cells(local) == cells(downloaded), "remote notebook cells differ from local candidate"
    work.mkdir(parents=True, exist_ok=True)
    source_path = work / "remote_source.ipynb"
    source_path.write_bytes(remote.blob.source.encode("utf-8"))
    digest = sha(source_path)
    version = int(meta.current_version_number)
    validate_remote_kernel_identity(remote, case["kernel"], version, COMP, digest)
    assert meta.enable_internet is False and meta.is_private is True
    return save(work, "source_identity.json", {
        "kernel": case["kernel"], "version": version, "source_sha256": digest,
        "local_source_sha256": sha(local_path), "cells_equal": True,
        "internet": meta.enable_internet, "private": meta.is_private,
        "metadata": meta.to_dict(),
    })


def status(api, case: dict) -> dict:
    result = api.kernels_status(case["kernel"])
    return {"kernel": case["kernel"], "status": str(result.status), "response": result.to_dict()}


def audit(api, case: dict, work: Path) -> dict:
    import requests
    from kagglesdk.kernels.types.kernels_api_service import ApiListKernelSessionOutputRequest
    from exp225_output_audit import audit_submission

    ident = identity(api, case, work)
    state = status(api, case)
    assert state["status"].endswith(".COMPLETE"), state
    files, logs, seen = [], [], set()
    token = None
    while True:
        request = ApiListKernelSessionOutputRequest()
        request.user_name, request.kernel_slug = case["kernel"].split("/")
        api._set_paging(request, 100, token)
        with api.build_kaggle_client() as client:
            response = client.kernels.kernels_api_client.list_kernel_session_output(request)
        files.extend(response.files or [])
        if response.log:
            logs.append(response.log)
        token = response.next_page_token
        if not token:
            break
        assert token not in seen
        seen.add(token)
    names = [item.file_name for item in files]
    assert len(names) == len(set(names))
    assert [name for name in names if PurePosixPath(name).name == "submission.csv"] == ["submission.csv"]
    out = ROOT / f"outputs/kaggle/exp{case['experiment']}_v{ident['version']}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "kernel.log").write_text("\n".join(logs), encoding="utf-8")
    (out / "output_inventory.json").write_text(json.dumps({"files": names, "identity": ident}, indent=2) + "\n", encoding="utf-8")
    required = ["submission.csv", "exp225_runtime_audit.json"]
    if case["experiment"] == "233":
        required.append("exp214_runtime_receipt.json")
    for name in required:
        assert name in names, name
        item = next(item for item in files if item.file_name == name)
        destination = out / name
        with requests.get(item.url, stream=True, timeout=(30, 180)) as response:
            response.raise_for_status()
            part = destination.with_suffix(destination.suffix + ".partial")
            with part.open("wb") as stream:
                for block in response.iter_content(1024 * 1024):
                    stream.write(block)
            part.replace(destination)
    runtime = json.loads((out / "exp225_runtime_audit.json").read_text(encoding="utf-8"))
    assert runtime["status"] == "PASS_EXP225_RUNTIME_OUTPUT_AUDIT"
    checked = audit_submission(out / "submission.csv", runtime["runtime_shapes"])
    assert checked["submission_sha256"] == runtime["submission_sha256"] == sha(out / "submission.csv")
    assert runtime["one_root_submission"] and checked["dynamic_runtime_id_equality"]
    if case["experiment"] == "233":
        inference = json.loads((out / "exp214_runtime_receipt.json").read_text(encoding="utf-8"))
        assert inference["status"] == "PASS_FULL_INFERENCE"
        assert sorted(inference["runtime_datasets"]) == checked["datasets"]
        assert inference["submission_sha256"] == checked["submission_sha256"]
        assert inference["unknown_embryo_selector_oof"] is None
    receipt = save(work, "prepost.json", {
        "status": "PASS_PREPOST", "track": case["track"], "slot": case["slot"],
        "hypothesis": case["hypothesis"], "parent": case["parent"],
        "hidden_test_dataflow": case["dataflow"], "expected_output": "submission.csv",
        "identity": ident, "audit": checked,
        "runtime_receipt_sha256": sha(out / "exp225_runtime_audit.json"),
        "inventory_sha256": sha(out / "output_inventory.json"),
        "promotion_gate": case["gate"], "description": case["description"],
    })
    return {"status": receipt["status"], "identity": ident, "audit": checked,
            "output": str(out / "submission.csv")}


def readback(api, case: dict, work: Path) -> dict:
    submissions = api.competition_submissions(COMP)
    matches = [item for item in submissions if item.description == case["description"]]
    fields = ("ref", "date", "description", "status", "public_score", "error_description", "total_bytes", "url")
    rows = [{key: getattr(item, key, None) for key in fields} for item in matches]
    anomalies = []
    for row in rows:
        state = str(row["status"]).rsplit(".", 1)[-1].upper()
        if state == "ERROR" or row["error_description"]:
            anomalies.append({"ref": row["ref"], "reason": str(row["error_description"] or state)})
        if state == "COMPLETE" and (not str(row["public_score"] or "").strip() or not int(row["total_bytes"] or 0)):
            anomalies.append({"ref": row["ref"], "reason": "COMPLETE without score or bytes"})
    state = "ANOMALY_STOP_NO_RETRY" if anomalies else (
        "SCORED" if len(rows) == 1 and str(rows[0]["status"]).endswith("COMPLETE") else "PENDING_OR_NOT_FOUND")
    return save(work, "submission_full_api.json", {"status": state, "matches": rows,
        "anomalies": anomalies, "quota": api.competition_get_submission_limits(COMP).to_dict()})


def submit(api, case: dict, work: Path) -> dict:
    prior = json.loads((work / "prepost.json").read_text(encoding="utf-8"))
    assert prior["status"] == "PASS_PREPOST"
    ident = identity(api, case, work)
    assert (ident["version"], ident["source_sha256"]) == (prior["identity"]["version"], prior["identity"]["source_sha256"])
    tests = json.loads((work / "required_tests.json").read_text(encoding="utf-8"))
    assert tests["status"] == "PASS"
    for name, digest in tests["files"].items():
        assert sha(ROOT / name) == digest, name
    with (work / "submission_claim.json").open("x", encoding="utf-8") as stream:
        json.dump({"description": case["description"], "identity": ident,
                   "policy": "one POST; reconcile ambiguity; no automatic retry"}, stream, indent=2)
    command = [sys.executable, "scripts/submit_code_file_once.py", "--competition", COMP,
               "--kernel", case["kernel"], "--version", str(ident["version"]),
               "--file-name", "submission.csv", "--description", case["description"],
               "--source-file", str(work / "remote_source.ipynb"),
               "--source-sha256", ident["source_sha256"]]
    try:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired as exc:
        (work / "guarded_submit.log").write_text(str(exc) + "\nAMBIGUOUS: reconcile, never retry\n", encoding="utf-8")
        readback(api, case, work)
        raise RuntimeError("Ambiguous guarded helper timeout; read full API receipt; never retry automatically") from exc
    (work / "guarded_submit.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    record = readback(api, case, work)
    assert result.returncode == 0 and len(record["matches"]) == 1 and not record["anomalies"], result.stdout + result.stderr
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment", choices=CASES)
    parser.add_argument("action", choices=("identity", "status", "audit", "submit", "readback"))
    args = parser.parse_args()
    case = {**CASES[args.experiment], "experiment": args.experiment}
    work = ROOT / f"work/exp{args.experiment}_20260924"
    api = api_client()
    if args.action == "identity":
        result = identity(api, case, work)
    elif args.action == "status":
        result = status(api, case)
    elif args.action == "audit":
        result = audit(api, case, work)
    elif args.action == "submit":
        result = submit(api, case, work)
    else:
        result = readback(api, case, work)
    print(json.dumps(result, default=str))


if __name__ == "__main__":
    main()
