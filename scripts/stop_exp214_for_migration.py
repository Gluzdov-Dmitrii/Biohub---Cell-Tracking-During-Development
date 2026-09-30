"""Stop only the registered owned RTX trainer after a resumable epoch exists."""
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import torch

root=Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
run=root/'runs/exp214_reduced6bba_s314159_20260912'
launch=json.loads((run/'launch.json').read_text())
assert launch['config']['lease_id']=='biohub-exp214-reduced6bba-s314159-rtx-20260912'
assert launch['config']['gpu']=='GPU-a4b01714-3774-ca39-a9d9-2f30429e84ba'
pid=launch['pid'];assert Path(f'/proc/{pid}/stat').read_text().split()[21]==launch['start']
assert os.getpgid(pid)==pid
checkpoint=run/'output/checkpoint_last.pth'
c=torch.load(checkpoint,map_location='cpu',weights_only=False)
assert c['contract']['fold']=='6bba' and c['contract']['seed']==314159
assert c['contract']['plan_sha256']=='983d2953c915d91d41db33bf8fafa14bd17ed6e5aeefd5f67c0dda8d7759090a'
assert 2<=c['epoch']<12
receipt={'action':'SIGTERM_OWN_RTX_TRAINER_FOR_A100_RESUME','pid':pid,'start':launch['start'],
         'checkpoint_epoch_before_signal':c['epoch'],'checkpoint_sha256_before_signal':hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
         'target_metrics_read':False,'utc_epoch':time.time(),'reason':'Measured737s RTX epoch vs~300s A100, preserve fixed12epoch science and optimizer state'}
with (run/'migration_stop_receipt.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
assert Path(f'/proc/{pid}/stat').read_text().split()[21]==launch['start']
os.killpg(pid,signal.SIGTERM)
print(json.dumps(receipt,indent=2))
