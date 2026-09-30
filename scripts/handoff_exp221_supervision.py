"""One-time verified handoff of the two owned Windows monitors to remote control."""
import json
from pathlib import Path
import subprocess
from monitor_exp213_job import ssh
from stage_exp221_supervision import CODE


def main():
    source='''import json,time
from pathlib import Path
s=Path(CODE)/'state'
ready=json.loads((s/'control_ready.json').read_text()); assert ready['queue_read_pass']
obs=json.loads((s/'observations.json').read_text()); assert 0<=time.time()-obs['checked_at']<120
assert set(obs['jobs'])=={'exp221-control-44b6-s2026-20260921','exp221-domain-44b6-s2026-20260921'}
assert all(v['identity_alive'] and v['gpu_pids'] for v in obs['jobs'].values())
claim=json.loads((s/'control_claim.json').read_text()); assert Path('/proc',str(claim['pid']),'stat').read_text().split()[21]==claim['start_identity']
assert not (s/'activate.json').exists()
print(json.dumps({'ready':ready,'observer_checked_at':obs['checked_at'],'controller':claim}))
'''.replace('CODE',repr(CODE))
    preflight=ssh('nsu-quadro','python3 -',source)
    ps="""$biohubRecords = @()
foreach ($biohubPair in @(@(10868, 'control'), @(29248, 'domain'))) {
 $biohubMonitor = Get-CimInstance Win32_Process -Filter ('ProcessId = ' + $biohubPair[0])
 if (-not $biohubMonitor) { throw 'Expected owned monitor missing: reconcile before handoff' }
 if ($biohubMonitor.CommandLine -notlike '*monitor_exp213_job.py*' -or $biohubMonitor.CommandLine -notlike ('*exp221_' + $biohubPair[1] + '_44b6_s2026_20260921_config.json*')) { throw 'Monitor identity mismatch' }
 $biohubRecords += @{pid=$biohubMonitor.ProcessId; command=$biohubMonitor.CommandLine}
}
foreach ($biohubRecord in $biohubRecords) { Stop-Process -Id $biohubRecord.pid -ErrorAction Stop }
$biohubRecords | ConvertTo-Json -Depth 3
"""
    stopped=json.loads(subprocess.check_output(['powershell','-NoProfile','-Command',ps],text=True))
    Path('reports/exp221_monitor_handoff_local_stop_20260921.json').write_text(json.dumps({'preflight':preflight,'stopped':stopped},indent=2)+'\n')
    source='''import json,time
from pathlib import Path
s=Path(CODE)/'state'
with (s/'activate.json').open('x') as f: json.dump({'at':time.time(),'local_monitor_pids_stopped':[10868,29248]},f)
print(json.dumps({'status':'REMOTE_CONTROL_ACTIVATED','path':str(s/'activate.json')}))
'''.replace('CODE',repr(CODE))
    print(json.dumps(ssh('nsu-quadro','python3 -',source)))


if __name__=='__main__':main()
