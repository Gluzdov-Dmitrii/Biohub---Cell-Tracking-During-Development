"""EXP223 bounded inference smoke: source embryo only, no annotation access."""
import sys,json,hashlib,time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
CODE=Path(__file__).resolve().parent
OUT=Path(sys.argv[1]);OUT.mkdir(exist_ok=True)
for name,digest in json.loads((CODE/'package_manifest.json').read_text()).items():
 assert hashlib.sha256((CODE/name).read_bytes()).hexdigest()==digest,name
sys.path.insert(0,str(CODE/'selected/src/src'))
# Fail closed if any code attempts to open annotations in this no-label process.
def audit(event,args):
 if event=='open' and args and isinstance(args[0],(str,bytes)):
  value=str(args[0]).lower()
  if '.geff' in value:raise RuntimeError('EXP223 prohibits annotation access')
sys.addaudithook(audit)
import torch
from engine import load_checkpoint
from inference import predict_one,write_submission
assert torch.cuda.is_available()
cfg=SimpleNamespace(**json.loads((CODE/'selected/resolved_config.json').read_text()))
data=ROOT/'data/exp213_source_view_20260912'
choices=[]
for p in data.glob('6bba_*.zarr'):
 shape=json.loads((p/'0/zarr.json').read_text())['shape']
 if shape[0]>=16:choices.append((shape[1]*shape[2]*shape[3],p))
assert choices
movie=min(choices,key=lambda x:(x[0],x[1].name))[1]
# Fold0 was trained on6bba: this source-only16frame smoke is not OOF scoring.
model,model_config=load_checkpoint(CODE/'selected/fold0_selected.pt',torch.device('cuda'))
t0=time.time();graph,stats=predict_one(model,model_config,movie,torch.device('cuda'),cfg,16)
write_submission([(movie.stem,graph)],OUT/'smoke.csv')
result={'status':'PASS_SOURCE_ONLY_NO_LABEL_SMOKE','movie':movie.stem,'fold':0,'max_frames':16,'seconds':time.time()-t0,'nodes':len(graph.nodes),'edges':len(graph.edges),'stats':stats,'peak_cuda_bytes':torch.cuda.max_memory_allocated(),'csv_sha256':hashlib.sha256((OUT/'smoke.csv').read_bytes()).hexdigest()}
(OUT/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
