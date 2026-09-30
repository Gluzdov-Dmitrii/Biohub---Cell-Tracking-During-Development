"""Freeze repaired graph and rerun both budgets, reusing verified neural caches."""
import hashlib,json
from pathlib import Path
from monitor_exp213_job import ssh
L=Path(__file__).resolve().parents[1]
R='/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'
def save(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def main():
    pair=(L/'scripts/run_exp214_paired_fold.py').read_text()
    pair=pair.replace('    a=p.parse_args();',"    p.add_argument('--reuse-manifest',type=Path)\n    a=p.parse_args();")
    start=pair.index('    subprocess.check_call(');end=pair.index('    subprocess.check_call(',start+5)
    original=pair[start:end]
    replacement="""    if a.reuse_manifest:
        reuse=json.loads(a.reuse_manifest.read_text());public=Path(reuse['public'])
        for name,digest in reuse['files'].items():
            assert hashlib.sha256((public/name).read_bytes()).hexdigest()==digest,name
        receipt=json.loads((public/'inference_receipt.json').read_text())
        assert receipt['target_labels_read'] is False
        assert receipt['bundle']==json.loads(a.bundle.read_text())
        assert receipt['movies']==json.loads(a.movies.read_text())
        (a.output/'public').symlink_to(public,target_is_directory=True)
    else:
"""+''.join('    '+line+'\n' for line in original.rstrip().splitlines())
    pair=pair[:start]+replacement+pair[end:]
    remote='''import hashlib,json,shutil
from pathlib import Path
r=Path(ROOT);code=r/'code/exp214_inference_v8_20260914';inp=r/'code/exp214_gapfix_inputs_20260914'
assert not code.exists() and not inp.exists()
shutil.copytree(r/'code/exp214_inference_v7_20260912',code,symlinks=True);inp.mkdir()
p=code/'evaluate_synthetic_gap_deepcenter.py';s=p.read_text()
old='if node not in used_middle]'
assert s.count(old)==1
p.write_text(s.replace(old,'if node not in used_middle and node not in incoming and node not in outgoing]'))
(code/'run_exp214_paired_fold.py').write_text(PAIR)
m=json.loads((code/'code_manifest.json').read_text())
for name in m:m[name]=hashlib.sha256((code/name).read_bytes()).hexdigest()
(code/'code_manifest.json').write_text(json.dumps(m,indent=2))
reuse={}
for budget,prefix,date in [('base60','strong60','20260912'),('new90','eval90','20260913')]:
 for fold,n in [('44b6',5),('6bba',3)]:
  for i in range(n):
   tag=f'{budget}_{fold}_{i:02}';pub=r/f'runs/exp214_{prefix}_paired_{fold}_{i:02}_{date}/output/public'
   receipt=pub/'inference_receipt.json'
   if not receipt.exists():continue
   d=json.loads(receipt.read_text());assert d['status']=='PASS_FROZEN_PUBLIC_FAMILY_INFERENCE'
   assert hashlib.sha256((pub/'submission.csv').read_bytes()).hexdigest()==d['submission_sha256']
   files=['inference_receipt.json','submission.csv']+[f'candidates/{name}.npz' for name in d['movies']]
   row={'public':str(pub),'files':{n:hashlib.sha256((pub/n).read_bytes()).hexdigest() for n in files}}
   dst=inp/(tag+'_reuse.json');dst.write_text(json.dumps(row,indent=2));reuse[tag]=str(dst)
print(json.dumps({'code_manifest':m,'reuse':reuse}))
'''.replace('ROOT',repr(R)).replace('PAIR',repr(pair))
    staging=L/'reports/exp214_gapfix_staging_20260914.json'
    if staging.exists():
        result=json.loads(staging.read_text())
    else:
        result=ssh('nsu-quadro','python3 -',remote);save(staging,result)
    for budget,prefix,date in [('base60','strong60','20260912'),('new90','eval90','20260913')]:
        manifest=json.loads((L/('reports/exp214_'+prefix+'_'+('score175_manifest_20260912.json' if budget=='base60' else 'manifest_20260913.json'))).read_text())
        for fold,n in [('44b6',5),('6bba',3)]:
            for i in range(n):
                tag=f'{budget}_{fold}_{i:02}'
                c=json.loads((L/f'reports/exp214_{prefix}_paired_{fold}_{i:02}_config_{date}.json').read_text())
                c.update(code=R+'/code/exp214_inference_v8_20260914',run=R+f'/runs/exp214_gapfix_paired_{tag}_20260914',lease_id='biohub-exp214-gapfix-'+tag,token='exp214-gapfix-'+tag,scope='Matched60/60 versus90/60 with identical corrected gap endpoint occupancy; no metric tuning/POST')
                c['arguments'][c['arguments'].index('--output')+1]=c['run']+'/output'
                if tag in result['reuse']:c['arguments']+=['--reuse-manifest',result['reuse'][tag]]
                save(L/f'reports/exp214_gapfix_paired_{tag}_config_20260914.json',c)
        for arm in manifest['arms'].values():
            for part in arm:
                for k in ('csv','receipt'):part[k]=part[k].replace(f'/runs/exp214_{prefix}_paired_',f'/runs/exp214_gapfix_paired_{budget}_').replace('_'+date+'/', '_20260914/')
        manifest['scope']='Gap endpoint occupancy correction applied equally to both budgets; unchanged weights and target cohort.'
        save(L/f'reports/exp214_gapfix_{budget}_manifest_20260914.json',manifest)
        ssh('nsu-quadro','python3 -',"import json\nfrom pathlib import Path\nPath("+repr(R+f'/code/exp214_gapfix_inputs_20260914/{budget}_manifest.json')+").write_text(json.dumps("+repr(manifest)+",indent=2))\nprint('{}')")
    s=(L/'scripts/finish_exp214_eval90_predictions.py').read_text()
    s=s.replace('exp214_eval90','exp214_gapfix').replace('_20260913','_20260914').replace('EVAL90','GAPFIX').replace('exp214_inference_v7_20260912','exp214_inference_v8_20260914')
    s=s.replace("LANES = [[f'44b6_{i:02}' for i in range(5)], [f'6bba_{i:02}' for i in range(3)]]","LANES = [[f'{budget}_44b6_{i:02}' for budget in ('new90','base60') for i in range(5)], [f'{budget}_6bba_{i:02}' for budget in ('new90','base60') for i in range(3)]]")
    s='\n'.join(line for line in s.splitlines() if "['status']=='PASS_FROZEN_90_60_MODELS'" not in line)+'\n'
    s=s.replace('datetime.datetime(2026, 9, 13, 23, 30','datetime.datetime(2026, 9, 14, 17, 30').replace('len(completed) == 8','len(completed) == 16')
    with (L/'scripts/finish_exp214_gapfix_predictions.py').open('x') as f:f.write(s)
    print(json.dumps({'reused_public_shards':len(result['reuse']),'total_shards':16,'code_manifest_sha256':hashlib.sha256(json.dumps(result['code_manifest'],sort_keys=True).encode()).hexdigest()}))
if __name__=='__main__':main()
