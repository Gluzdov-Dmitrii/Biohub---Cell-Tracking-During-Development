"""Stage finite scoring of both corrected budgets after all16 shards release."""
import json
from pathlib import Path
from monitor_exp213_job import ssh
L=Path(__file__).resolve().parents[1]
R='/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'
def main():
    s=(L/'scripts/finish_exp214_eval90_scoring.py').read_text().replace('exp214_eval90','exp214_gapfix').replace('_20260913','_20260914').replace('EVAL90','GAPFIX').replace('exp214_inference_v7_20260912','exp214_inference_v8_20260914')
    s=s.replace('datetime.datetime(2026, 9, 14, 0','datetime.datetime(2026, 9, 14, 18').replace("len(ready['shards']) == 8","len(ready['shards']) == 16")
    start=s.index('    commands = [');end=s.index('    for index, arguments',start)
    s=s[:start]+'''    commands = []
    for budget in ('base60','new90'):
        commands.append([CODE/'score_exp214_paired.py','--repo',ROOT/'code/exp214_honest_refit_v4_20260912/tracking_repo','--data',ROOT/'data/exp213_source_view_20260912','--manifest',INPUT/(budget+'_manifest.json'),'--output',out/budget])
    commands.append([INPUT/'compare_exp214_60_90.py','--metrics',out/'new90/metrics.json','--baseline',out/'base60/metrics.json','--output',out/'comparison.json'])
'''+s[end:]
    local=L/'scripts/finish_exp214_gapfix_scoring.py'
    with local.open('x') as f:f.write(s)
    template=(L/'scripts/stage_exp214_eval90_scoring.py').read_text()
    start=template.index("    remote='''")+len("    remote='''")
    end=template.index("'''.replace('ROOT'",start)
    remote=template[start:end].replace('exp214_eval90','exp214_gapfix').replace('_20260913','_20260914').replace('2026-09-14T00:00:00Z','2026-09-14T18:00:00Z')
    remote=remote.replace('ROOT',repr(R)).replace('SOURCE',repr(s)).replace('COMPARE',repr((L/'scripts/compare_exp214_60_90.py').read_text()))
    result=ssh('nsu-quadro','python3 -',remote)
    (L/'reports/exp214_gapfix_cpu_launch_20260914.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
