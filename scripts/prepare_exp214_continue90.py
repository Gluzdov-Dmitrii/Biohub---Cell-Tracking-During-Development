"""Prepare two bounded source-only 60->90 continuations; never launch or POST."""
import hashlib
import json
from pathlib import Path
from monitor_exp213_job import ssh

ROOT = Path(__file__).resolve().parents[1]
REMOTE = '/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'

def main():
    base = json.loads((ROOT/'reports/exp214_strong60_plan_20260912.json').read_text())
    base['detector']['epochs'] = 90
    base['detector']['seeds'] = [2026]
    base['status'] = 'PREREGISTERED_USER_AUTHORIZED_CONTINUE90_SOURCE_ONLY'
    base.pop('strong60_extension', None)
    base['scope_limits'] = 'User requested longer A100 training on 2026-09-13. Fixed90 total epochs, one seed per embryo fold. Development-adapted comparison, not pristine holdout. No POST. No automatic continuation beyond90.'
    base['no_metric_gate'] = 'Select checkpoint by unchanged source validation only; freeze both models and a complete paired target cohort before target metrics. No intermediate target score selection.'
    base['continuation'] = {'initial_epoch':60, 'total_epochs':90, 'seeds':[2026], 'max_gpu_hours_estimate':4, 'reason':'Test additional optimization after source6bba seed2026 best checkpoint occurred at epoch53; improvement not guaranteed.'}
    source = '''import hashlib,json,shutil
from pathlib import Path
r=Path(REMOTE)
fold=FOLD
parent=r/PARENT
status=json.loads((parent/'status.json').read_text())
assert status['status']=='COMPLETE_SOURCE_REFIT' and status['epoch']==60
assert hashlib.sha256((parent/'checkpoint_last.pth').read_bytes()).hexdigest()==status['checkpoint_sha256']
assert hashlib.sha256((parent/'edge_predictor_best.pth').read_bytes()).hexdigest()==status['best_sha256']
assert status['contract']['fold']==fold and status['contract']['seed']==2026
plan=PLAN
plan['warm_start_plan_sha256']=status['contract']['plan_sha256']
plan['continuation']['parent_checkpoint_sha256']=status['checkpoint_sha256']
plan['continuation']['parent_best_sha256']=status['best_sha256']
code=r/('code/exp214_continue90_'+fold+'_20260913')
assert not code.exists(), 'Existing staged code; reconcile instead of overwrite'
shutil.copytree(r/'code/exp214_strong60_v1_20260912',code,symlinks=True)
trainer=code/'train_exp213_detector.py'
text=trainer.read_text()
old="parent_status['epoch']==12"
assert text.count(old)==1
trainer.write_text(text.replace(old,"parent_status['epoch']==60"))
(code/'plan.json').write_text(json.dumps(plan,indent=2)+'\\n')
manifest=json.loads((code/'code_manifest.json').read_text())
for name in manifest:
 manifest[name]=hashlib.sha256((code/name).read_bytes()).hexdigest()
(code/'code_manifest.json').write_text(json.dumps(manifest,indent=2)+'\\n')
print(json.dumps({'plan':plan,'manifest':manifest,'code':str(code),'warm_start':str(parent/'checkpoint_last.pth')}))
'''
    parents = {'44b6':'runs/exp214_equal_time44b6_s2026_20260912/output', '6bba':'runs/exp214_strong60_6bba_s2026_p01_20260912/output'}
    for index,(fold,parent) in enumerate(parents.items()):
        script=source.replace('REMOTE',repr(REMOTE)).replace('FOLD',repr(fold)).replace('PARENT',repr(parent)).replace('PLAN',repr(base))
        staged=ssh('nsu-a100','python3 -',script)
        name=f'exp214_continue90_{fold}_s2026_20260913'
        (ROOT/f'reports/{name}_staging.json').write_text(json.dumps(staged,indent=2)+'\n')
        config=json.loads((ROOT/'reports/exp214_strong60_6bba_s2026_p02_config_20260912.json').read_text())
        config.pop('resume_output',None)
        config.update(lease_id=name.replace('_','-'),token=name,code=staged['code'],run=REMOTE+'/runs/'+name,fold=fold,seed=2026,max_seconds=10800,lease_minutes=240,warm_start=staged['warm_start'],scope=base['scope_limits'],retention='Preserve source-selected and optimizer states for paired comparison; no deletion without review')
        config['gpu']=['GPU-61c0078d-a4a6-37a2-3aba-0378e7794c46','GPU-04efb7bd-1f45-38cd-4a13-c79b6aeaa002'][index]
        config['cpu_affinity']='0-7' if index==0 else '8-15'
        path=ROOT/f'reports/exp214_continue90_{fold}_s2026_config_20260913.json'
        assert not path.exists()
        path.write_text(json.dumps(config,indent=2)+'\n')
        print(json.dumps({'config':str(path),'plan_sha256':staged['manifest']['plan.json']}))

if __name__=='__main__':
    main()
