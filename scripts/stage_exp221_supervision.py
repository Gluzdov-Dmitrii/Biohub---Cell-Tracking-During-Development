"""Stage and start dormant finite remote observers for the two current jobs."""
import base64
import json
from pathlib import Path
from monitor_exp213_job import ssh

ROOT='/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'
CODE=ROOT+'/code/exp221_supervision_v1_20260921'


def main():
    files={n:base64.b64encode(Path('scripts',n).read_bytes()).decode() for n in ['exp221_remote_supervisor.py','monitor_exp213_job.py']}
    for arm in ['control','domain']:
        files[arm+'.json']=base64.b64encode(Path(f'reports/exp221_{arm}_44b6_s2026_20260921_config.json').read_bytes()).decode()
    src='''import base64,json,hashlib
from pathlib import Path
p=Path(CODE);p.mkdir(exist_ok=True)
manifest={}
for name,data in FILES.items():
 b=base64.b64decode(data); dest=p/name
 if dest.exists(): assert dest.read_bytes()==b
 else: dest.write_bytes(b)
 manifest[name]=hashlib.sha256(b).hexdigest()
print(json.dumps({'code':str(p),'manifest':manifest}))
'''.replace('CODE',repr(CODE)).replace('FILES',repr(files))
    receipt={'stage':ssh('nsu-quadro','python3 -',src)}
    for mode,alias in [('observe','nsu-a100'),('control','nsu-quadro')]:
        src='''import subprocess,json
from pathlib import Path
p=Path(CODE);s=p/'state';s.mkdir(exist_ok=True)
assert not (s/(MODE+'_launch.json')).exists(), 'Never duplicate a launched supervisor'
with (s/(MODE+'.log')).open('w') as f:
 child=subprocess.Popen(['python3',str(p/'exp221_remote_supervisor.py'),MODE],stdout=f,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
result={'pid':child.pid,'mode':MODE}
(s/(MODE+'_launch.json')).write_text(json.dumps(result))
print(json.dumps(result))
'''.replace('CODE',repr(CODE)).replace('MODE',repr(mode))
        receipt[mode]=ssh(alias,'python3 -',src)
    Path('reports/exp221_remote_supervision_launch_20260921.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__': main()
