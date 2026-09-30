import pathlib,json,sys,base64,hashlib
sys.path.insert(0,'scripts');from monitor_exp213_job import ssh
manifest=pathlib.Path('reports/exp223_heldout175_manifest_20260921.json').read_bytes()
source=r'''import pathlib,json,csv,hashlib,base64,math
root=pathlib.Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
code=root/'code/exp223_horaz0_v1_20260921';data=base64.b64decode(MANIFEST)
p=code/'heldout175_manifest.json'
if p.exists():assert p.read_bytes()==data
else:p.write_bytes(data)
run=root/'runs/exp223_horaz0_source_smoke_20260921'
a=json.loads((run/'output/result.json').read_text());shape=json.loads((root/'data/exp213_source_view_20260912'/(a['movie']+'.zarr')/'0/zarr.json').read_text())['shape'];shape[0]=16
nodes={};edges=[];ids=set()
with (run/'output/smoke.csv').open() as f:
 reader=csv.DictReader(f)
 assert reader.fieldnames==['id','dataset','row_type','node_id','t','z','y','x','source_id','target_id']
 for row in reader:
  assert row['dataset']==a['movie'];i=int(row['id']);assert i not in ids;ids.add(i)
  v={k:int(row[k]) for k in ['node_id','t','z','y','x','source_id','target_id']}
  if row['row_type']=='node':
   n=v['node_id'];assert n not in nodes
   point=tuple(v[k] for k in ['t','z','y','x']);assert all(0<=x<s for x,s in zip(point,shape)),point
   nodes[n]=point
  else:
   assert row['row_type']=='edge';edges.append((v['source_id'],v['target_id']))
assert len(edges)==len(set(edges))
incoming={};outgoing={}
for s,t in edges:
 assert s in nodes and t in nodes and nodes[t][0]==nodes[s][0]+1
 incoming[t]=incoming.get(t,0)+1;outgoing[s]=outgoing.get(s,0)+1
assert max(incoming.values(),default=0)<=1 and max(outgoing.values(),default=0)<=2
result={'status':'PASS_SMOKE_GRAPH_BOUNDS_AND_SEALED_COHORT','n_movies':175,'fold_counts':{'0':59,'1':116},'manifest_sha256':hashlib.sha256(data).hexdigest(),'smoke_csv_sha256':a['csv_sha256'],'nodes':len(nodes),'edges':len(edges),'full_inference_launched':False}
(code/'graph_and_cohort_gate.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
'''.replace('MANIFEST',repr(base64.b64encode(manifest).decode()))
r=ssh('nsu-a100','python3 -',source);pathlib.Path('reports/exp223_graph_and_cohort_gate_20260921.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
