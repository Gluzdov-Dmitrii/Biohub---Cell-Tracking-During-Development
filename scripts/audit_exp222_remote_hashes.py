"""Read-only current remote byte hash audit; no inference or evaluation."""
import json
from pathlib import Path
from monitor_exp213_job import ssh

source = r'''
import datetime,hashlib,json,subprocess
from pathlib import Path
root=Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
run=root/'runs/exp222_classical_full175_20260921'
repo=root/'code/exp214_honest_refit_v4_20260912/tracking_repo'
def info(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(8*1024**2),b''):h.update(chunk)
 st=path.stat()
 return {'path':str(path),'sha256':h.hexdigest(),'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}
files=[run/'predictions.csv',run/'exp002_exact.py',run/'run_exp222_classical_pilot.py',run/'analyze_submission_edge_failure_modes.py',run/'result.json',run/'no_metric_gate.json',repo/'src/biohub_tracking/metrics.py',repo/'src/biohub_tracking/io.py',repo/'scripts/predict_unet_transformer.py']
hashed={str(p.relative_to(root)):info(p) for p in files}
metrics_tree={str(p.relative_to(repo)):info(p) for p in (repo/'src/biohub_tracking').rglob('*.py')}
result=json.loads((run/'result.json').read_text());gate=json.loads((run/'no_metric_gate.json').read_text())
checks={'prediction_sha_matches_result_and_gate':hashed[str((run/'predictions.csv').relative_to(root))]['sha256']==result['prediction_sha256']==gate['prediction_sha256'],'original_source_sha_matches_result':hashed[str((run/'exp002_exact.py').relative_to(root))]['sha256']==result['source_sha256'],'gate_sha_matches_result':hashed[str((run/'no_metric_gate.json').relative_to(root))]['sha256']==result['no_metric_gate_sha256']}
version_source="import importlib.metadata as m,json; names=['numpy','scipy','tracksdata','geff','polars','zarr','torch']; print(json.dumps({n:m.version(n) for n in names}))"
v=subprocess.run([str(root/'envs/prepost/py3.11-stdlib-v1/bin/python'),'-c',version_source],capture_output=True,text=True,timeout=15)
print(json.dumps({'status':'PASS_CURRENT_REMOTE_HASHES' if all(checks.values()) else 'FAIL_REMOTE_HASHES','checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'files':hashed,'biohub_python_tree':metrics_tree,'environment_versions':json.loads(v.stdout) if v.returncode==0 else {'error':v.stderr[-1000:]},'limitation':'Current hashes pin current deployed bytes, not independently timestamped execution-time byte identity. Prior exact175baseline behavioral reproduction remains historical evidence.'}))
'''
result=ssh('nsu-quadro','python3 -',source)
path=Path(__file__).resolve().parents[1]/'reports/exp222_remote_current_hash_audit_20260921.json'
path.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='biohub_python_tree'},indent=2))
assert result['status']=='PASS_CURRENT_REMOTE_HASHES'
