"""Independent read-only postcompletion check for EXP240's label-free CPU screen."""

import argparse
import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh
from stage_exp240_source_two_peak_chain import (
    BUNDLE, CODE, MANIFEST, RECEIPT as STAGE_RECEIPT, ROOT, RUN,
    exclusive_json, local_gate, sha,
)
from launch_exp240_source_two_peak_chain import (
    PYTHON, RECEIPT as LAUNCH_RECEIPT, command,
)

if not __debug__:
    raise RuntimeError('EXP240 verifier requires assertions; PYTHONOPTIMIZE must be 0')

OUT = ROOT / 'reports/exp240_source_two_peak_chain_verified_20260927.json'


def recount(rows: list[dict], ids: list[str]) -> tuple[list[dict], str]:
    assert len(rows) == len(ids) == 19
    assert [r['dataset'] for r in rows] == ids
    summaries = []
    for cohort, n in (('source44', 8), ('source6', 11)):
        group = [r for r in rows if r['cohort'] == cohort]
        assert len(group) == n
        total = {'cohort': cohort, 'movies': n}
        for key in ('original_nodes', 'original_edges', 'seed_count', 'peak_count',
                    'offgraph_peak_count', 'legal_pair_count', 'distinct_legal_seed_count',
                    'selected_conflict_free_chain_count'):
            assert all(isinstance(row[key], int) and row[key] >= 0 for row in group)
            total[key] = sum(row[key] for row in group)
        assert all(row['selected_conflict_free_chain_count'] <= row['distinct_legal_seed_count'] <=
                   row['legal_pair_count'] and row['distinct_legal_seed_count'] <= row['seed_count']
                   and row['offgraph_peak_count'] <= row['peak_count'] for row in group)
        total['feasibility_gate'] = (total['distinct_legal_seed_count'] >= 10 and
                                     total['selected_conflict_free_chain_count'] >= 10)
        summaries.append(total)
    decision = ('PERMIT_ONE_FIXED_SOURCE_CANDIDATE_WITH_SEPARATE_SCORE_PREREG'
                if all(c['feasibility_gate'] for c in summaries)
                else 'REJECT_ADDITIVE_FREE_TERMINUS_REPAIR_BEFORE_SOURCE_SCORING')
    return summaries, decision


def remote_source(manifest_sha: str, launch: dict) -> str:
    source = r'''import csv,hashlib,json,math,os,pathlib,sys
import numpy as np
from scipy.spatial import cKDTree
if not __debug__:raise RuntimeError('EXP240 verifier requires assertions')
root=pathlib.Path(@@ROOT@@);code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
data=root/'data';sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert os.environ.get('PYTHONOPTIMIZE')=='0'
assert os.uname().nodename=='prepost'
def deny(event,args):
 if event not in ('open','os.listdir','os.scandir') or not args:return
 raw=args[0]
 if not isinstance(raw,(str,bytes,os.PathLike)):return
 path=pathlib.Path(os.fsdecode(raw)).resolve()
 if path.is_relative_to(data) or any(part.lower().endswith('.geff') for part in path.parts):
  raise PermissionError('EXP240 verifier denies all image, GEFF and label data')
sys.addaudithook(deny)
assert code.is_dir() and run.is_dir()
assert sha(code/'manifest.json')==@@MANIFEST@@
manifest=json.loads((code/'manifest.json').read_text())
assert manifest['status']=='SEALED_EXP240_LABEL_FREE_CPU_BUNDLE'
observed={p.relative_to(code).as_posix():sha(p) for p in code.rglob('*') if p.is_file()}
assert observed=={**manifest['files'],'manifest.json':@@MANIFEST@@}
cfg=json.loads((code/'config.json').read_text())
assert cfg['status']=='PREREGISTERED_EXP240_SOURCE19_LABEL_FREE'
assert cfg['output']==str(run/'output') and cfg['floor']==0.075 and cfg['radius_um']==7.0
assert cfg['scale_zyx_um']==[1.625,0.40625,0.40625] and cfg['downsample_zyx']==[1,4,4]
assert cfg['source_only'] and not any(cfg[k] for k in ('labels_read','target_data_opened',
 'graph_created','gpu_used','metrics_computed','kaggle_post'))
ids=[n for c in cfg['cohorts'] for n in c['ids']]
assert len(ids)==len(set(ids))==19
assert [len(c['ids']) for c in cfg['cohorts']]==[8,11]
assert [c['cohort'] for c in cfg['cohorts']]==['source44','source6']
first=cfg['cohorts'][0]
guarded_path=code/'verification/source44_guarded_recheck.json'
correction_path=code/'verification/source44_optimization_correction.json'
assert sha(guarded_path)==first['guarded_recheck_receipt_sha256']
assert sha(correction_path)==first['optimization_correction_receipt_sha256']
guarded=json.loads(guarded_path.read_text());correction=json.loads(correction_path.read_text())
assert guarded['status']=='PASS_EXP238_SOURCE_PEAK_CACHE_GUARDED_RECHECK_NO_LABELS'
assert guarded['original_receipt_sha256']==first['independent_receipt_sha256']
assert guarded['identical_receipt_payload'] and guarded['identical_remote']
assert correction['status']=='CORRECTED_EXP238_SOURCE44_VERIFIER_OPTIMIZATION_GUARD'
assert correction['original_receipt_sha256']==first['independent_receipt_sha256']
assert correction['guarded_recheck_receipt_sha256']==first['guarded_recheck_receipt_sha256']
assert correction['original_receipt_preserved'] is True
remote_launch=json.loads((run/'launch.json').read_text())
assert remote_launch==@@LAUNCH@@
assert remote_launch['status']=='LAUNCHED_EXP240_LABEL_FREE_SOURCE19_CPU_SCREEN'
assert remote_launch['manifest_sha256']==@@MANIFEST@@
assert remote_launch['code']==str(code) and remote_launch['run']==str(run)
assert remote_launch['command']==@@COMMAND@@
assert remote_launch['pythonoptimize']=='0' and remote_launch['cuda_visible_devices']==''
assert not any(remote_launch[k] for k in ('source_labels_read','target_data_opened',
 'graph_created','gpu_used','kaggle_post'))
assert sha(run/'cpu_wrapper.py')==remote_launch['wrapper_sha256']
wrapper=(run/'cpu_wrapper.py').read_text()
assert "PYTHONOPTIMIZE='0'" in wrapper and 'if not __debug__' in wrapper
exit_record=json.loads((run/'exit.json').read_text())
assert exit_record['returncode']==0 and exit_record['timeout'] is False
assert exit_record['error'] is None and exit_record['pythonoptimize']=='0'
assert not any(exit_record[k] for k in ('source_labels_read','target_data_opened',
 'graph_created','gpu_used','kaggle_post'))
child=json.loads((run/'child.json').read_text())
assert child['command']==@@COMMAND@@ and child['pythonoptimize']=='0'
assert child['cuda_visible_devices']=='' and child['ram_bytes']==16*1024**3
assert child['cpu_affinity']==[24,25,26,27]
assert exit_record['pid']==child['pid'] and exit_record['start']==child['start']
def proc(pid):
 try:fields=pathlib.Path(f'/proc/{pid}/stat').read_text().split(') ')[1].split()
 except FileNotFoundError:return None
 return fields[0],fields[19]
wrapper_proc=proc(remote_launch['wrapper_pid'])
assert wrapper_proc is None or wrapper_proc[0]=='Z'
child_proc=proc(child['pid'])
assert child_proc is None or child_proc[0]=='Z' or child_proc[1]!=child['start']
output=run/'output'
assert {p.name for p in output.iterdir()}=={'no_label_gate.json','result.json'}
gate_path=output/'no_label_gate.json';result_path=output/'result.json'
gate=json.loads(gate_path.read_text());result=json.loads(result_path.read_text())
assert gate['status']=='PASS_EXP240_SOURCE19_RECEIPT_AND_HASH_GATE_BEFORE_ENUMERATION'
assert gate['bundle_sha256']==@@MANIFEST@@ and gate['ids']==ids
assert gate['prereg_sha256']==cfg['prereg_sha256']
assert gate['exp238_verified_audit_sha256_pin_only']==cfg['exp238_verified_audit_sha256_pin_only']
assert not any(gate[k] for k in ('source_labels_read','target_data_opened','graph_created','gpu_used','kaggle_post'))
assert result['status']=='PASS_EXP240_LABEL_FREE_SOURCE_CHAIN_FEASIBILITY'
assert result['no_label_gate_sha256']==sha(gate_path)
assert gate_path.stat().st_mtime_ns<=result_path.stat().st_mtime_ns
assert result['prereg_sha256']==cfg['prereg_sha256']
assert not any(result[k] for k in ('source_labels_read','target_data_opened',
 'graph_created','metrics_computed','gpu_used','kaggle_post'))
rows=result['rows'];assert [r['dataset'] for r in rows]==ids
assert [r['cohort'] for r in rows]==['source44']*8+['source6']*11
scale=np.asarray(cfg['scale_zyx_um']);down=np.asarray(cfg['downsample_zyx'])
graph_hashes={};peak_hashes={}
for cohort in cfg['cohorts']:
 short=cohort['cohort'];cache=pathlib.Path(cohort['cache_run'])
 receipt_path=code/'verification'/(short+'.json')
 assert sha(receipt_path)==cohort['independent_receipt_sha256']
 receipt=json.loads(receipt_path.read_text())
 assert receipt['status']=='PASS_EXP238_SOURCE_PEAK_CACHE_INDEPENDENT_VERIFICATION'
 assert receipt['ordered_ids']==cohort['ids'] and receipt['cohort']==short
 assert receipt['exit0'] and receipt['released'] and receipt['all_graph_hashes_exact']
 assert receipt['source_only'] and receipt['labels_read'] is False
 assert receipt['queue_release']['state']=='RELEASED'
 assert sha(cache/'output/status.json')==cohort['status_sha256']
 status=json.loads((cache/'output/status.json').read_text())
 assert status['status']=='PASS_EXP238_SOURCE_PEAK_CACHE_NO_LABELS'
 assert status['source_labels_read'] is False and status['target_data_opened'] is False
 assert [r['dataset'] for r in status['records']]==cohort['ids']
 assert [r['dataset'] for r in receipt['remote']['rows']]==cohort['ids']
 for key,path in (('exit_sha256',cache/'exit.json'),
  ('complete_sha256',cache/'supervision/complete.json'),
  ('control_sha256',cache/'supervision/control.json')):
  assert sha(path)==cohort[key]
 for record,verified in zip(status['records'],receipt['remote']['rows']):
  name=record['dataset'];assert verified['dataset']==name
  graph=cache/'output'/('graph__'+name+'.csv')
  peak=cache/'output'/('peaks__'+name+'.npy')
  metadata=peak.with_suffix('.json')
  assert sha(graph)==record['graph_csv_sha256']==verified['graph_csv_sha256']
  assert sha(peak)==record['peak_npy_sha256']==verified['peak_npy_sha256']
  assert sha(metadata)==record['peak_metadata_sha256']==verified['peak_metadata_sha256']
  graph_hashes[name]=sha(graph);peak_hashes[name]=sha(peak)
assert gate['receipt_sha256']=={c['cohort']:c['independent_receipt_sha256'] for c in cfg['cohorts']}
assert gate['graph_csv_sha256']==graph_hashes and gate['peak_npy_sha256']==peak_hashes
for row in rows:
 name=row['dataset'];short=row['cohort']
 cohort=next(c for c in cfg['cohorts'] if c['cohort']==short)
 cache=pathlib.Path(cohort['cache_run'])
 assert row['graph_csv_sha256']==graph_hashes[name]
 assert row['peak_npy_sha256']==peak_hashes[name]
 peak=np.load(cache/'output'/('peaks__'+name+'.npy'),mmap_mode='r',allow_pickle=False)
 assert row['peak_count']==len(peak)
 available={(int(v['t']),int(v['z']),int(v['y']),int(v['x'])):float(v['probability']) for v in peak}
 assert len(available)==len(peak)
 nodes={};edges=[]
 with (cache/'output'/('graph__'+name+'.csv')).open(newline='') as stream:
  reader=csv.DictReader(stream)
  assert reader.fieldnames==['id','dataset','row_type','node_id','t','z','y','x','source_id','target_id']
  for record in reader:
   assert record['dataset']==name
   if record['row_type']=='node':
    nodes[int(record['node_id'])]=(int(record['t']),float(record['z']),
     float(record['y']),float(record['x']))
   else:
    assert record['row_type']=='edge'
    edges.append((int(record['source_id']),int(record['target_id'])))
 assert row['original_nodes']==len(nodes) and row['original_edges']==len(edges)
 incoming={};outgoing=set();frames={}
 for node,position in nodes.items():frames.setdefault(position[0],[]).append(np.asarray(position[1:])*scale)
 for a,b in edges:
  assert a in nodes and b in nodes and nodes[b][0]==nodes[a][0]+1
  incoming.setdefault(b,[]).append(a);outgoing.add(a)
 seeds={n for n in nodes if len(incoming.get(n,[]))==1 and n not in outgoing and nodes[n][0]<=97}
 assert row['seed_count']==len(seeds)
 assert row['selected_conflict_free_chain_count']==len(row['selected_chains'])
 used=set();seen_seeds=set()
 for chain in row['selected_chains']:
  seed=chain['seed_id'];p1=tuple(chain['p1']);p2=tuple(chain['p2'])
  assert seed in seeds and seed not in seen_seeds and len(p1)==len(p2)==4
  seen_seeds.add(seed)
  assert p1 in available and p2 in available and p1 not in used and p2 not in used
  assert available[p1]>0.075 and available[p2]>0.075
  used.update((p1,p2))
  t=nodes[seed][0];assert p1[0]==t+1 and p2[0]==t+2
  p0=np.asarray(nodes[seed][1:])*scale
  previous=np.asarray(nodes[incoming[seed][0]][1:])*scale
  v=p0-previous
  x1=np.asarray(p1[1:])*down*scale;x2=np.asarray(p2[1:])*down*scale
  residuals=(x1-(p0+v),x2-(p0+2*v),x2-x1,(x2-x1)-v)
  sq=[float(np.dot(r,r)) for r in residuals]
  assert all(z<=49.0+1e-12 for z in sq)
  assert math.isclose(sum(sq),chain['rank_residual_sq'],rel_tol=0,abs_tol=1e-10)
  assert math.isclose(-available[p1]-available[p2],chain['rank_negative_probability_sum'],
   rel_tol=0,abs_tol=1e-10)
  for key,point in ((p1,x1),(p2,x2)):
   assert not frames.get(key[0]) or cKDTree(frames[key[0]]).query(point)[0]>7.0
  assert chain['seed_legal_pair_count']>=1
 assert len(used)==2*len(row['selected_chains'])
compact_rows=[{k:v for k,v in row.items() if k!='selected_chains'} for row in rows]
print(json.dumps({'status':'PASS_EXP240_INDEPENDENT_READBACK_NO_LABELS',
 'manifest_sha256':sha(code/'manifest.json'),'launch_sha256':sha(run/'launch.json'),
 'exit_sha256':sha(run/'exit.json'),'no_label_gate_sha256':sha(gate_path),
 'result_sha256':sha(result_path),'rows':compact_rows,'cohorts':result['cohorts'],
 'decision':result['preregistered_decision'],'child_absent':True,
 'source_labels_read':False,'target_data_opened':False,'graph_created':False,
 'gpu_used':False,'kaggle_post':False}))
'''
    for token, value in {'@@ROOT@@': CODE.rsplit('/code/', 1)[0],
                         '@@CODE@@': CODE, '@@RUN@@': RUN,
                         '@@MANIFEST@@': manifest_sha,
                         '@@LAUNCH@@': launch,
                         '@@COMMAND@@': command(manifest_sha)}.items():
        source = source.replace(token, repr(value))
    assert '@@' not in source
    compile(source, 'exp240_independent_remote_verifier', 'exec')
    return source


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    local_gate()
    if not args.execute:
        print(json.dumps({'status': 'EXP240_VERIFY_LOCAL_REVIEW_ONLY',
                          'stage_receipt_present': STAGE_RECEIPT.exists(),
                          'launch_receipt_present': LAUNCH_RECEIPT.exists(),
                          'remote_read': False, 'source_labels_read': False}))
        return
    assert not OUT.exists()
    manifest_sha = sha(MANIFEST)
    stage = json.loads(STAGE_RECEIPT.read_text())
    launch = json.loads(LAUNCH_RECEIPT.read_text())
    assert stage['status'] == 'STAGED_EXP240_LABEL_FREE_CPU_BUNDLE'
    assert stage['manifest_sha256'] == manifest_sha
    assert launch['status'] == 'LAUNCHED_EXP240_LABEL_FREE_SOURCE19_CPU_SCREEN'
    assert launch['manifest_sha256'] == manifest_sha
    assert launch['stage_receipt_sha256'] == sha(STAGE_RECEIPT)
    assert launch['source_labels_read'] is False and launch['gpu_used'] is False
    assert launch['remote']['command'] == command(manifest_sha)
    assert launch['remote']['pythonoptimize'] == '0'
    checked = ssh('nsu-quadro', f'env PYTHONOPTIMIZE=0 {PYTHON} -B -',
                  remote_source(manifest_sha, launch['remote']))
    assert checked['status'] == 'PASS_EXP240_INDEPENDENT_READBACK_NO_LABELS'
    assert checked['manifest_sha256'] == manifest_sha
    assert checked['child_absent'] and not checked['source_labels_read']
    assert not checked['target_data_opened'] and not checked['graph_created']
    assert not checked['gpu_used'] and not checked['kaggle_post']
    ids = [n for c in json.loads((BUNDLE / 'config.json').read_text())['cohorts'] for n in c['ids']]
    summary, decision = recount(checked['rows'], ids)
    assert checked['cohorts'] == summary and checked['decision'] == decision
    compact = {key: value for key, value in checked.items() if key != 'rows'}
    exclusive_json(OUT, {'status': 'PASS_EXP240_LABEL_FREE_CPU_INDEPENDENT_VERIFICATION',
                         'source_manifest_sha256': manifest_sha,
                         'stage_receipt_sha256': sha(STAGE_RECEIPT),
                         'launch_receipt_sha256': sha(LAUNCH_RECEIPT),
                         'verifier_source_sha256': sha(Path(__file__)),
                         'remote': compact, 'source_labels_read': False,
                         'target_data_opened': False, 'gpu_used': False,
                         'kaggle_post': False})
    print(json.dumps({'status': 'PASS_EXP240_LABEL_FREE_CPU_INDEPENDENT_VERIFICATION',
                      'decision': decision, 'receipt_sha256': sha(OUT)}))


if __name__ == '__main__':
    main()
