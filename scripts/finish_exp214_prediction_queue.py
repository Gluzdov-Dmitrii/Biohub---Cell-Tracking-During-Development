"""Finish a finite, frozen set of authorized EXP214 inference jobs; never POST."""
import hashlib,json,subprocess,sys,time,traceback
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/exp214_prediction_queue_progress_20260912.json'
LANES=[
    ['paired_6bba_01','paired_6bba_02','control_full12','control_reduced12','control_reduced60'],
    ['paired_44b6_01','paired_44b6_02','paired_44b6_03','paired_44b6_04'],
]

def save(status,**fields):
    value={'status':status,'updated':time.time(),**fields}
    temp=REPORT.with_suffix('.json.partial');temp.write_text(json.dumps(value,indent=2)+'\n');temp.replace(REPORT)
    print(json.dumps(value),flush=True)

def main():
    claim=ROOT/'reports/exp214_prediction_queue_claim_20260912.json'
    with claim.open('x') as f:json.dump({'started':time.time(),'lanes':LANES,'scope':'Only these seven pending inference jobs; no training, scoring, model changes, kernel pushes or submissions'},f,indent=2)
    configs={}
    for lane in LANES:
        for name in lane:
            path=ROOT/'reports'/('exp214_'+name+'_config_20260912.json');c=json.loads(path.read_text())
            assert c['experiment']=='EXP214' and c['code'].endswith('/exp214_inference_v6_20260912')
            assert c['run'].endswith('/exp214_'+name+'_20260912') and c['resources']['gpus']==1
            assert c['script']==('run_exp214_paired_fold.py' if name.startswith('paired_') else 'run_exp214_public_fold.py')
            configs[name]=(path,c)
    config_hashes={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,(path,c) in configs.items()}
    deadline=time.monotonic()+8*3600
    while time.monotonic()<deadline:
        proc=subprocess.run([sys.executable,'scripts/snapshot_exp214_progress.py'],cwd=ROOT,capture_output=True,text=True,timeout=90)
        if proc.returncode:raise RuntimeError('Operational snapshot failed; reconcile before resuming: '+proc.stderr[-1200:])
        snapshot=json.loads((ROOT/'reports/exp214_progress_snapshot_20260912.json').read_text())
        rows={r['run']:r for r in snapshot['runs']};active=snapshot['queue'];done=[];waiting=[];started=[]
        for lane in LANES:
            for name in lane:
                path,c=configs[name];row=rows.get('exp214_'+name+'_20260912')
                if row:
                    if 'exit' in row and row['exit']['returncode']!=0:raise RuntimeError('Inference failed: '+name)
                    if 'exit' in row:
                        assert row['public_receipt'] and (row['local_receipt'] or name.startswith('control_')),name
                        monitor_path=Path(str(path).replace('_config_','_monitor_'))
                        try:monitor=json.loads(monitor_path.read_text())
                        except (FileNotFoundError,json.JSONDecodeError):monitor={}
                        if monitor.get('monitor_status')=='RELEASED_AFTER_VERIFIED_EXIT':
                            assert monitor['queue']['id']==c['lease_id'] and monitor['queue']['state']=='RELEASED'
                            done.append(name);continue
                    waiting.append(name);break
                own=[q for q in active if q['project']=='biohub-cell-tracking-during-development' and q['state'] in ('RUNNING','RESERVED')]
                others_waiting=[q for q in active if q['project']!='biohub-cell-tracking-during-development' and q['state'].startswith('WAITING')]
                if len(own)>=2 or (own and others_waiting):waiting.append(name);break
                assert hashlib.sha256(path.read_bytes()).hexdigest()==config_hashes[name],'Frozen configuration changed: '+name
                launched=subprocess.run([sys.executable,'scripts/launch_exp214_job.py','--config',str(path.relative_to(ROOT)),'--mode','inference'],cwd=ROOT,capture_output=True,text=True,timeout=120)
                log=ROOT/'reports'/('exp214_'+name+'_finite_queue_launch_20260912.log');log.write_text(launched.stdout+'\n'+launched.stderr)
                if launched.returncode:raise RuntimeError('Launch did not complete: '+name+'; inspect '+str(log)+' and reconcile any reserved lease, never duplicate')
                result=json.loads(launched.stdout);active.append(result['lease']);started.append(name);break
        if len(done)==sum(map(len,LANES)):
            save('COMPLETE_ALL_FROZEN_PREDICTIONS',completed=done);return
        current=[{'run':r['run'],'candidate_movies':r['candidate_movies'],'public_receipt':r['public_receipt'],'local_receipt':r['local_receipt']} for r in snapshot['runs'] if r['run'] in {'exp214_'+n+'_20260912' for lane in LANES for n in lane}]
        save('RUNNING_FROZEN_PREDICTION_QUEUE',completed=done,waiting_or_running=waiting,launched=started,current=current)
        time.sleep(45)
    raise TimeoutError('Finite eight-hour prediction queue budget reached; existing jobs retain their independent monitors')

if __name__=='__main__':
    try:main()
    except Exception as e:
        save('STOPPED_NEEDS_RECONCILIATION',error=str(e));traceback.print_exc();raise
