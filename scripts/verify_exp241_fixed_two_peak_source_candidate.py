"""Independent read-only validation of EXP241's 19 fixed source graphs."""

import argparse
import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh
from stage_exp241_fixed_two_peak_source_candidate import (
    BUNDLE, CODE, MANIFEST, RECEIPT as STAGE_RECEIPT, ROOT, RUN,
    exclusive_json, local_gate, sha,
)
from launch_exp241_fixed_two_peak_source_candidate import (
    PYTHON, RECEIPT as LAUNCH_RECEIPT, command,
)

if not __debug__:
    raise RuntimeError('EXP241 independent verifier requires PYTHONOPTIMIZE=0')

OUT = ROOT / 'reports/exp241_fixed_two_peak_source_candidate_verified_20260927.json'


def remote_source(manifest_sha: str, launch: dict) -> str:
    source = r'''import csv,hashlib,json,math,os,pathlib,sys
import numpy as np
from scipy.spatial import cKDTree
if not __debug__:raise RuntimeError('EXP241 verifier requires assertions')
root=pathlib.Path(@@ROOT@@);code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert os.environ.get('PYTHONOPTIMIZE')=='0' and os.uname().nodename=='prepost'
data=root/'data'
def deny(event,args):
 if event not in ('open','os.listdir','os.scandir') or not args:return
 raw=args[0]
 if not isinstance(raw,(str,bytes,os.PathLike)):return
 path=pathlib.Path(os.fsdecode(raw)).resolve()
 if path.is_relative_to(data) or any(part.lower().endswith('.geff') for part in path.parts):
  raise PermissionError('EXP241 verifier denies data and GEFF')
sys.addaudithook(deny)
assert code.is_dir() and run.is_dir()
assert sha(code/'manifest.json')==@@MANIFEST@@
manifest=json.loads((code/'manifest.json').read_text())
assert manifest['status']=='SEALED_EXP241_LABEL_FREE_CPU_GRAPH_BUNDLE'
assert {p.relative_to(code).as_posix():sha(p) for p in code.rglob('*') if p.is_file()}=={**manifest['files'],'manifest.json':@@MANIFEST@@}
builder=(code/'build_exp241_graphs.py').read_text()
assert 'if not __debug__' in builder and 'os.fsync(stream.fileno())' in builder
assert "durable_json(OUTPUT / 'no_label_gate.json', gate)" in builder
assert builder.index("durable_json(OUTPUT / 'no_label_gate.json', gate)")<builder.index('nodes, edges = old.load_graph')
cfg=json.loads((code/'config.json').read_text())
assert cfg['status']=='PREREGISTERED_EXP241_FIXED_SOURCE19_LABEL_FREE_GRAPH'
assert cfg['output']==str(run/'output') and cfg['expected_chains']=={'source44':835,'source6':358}
assert cfg['source_only'] and not any(cfg[k] for k in ('source_labels_read','target_data_opened','metric_computed','gpu_used','kaggle_post'))
remote_launch=json.loads((run/'launch.json').read_text())
assert remote_launch==@@LAUNCH@@
assert remote_launch['status']=='LAUNCHED_EXP241_LABEL_FREE_SOURCE19_CPU_GRAPH_BUILD'
assert remote_launch['manifest_sha256']==@@MANIFEST@@ and remote_launch['code']==str(code) and remote_launch['run']==str(run)
assert remote_launch['command']==@@COMMAND@@ and remote_launch['pythonoptimize']=='0' and remote_launch['cuda_visible_devices']==''
assert remote_launch['source_labels_read'] is False and remote_launch['gpu_used'] is False
assert sha(run/'cpu_wrapper.py')==remote_launch['wrapper_sha256']
wrapper=(run/'cpu_wrapper.py').read_text()
assert "PYTHONOPTIMIZE='0'" in wrapper and "CUDA_VISIBLE_DEVICES=''" in wrapper
exit_record=json.loads((run/'exit.json').read_text())
assert exit_record['returncode']==0 and exit_record['timeout'] is False and exit_record['error'] is None
assert exit_record['pythonoptimize']=='0' and exit_record['graph_created'] is True
assert exit_record['source_labels_read'] is False and exit_record['target_data_opened'] is False
assert exit_record['gpu_used'] is False and exit_record['kaggle_post'] is False
child=json.loads((run/'child.json').read_text())
assert child['command']==@@COMMAND@@ and child['pythonoptimize']=='0' and child['cuda_visible_devices']==''
assert child['ram_bytes']==16*1024**3 and child['cpu_affinity']==[24,25,26,27]
assert child['pid']==exit_record['pid'] and child['start']==exit_record['start']
def proc(pid):
 try:fields=pathlib.Path(f'/proc/{pid}/stat').read_text().split(') ')[1].split()
 except FileNotFoundError:return None
 return fields[0],fields[19]
wp=proc(remote_launch['wrapper_pid']);cp=proc(child['pid'])
assert wp is None or wp[0]=='Z'
assert cp is None or cp[0]=='Z' or cp[1]!=child['start']
output=run/'output'
old_code=pathlib.Path(cfg['exp240_code']);old_run=pathlib.Path(cfg['exp240_run'])
assert old_code==root/'code'/old_code.name and old_run==root/'runs'/old_run.name
assert sha(old_code/'manifest.json')==cfg['exp240_manifest_sha256']
old_manifest=json.loads((old_code/'manifest.json').read_text())
assert {p.relative_to(old_code).as_posix():sha(p) for p in old_code.rglob('*') if p.is_file()}=={**old_manifest['files'],'manifest.json':cfg['exp240_manifest_sha256']}
assert sha(old_run/'output/result.json')==cfg['exp240_result_sha256']
assert sha(old_run/'output/no_label_gate.json')==cfg['exp240_no_label_gate_sha256']
old_cfg=json.loads((old_code/'config.json').read_text())
old_result=json.loads((old_run/'output/result.json').read_text())
old_gate=json.loads((old_run/'output/no_label_gate.json').read_text())
ids=[name for cohort in old_cfg['cohorts'] for name in cohort['ids']]
assert len(ids)==len(set(ids))==19 and [len(c['ids']) for c in old_cfg['cohorts']]==[8,11]
assert [r['dataset'] for r in old_result['rows']]==ids and old_gate['ids']==ids
assert old_result['status']=='PASS_EXP240_LABEL_FREE_SOURCE_CHAIN_FEASIBILITY'
assert old_result['no_label_gate_sha256']==cfg['exp240_no_label_gate_sha256']
assert old_result['preregistered_decision']=='PERMIT_ONE_FIXED_SOURCE_CANDIDATE_WITH_SEPARATE_SCORE_PREREG'
expected_files={'no_label_gate.json','result.json'}|{'graph__'+name+'.csv' for name in ids}
assert {p.name for p in output.iterdir()}==expected_files
gate_path=output/'no_label_gate.json';result_path=output/'result.json'
gate=json.loads(gate_path.read_text());result=json.loads(result_path.read_text())
assert gate['status']=='PASS_EXP241_DURABLE_NO_LABEL_GATE_BEFORE_CSV_NPY_PARSE'
assert gate['bundle_sha256']==@@MANIFEST@@ and gate['ordered_ids']==ids
assert gate['csv_npy_values_read_before_gate'] is False
assert gate['source_labels_read'] is False and gate['target_data_opened'] is False
assert gate['gpu_used'] is False and gate['kaggle_post'] is False
assert result['status']=='BUILT_EXP241_FIXED_SOURCE19_LABEL_FREE_GRAPHS'
assert result['bundle_sha256']==@@MANIFEST@@ and result['ordered_ids']==ids
assert result['no_label_gate_sha256']==sha(gate_path)
assert result['exp240_result_sha256']==cfg['exp240_result_sha256']
assert result['source_labels_read'] is False and result['target_data_opened'] is False
assert result['metric_computed'] is False and result['gpu_used'] is False and result['kaggle_post'] is False
assert [r['dataset'] for r in result['rows']]==ids and len(result['rows'])==19
assert gate_path.stat().st_mtime_ns<=min((output/('graph__'+name+'.csv')).stat().st_mtime_ns for name in ids)
assert gate_path.stat().st_mtime_ns<=result_path.stat().st_mtime_ns
columns=['id','dataset','row_type','node_id','t','z','y','x','source_id','target_id']
scale=np.asarray([1.625,0.40625,0.40625]);down=np.asarray([1,4,4])
totals={'source44':0,'source6':0};checked=[]
for cohort in old_cfg['cohorts']:
 cache=pathlib.Path(cohort['cache_run'])/'output';short=cohort['cohort']
 assert [r['dataset'] for r in old_result['rows'] if r['cohort']==short]==cohort['ids']
 for name in cohort['ids']:
  index=ids.index(name);selection=old_result['rows'][index];record=result['rows'][index]
  assert record['dataset']==selection['dataset']==name and record['cohort']==selection['cohort']==short
  original=cache/('graph__'+name+'.csv');new=output/('graph__'+name+'.csv')
  peak=cache/('peaks__'+name+'.npy')
  assert sha(original)==selection['graph_csv_sha256']==record['source_graph_sha256']==gate['graph_csv_sha256'][name]
  assert sha(peak)==selection['peak_npy_sha256']==record['source_peak_npy_sha256']==gate['peak_npy_sha256'][name]
  assert sha(new)==record['candidate_csv_sha256']
  old_bytes=original.read_bytes();new_bytes=new.read_bytes()
  assert new_bytes.startswith(old_bytes) and old_bytes.endswith(b'\n')
  old_rows=list(csv.reader(old_bytes.decode('utf-8').splitlines()))
  new_rows=list(csv.reader(new_bytes.decode('utf-8').splitlines()))
  assert old_rows[0]==new_rows[0]==columns and new_rows[:len(old_rows)]==old_rows
  assert len(old_rows)-1==record['original_rows']==selection['original_nodes']+selection['original_edges']
  assert record['original_prefix_sha256']==sha(original)
  old_ids=[int(r[0]) for r in old_rows[1:]]
  assert len(old_ids)==len(set(old_ids)) and min(old_ids)>=0
  old_nodes={};old_edges=[]
  for r in old_rows[1:]:
   assert r[1]==name
   if r[2]=='node':
    node=int(r[3]);assert node not in old_nodes and int(r[8])==int(r[9])==-1
    old_nodes[node]=(int(r[4]),float(r[5]),float(r[6]),float(r[7]))
   else:
    assert r[2]=='edge' and all(float(v)==-1 for v in r[3:8])
    old_edges.append((int(r[8]),int(r[9])))
  assert len(old_nodes)==selection['original_nodes'] and len(old_edges)==selection['original_edges']
  available=np.load(peak,mmap_mode='r',allow_pickle=False)
  assert available.dtype.names==('t','z','y','x','probability') and len(available)==selection['peak_count']
  probs={(int(p['t']),int(p['z']),int(p['y']),int(p['x'])):float(p['probability']) for p in available}
  assert len(probs)==len(available)
  incoming={};outgoing=set();frames={}
  for node,point in old_nodes.items():frames.setdefault(point[0],[]).append(np.asarray(point[1:])*scale)
  trees={t:cKDTree(np.asarray(coords)) for t,coords in frames.items()}
  for a,b in old_edges:
   assert a in old_nodes and b in old_nodes and old_nodes[b][0]==old_nodes[a][0]+1
   incoming.setdefault(b,[]).append(a);outgoing.add(a)
  assert max((len(v) for v in incoming.values()),default=0)<=1
  seen_seeds=set();seen_peaks=set();expected=[]
  chains=sorted(selection['selected_chains'],key=lambda c:(c['seed_id'],c['p1'],c['p2']))
  assert len(chains)==selection['selected_conflict_free_chain_count']==record['selected_chains']
  first_row=max(old_ids)+1;first_node=max(old_nodes)+1
  for j,chain in enumerate(chains):
   seed=chain['seed_id'];p1=tuple(chain['p1']);p2=tuple(chain['p2'])
   assert seed in old_nodes and seed not in seen_seeds and len(incoming.get(seed,[]))==1
   assert seed not in outgoing and old_nodes[seed][0]<=97
   assert p1 in probs and p2 in probs and p1 not in seen_peaks and p2 not in seen_peaks
   assert probs[p1]>0.075 and probs[p2]>0.075 and p1[0]==old_nodes[seed][0]+1 and p2[0]==p1[0]+1
   p0=np.asarray(old_nodes[seed][1:])*scale;pred=np.asarray(old_nodes[incoming[seed][0]][1:])*scale
   v=p0-pred;x1=np.asarray(p1[1:])*down*scale;x2=np.asarray(p2[1:])*down*scale
   residuals=(x1-(p0+v),x2-(p0+2*v),x2-x1,(x2-x1)-v)
   sq=[float(np.dot(r,r)) for r in residuals]
   assert all(s<=49+1e-12 for s in sq)
   assert math.isclose(sum(sq),chain['rank_residual_sq'],rel_tol=0,abs_tol=1e-10)
   assert math.isclose(-probs[p1]-probs[p2],chain['rank_negative_probability_sum'],rel_tol=0,abs_tol=1e-10)
   for key,pos in ((p1,x1),(p2,x2)):
    assert key[0] not in trees or trees[key[0]].query(pos)[0]>7
   n1=first_node+2*j;n2=n1+1;rid=first_row+4*j
   expected.extend([
    [str(rid),name,'node',str(n1),str(p1[0]),str(p1[1]),str(p1[2]*4),str(p1[3]*4),'-1','-1'],
    [str(rid+1),name,'node',str(n2),str(p2[0]),str(p2[1]),str(p2[2]*4),str(p2[3]*4),'-1','-1'],
    [str(rid+2),name,'edge','-1','-1','-1','-1','-1',str(seed),str(n1)],
    [str(rid+3),name,'edge','-1','-1','-1','-1','-1',str(n1),str(n2)]])
   seen_seeds.add(seed);seen_peaks.update((p1,p2))
  assert new_rows[len(old_rows):]==expected
  assert record['first_new_node_id']==first_node and record['first_new_row_id']==first_row
  assert record['added_nodes']==record['added_edges']==2*len(chains)
  assert record['added_rows']==4*len(chains)
  totals[short]+=len(chains)
  all_ids=set();nodes={};edges=[]
  for r in new_rows[1:]:
   rid=int(r[0]);assert rid>=0 and rid not in all_ids and r[1]==name
   all_ids.add(rid)
   if r[2]=='node':
    n=int(r[3]);assert n>=0 and n not in nodes and int(r[8])==int(r[9])==-1
    point=(int(r[4]),float(r[5]),float(r[6]),float(r[7]))
    assert all(math.isfinite(v) and 0<=v<bound for v,bound in zip(point,(100,64,256,256)))
    nodes[n]=point
   else:
    assert r[2]=='edge' and all(float(v)==-1 for v in r[3:8])
    edges.append((int(r[8]),int(r[9])))
  indeg={};outdeg={}
  assert len(edges)==len(set(edges))
  for a,b in edges:
   assert a in nodes and b in nodes and nodes[b][0]==nodes[a][0]+1
   indeg[b]=indeg.get(b,0)+1;outdeg[a]=outdeg.get(a,0)+1
  assert max(indeg.values(),default=0)<=1 and max(outdeg.values(),default=0)<=2
  assert len(nodes)==len(old_nodes)+2*len(chains) and len(edges)==len(old_edges)+2*len(chains)
  for j in range(len(chains)):
   n1=first_node+2*j;n2=n1+1
   assert indeg[n1]==1 and outdeg[n1]==1 and indeg[n2]==1 and outdeg.get(n2,0)==0
  assert set(record)=={'dataset','cohort','source_graph_sha256','source_peak_npy_sha256',
   'selected_chains','original_rows','original_prefix_sha256','added_nodes','added_edges',
   'added_rows','first_new_row_id','first_new_node_id','candidate_csv_sha256'}
  checked.append(record)
assert totals==cfg['expected_chains']==result['selected_chains']
assert {k:2*v for k,v in totals.items()}==cfg['expected_added_nodes']==cfg['expected_added_edges']
print(json.dumps({'status':'PASS_EXP241_INDEPENDENT_LABEL_FREE_GRAPH_VERIFICATION',
 'run':str(run),'manifest_sha256':sha(code/'manifest.json'),
 'launch_sha256':sha(run/'launch.json'),'exit_sha256':sha(run/'exit.json'),
 'no_label_gate_sha256':sha(gate_path),'result_sha256':sha(result_path),
 'ordered_ids':ids,'rows':checked,'selected_chains':totals,
 'exact_original_byte_prefix':True,'selected_peak_and_graph_provenance':True,
 'exclusive_new_paths':True,'graph_invariants':True,
 'source_labels_read':False,'target_data_opened':False,
 'metric_computed':False,'gpu_used':False,'kaggle_post':False}))
'''
    for token, value in {'@@ROOT@@': CODE.rsplit('/code/', 1)[0],
                         '@@CODE@@': CODE, '@@RUN@@': RUN,
                         '@@MANIFEST@@': manifest_sha,
                         '@@LAUNCH@@': launch,
                         '@@COMMAND@@': command(manifest_sha)}.items():
        source = source.replace(token, repr(value))
    assert '@@' not in source
    compile(source, 'exp241_independent_remote_verifier', 'exec')
    return source


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    local_gate()
    if not args.execute:
        print(json.dumps({'status': 'EXP241_VERIFY_LOCAL_REVIEW_ONLY',
                          'stage_receipt_present': STAGE_RECEIPT.exists(),
                          'launch_receipt_present': LAUNCH_RECEIPT.exists(),
                          'remote_read': False, 'source_labels_read': False}))
        return
    assert not OUT.exists()
    manifest_sha = sha(MANIFEST)
    stage = json.loads(STAGE_RECEIPT.read_text())
    launch = json.loads(LAUNCH_RECEIPT.read_text())
    assert stage['status'] == 'STAGED_EXP241_LABEL_FREE_CPU_GRAPH_BUNDLE'
    assert stage['manifest_sha256'] == manifest_sha
    assert launch['status'] == 'LAUNCHED_EXP241_LABEL_FREE_SOURCE19_CPU_GRAPH_BUILD'
    assert launch['manifest_sha256'] == manifest_sha
    assert launch['stage_receipt_sha256'] == sha(STAGE_RECEIPT)
    assert launch['remote']['command'] == command(manifest_sha)
    assert launch['remote']['pythonoptimize'] == '0'
    checked = ssh('nsu-quadro', f'env PYTHONOPTIMIZE=0 CUDA_VISIBLE_DEVICES= {PYTHON} -B -',
                  remote_source(manifest_sha, launch['remote']))
    assert checked['status'] == 'PASS_EXP241_INDEPENDENT_LABEL_FREE_GRAPH_VERIFICATION'
    assert checked['manifest_sha256'] == manifest_sha and checked['run'] == RUN
    assert len(checked['ordered_ids']) == len(checked['rows']) == 19
    assert checked['selected_chains'] == {'source44': 835, 'source6': 358}
    assert checked['exact_original_byte_prefix'] and checked['graph_invariants']
    assert checked['selected_peak_and_graph_provenance'] and checked['exclusive_new_paths']
    assert not any(checked[k] for k in
        ('source_labels_read', 'target_data_opened', 'metric_computed', 'gpu_used', 'kaggle_post'))
    exclusive_json(OUT, {'status': checked['status'], 'run': RUN,
                         'manifest_sha256': manifest_sha,
                         'stage_receipt_sha256': sha(STAGE_RECEIPT),
                         'launch_receipt_sha256': sha(LAUNCH_RECEIPT),
                         'verifier_source_sha256': sha(Path(__file__)),
                         'remote': checked, 'source_labels_read': False,
                         'target_data_opened': False, 'metric_computed': False,
                         'gpu_used': False, 'kaggle_post': False})
    print(json.dumps({'status': checked['status'], 'receipt_sha256': sha(OUT),
                      'result_sha256': checked['result_sha256']}))


if __name__ == '__main__':
    main()
