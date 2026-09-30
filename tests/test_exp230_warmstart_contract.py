"""Source routing and one-checkpoint allowlist for the warm-start pilot."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_exp230_warmstart_pilot import PARENT_SHA, WarmstartGuard, validate


class WarmstartContract(unittest.TestCase):
    def setUp(self):
        with Path('work/horaz_development_20260922/source44_manifest.json').open() as f:
            self.manifest=json.load(f)
        with Path('work/horaz_development_20260922/pilot_plan.json').open() as f:
            pilot=json.load(f)
        self.plan=dict(experiment='EXP230',purpose='warmstart_source_only_feasibility',
                       source_embryo='44b6',target_embryo='6bba',fold=1,parent_sha256=PARENT_SHA,
                       parent_epoch=20,learning_rate=0.00002,epochs=2,iterations_per_epoch=8,
                       seed=3407,resume=False,checkpoint_selection='none_feasibility_only',
                       num_workers=0,torch_compile=False,train=pilot['train'],
                       inner_validation=pilot['inner_validation'])

    def test_exact_source_subset(self):
        validate(self.plan,self.manifest)

    def test_target_or_wrong_source_denied(self):
        for changed in ['target','path','duplicate','learning_rate']:
            p=copy.deepcopy(self.plan)
            if changed=='target':p['train'][0]['dataset_id']='6bba_fake'
            if changed=='path':p['train'][0]['zarr_path']='/tmp/44b6_fake.zarr'
            if changed=='duplicate':p['inner_validation'][0]=p['train'][0]
            if changed=='learning_rate':p['learning_rate']=0.0001
            with self.subTest(changed=changed),self.assertRaises((AssertionError,KeyError)):
                validate(p,self.manifest)

    def test_only_exact_parent_checkpoint_allowed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'source').mkdir();(root/'out').mkdir()
            parent=root/'fold1_selected.pt';parent.write_bytes(b'parent')
            guard=WarmstartGuard([],root/'out',root/'source',parent)
            guard.check(parent)
            guard.check(root/'out'/'last.pt')
            with self.assertRaises(PermissionError):guard.check(root/'other.pt')


if __name__=='__main__':unittest.main()
