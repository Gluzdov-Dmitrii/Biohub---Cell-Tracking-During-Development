"""EXP223 no-label resumable inference, with per-movie sealed receipts."""
import argparse,csv,hashlib,json,sys,time
from pathlib import Path
from types import SimpleNamespace
ARMS={'selected50_20':('selected','selected'),'fixedlast50_same_decoder':('fixed_last','last')}
def atomic_json(path,value):
 p=Path(path);t=p.with_suffix('.json.tmp');t.write_text(json.dumps(value,indent=2));t.replace(p)
def resume_receipt(receipt,csvpath,contract,row):
 old=json.loads(Path(receipt).read_text());assert old['contract']==contract and old['csv_sha256']==sha(csvpath);verify_csv(csvpath,row);return old
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def validate_rows(rows,shape,name):
 nodes={};edges=[];ids=set()
 for r in rows:
  assert r['dataset']==name
  i=int(r['id']);assert i not in ids;ids.add(i)
  if r['row_type']=='node':
   n=int(r['node_id']);assert n not in nodes
   point=tuple(int(r[k]) for k in ['t','z','y','x']);assert all(0<=v<s for v,s in zip(point,shape));nodes[n]=point
  else:
   assert r['row_type']=='edge';edges.append((int(r['source_id']),int(r['target_id'])))
 assert nodes and len(edges)==len(set(edges));inc={};out={}
 for s,t in edges:
  assert s in nodes and t in nodes and nodes[t][0]==nodes[s][0]+1
  inc[t]=inc.get(t,0)+1;out[s]=out.get(s,0)+1
 assert max(inc.values(),default=0)<=1 and max(out.values(),default=0)<=2
 return {'nodes':len(nodes),'edges':len(edges)}
def verify_csv(p,row):
 with Path(p).open() as f:return validate_rows(list(csv.DictReader(f)),row['shape'],row['dataset'])
def route(row,benchmark=False):
 expected=0 if row['dataset'].startswith('44b6_') else 1 if row['dataset'].startswith('6bba_') else -1
 assert expected>=0 and row['fold']==expected
 return 1-expected if benchmark else expected

def main():
 ap=argparse.ArgumentParser();ap.add_argument('plan');ap.add_argument('--plan-sha256',required=True);a=ap.parse_args();assert sha(a.plan)==a.plan_sha256;plan=json.loads(Path(a.plan).read_text());code=Path(plan['code']);out=Path(plan['output']);out.mkdir(exist_ok=True,parents=True)
 assert sha(code/'code_manifest.json')==plan['code_manifest_sha256']
 for name,digest in json.loads((code/'code_manifest.json').read_text()).items():assert sha(code/name)==digest,name
 manifest=code/'heldout175_manifest.json';assert sha(manifest)==plan['manifest_sha256']
 allrows=json.loads(manifest.read_text())['rows'];assert len(allrows)==175
 rows=[r for r in allrows if r['dataset'] in plan['movies']];assert len(rows)==len(set(plan['movies']))
 benchmark=plan['mode']=='source_benchmark';assert benchmark or plan['mode']=='heldout'
 if not benchmark:assert plan['arms']==['selected50_20','fixedlast50_same_decoder']
 def audit(event,args):
  if event=='open' and args and isinstance(args[0],(str,bytes)) and '.geff' in str(args[0]).lower():raise RuntimeError('EXP223 NO LABEL ACCESS')
 sys.addaudithook(audit)
 sys.path.insert(0,str(code/'selected/src/src'))
 import torch
 from engine import load_checkpoint
 from inference import predict_one,write_submission
 assert torch.cuda.is_available();cfg=SimpleNamespace(**json.loads((code/'selected/resolved_config.json').read_text()))
 loaded={};records=[];start=time.time()
 for arm in plan['arms']:
  assert arm in ARMS
  for row in rows:
   fold=route(row,benchmark);folder,suffix=ARMS[arm];weight=code/folder/f'fold{fold}_{suffix}.pt';csvpath=out/f"{arm}__{row['dataset']}.csv";receipt=csvpath.with_suffix('.json')
   contract={'arm':arm,'dataset':row['dataset'],'fold':fold,'mode':plan['mode'],'weight_sha256':sha(weight),'manifest_sha256':plan['manifest_sha256'],'decoder_sha256':sha(code/'selected/resolved_config.json'),'code_sha256':sha(code/'code_manifest.json')}
   if receipt.exists():
    old=resume_receipt(receipt,csvpath,contract,row);records.append(old);continue
   assert not csvpath.exists(),'Unreceipted CSV: reconcile, do not overwrite'
   key=(arm,fold)
   if key not in loaded:
    loaded.clear();torch.cuda.empty_cache();loaded[key]=load_checkpoint(weight,torch.device('cuda'))
   t0=time.time();model,mc=loaded[key];graph,stats=predict_one(model,mc,Path(row['zarr']),torch.device('cuda'),cfg,None)
   tmp=csvpath.with_suffix('.tmp');write_submission([(row['dataset'],graph)],tmp);counts=verify_csv(tmp,row);tmp.replace(csvpath)
   record={'contract':contract,'seconds':time.time()-t0,'csv_sha256':sha(csvpath),'shape':row['shape'],'peak_cuda_bytes':torch.cuda.max_memory_allocated(),**counts,'stats':stats}
   atomic_json(receipt,record);records.append(record);print(json.dumps({k:record[k] for k in ['contract','seconds','nodes','edges']}),flush=True)
 result={'status':'PASS_NO_LABEL_CHUNK','mode':plan['mode'],'records':records,'seconds':time.time()-start}
 atomic_json(out/'complete.json',result);print(json.dumps({'status':result['status'],'records':len(records),'seconds':result['seconds']}),flush=True)
if __name__=='__main__':main()
