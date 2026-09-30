"""Score one sealed EXP234 source fold after verified A100 lease release."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

from monitor_exp213_job import ssh


ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"


def released_success(state):
    return (state.get("monitor_status") == "RELEASED_AFTER_VERIFIED_EXIT"
            and state.get("queue", {}).get("state") == "RELEASED"
            and state.get("exit", {}).get("returncode") == 0
            and state.get("exit", {}).get("hard_timeout") is False
            and state.get("identity_alive") is False
            and state.get("group_alive") is False
            and state.get("gpu_pids") == []
            and isinstance(state.get("status"), dict)
            and state["status"].get("status") == "PASS_EXP234_SOURCE_ARMS_NO_LABELS")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source_embryo", choices=("44b6", "6bba"))
    args = parser.parse_args()
    embryo = args.source_embryo
    monitor_path = ROOT / f"reports/exp234_source_{embryo}_config_v2_20260926_monitor.json"
    monitor = json.loads(monitor_path.read_text())
    assert released_success(monitor), "Source worker/lease/arms are not verified complete"
    inference_config = json.loads((ROOT / f"reports/exp234_source_{embryo}_config_v2_20260926.json").read_text())
    assert monitor["launch"]["config"]["run"] == inference_config["run"]
    assert inference_config["lease_id"] == monitor["queue"]["id"]

    prepared = json.loads((ROOT / "reports/exp234_source_scorer_prepare_v3_20260926.json").read_text())
    assert prepared["status"] == "PREPARED_EXP234_SOURCE_SCORER"
    scorer = prepared["configs"][embryo]
    assert scorer["run"] == inference_config["run"]
    assert prepared["staging"]["code"] == REMOTE + "/code/exp234_source_scorer_v3_20260926"
    code = prepared["staging"]["code"]
    command = shlex.join([
        "env", "CUDA_VISIBLE_DEVICES=", "OMP_NUM_THREADS=4", "MKL_NUM_THREADS=4",
        REMOTE + "/envs/prepost/py3.11-stdlib-v1/bin/python",
        code + "/score_exp234_source_threshold.py", scorer["path"],
        "--config-sha256", scorer["sha256"]])
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "nsu-a100", command],
        text=True, capture_output=True, timeout=1800)
    log = ROOT / f"reports/exp234_source_{embryo}_score_v3_20260926.log"
    log.write_text(result.stdout + "\n--- stderr ---\n" + result.stderr)
    if result.returncode:
        raise RuntimeError(f"EXP234 source {embryo} scorer failed {result.returncode}; see {log}")

    source = '''import hashlib,json,pathlib
r=pathlib.Path(RUN);code=pathlib.Path(CODE)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(code/'code_manifest.json')==MANIFEST_SHA
assert sha(code/CONFIG_NAME)==CONFIG_SHA
gate=r/'score/no_metric_gate.json';result=r/'score/result.json'
g=json.loads(gate.read_text());x=json.loads(result.read_text())
assert g['status']=='PASS_ALL_EXP234_SOURCE_ARMS_BEFORE_LABEL_ACCESS'
assert x['status']=='PASS_EXP234_SOURCE_THRESHOLD_SELECTED'
assert x['source_embryo']==EMBRYO and x['no_metric_gate_sha256']==sha(gate)
assert len(x['movies'])==(8 if EMBRYO=='44b6' else 11)
print(json.dumps({'status':'VERIFIED_EXP234_SOURCE_SELECTION','source_embryo':EMBRYO,
 'selected_threshold':x['selected_threshold'],
 'scores':{t:x['summary'][t]['score'] for t in ('0.900','0.940','0.965')},
 'result_sha256':sha(result),'gate_sha256':sha(gate),'config_sha256':CONFIG_SHA,
 'inference_run':str(r)}))
'''.replace("RUN", repr(scorer["run"])).replace("CODE", repr(code)).replace(
        "MANIFEST_SHA", repr(prepared["staging"]["manifest_sha256"])).replace(
        "CONFIG_NAME", repr(embryo + "_score_config.json")).replace(
        "CONFIG_SHA", repr(scorer["sha256"])).replace("EMBRYO", repr(embryo))
    verified = ssh("nsu-a100", "python3 -", source)
    receipt = {**verified, "monitor_receipt_sha256": hashlib.sha256(monitor_path.read_bytes()).hexdigest(),
               "scorer_log": str(log)}
    path = ROOT / f"reports/exp234_source_{embryo}_score_v3_20260926.json"
    path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
