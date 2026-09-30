"""Source8 single-job remote supervision plus gated post-release CPU scoring."""
import json
from pathlib import Path
import subprocess
from monitor_exp213_job import ssh
from prepare_exp221_source_graph import ROOT,CODE,RUN

SUP=ROOT+'/code/exp221_source_supervision_v1_20260921'
LEASE='exp221-source-graph8-20260921'


def main():
    cfg=json.loads(Path('reports/exp221_source_graph8_20260921_config.json').read_text())
    script=Path('scripts/exp221_remote_supervisor.py').read_text()
    script=script.replace("['control','domain']","['control']")
    script=script.replace("{'exp221-control-44b6-s2026-20260921','exp221-domain-44b6-s2026-20260921'}",repr({LEASE}))
    script=script.replace('len(released)==2','len(released)==1')
    trigger='''                    prediction=json.loads((Path(RUN)/'output/status.json').read_text())
                    assert prediction['status']=='PASS_BOTH_SOURCE8_PREDICTIONS_NO_METRICS'
                    with (state/'score_claim.json').open('x') as f: json.dump({'at':time.time()},f)
                    command=['taskset','-c','0-3',ROOT+'/envs/prepost/py3.11-stdlib-v1/bin/python',CODE+'/score_exp221_source_graph.py','--repo',ROOT+'/code/exp214_honest_refit_v4_20260912/tracking_repo','--data',ROOT+'/data/exp213_source_view_20260912','--manifest',CODE+'/score_manifest.json','--output',RUN+'/score']
                    with (state/'scoring.log').open('w') as f:
                        result=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,timeout=900,env=dict(os.environ,OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',CUDA_VISIBLE_DEVICES=''))
                    atomic(state/'score_exit.json',{'returncode':result.returncode,'at':time.time()})
                    assert result.returncode==0
'''.replace('ROOT',repr(ROOT)).replace('CODE',repr(CODE)).replace('RUN',repr(RUN))
    script=script.replace("                    atomic(state/'complete.json'",trigger+"                    atomic(state/'complete.json'")
    files={'exp221_remote_supervisor.py':script,'monitor_exp213_job.py':Path('scripts/monitor_exp213_job.py').read_text(),'control.json':json.dumps(cfg)}
    src='''import json,subprocess
from pathlib import Path
p=Path(SUP);p.mkdir(exist_ok=False);(p/'state').mkdir()
for name,data in FILES.items(): (p/name).write_text(data)
print(json.dumps({'staged':str(p)}))
'''.replace('SUP',repr(SUP)).replace('FILES',repr(files))
    receipt={'stage':ssh('nsu-quadro','python3 -',src)}
    for mode,host in [('observe','nsu-a100'),('control','nsu-quadro')]:
        src='''import json,subprocess
from pathlib import Path
p=Path(SUP);s=p/'state'
with (s/(MODE+'.log')).open('w') as f: child=subprocess.Popen(['python3',str(p/'exp221_remote_supervisor.py'),MODE],stdout=f,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
print(json.dumps({'mode':MODE,'pid':child.pid}))
'''.replace('SUP',repr(SUP)).replace('MODE',repr(mode))
        receipt[mode]=ssh(host,'python3 -',src)
    Path('reports/exp221_source_supervision_launch_20260921.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))


if __name__=='__main__':main()
