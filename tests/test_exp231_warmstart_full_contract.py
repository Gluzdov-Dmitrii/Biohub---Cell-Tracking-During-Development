"""Full source manifest and fixed schedule gates for EXP231."""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_exp231_warmstart_full import PARENT_SHA,validate


class FullWarmstartContract(unittest.TestCase):
    def setUp(self):
        self.manifest=json.loads(Path('work/horaz_development_20260922/source44_manifest.json').read_text())
        self.plan=dict(experiment='EXP231',purpose='warmstart_source_only_full2',
                       source_embryo='44b6',target_embryo='6bba',fold=1,parent_sha256=PARENT_SHA,
                       parent_epoch=20,learning_rate=0.00002,epochs=2,iterations_per_epoch=None,
                       seed=3407,resume=False,checkpoint_selection='fixed_epoch2_no_outer_selection',
                       num_workers=0,torch_compile=False,train=self.manifest['train'],
                       inner_validation=self.manifest['inner_validation'])

    def test_exact_full_partition(self):
        validate(self.plan,self.manifest)

    def test_rejects_sample_cap_or_partial_source(self):
        for change in ('cap','partial','swap','target','lr'):
            plan=copy.deepcopy(self.plan)
            if change=='cap':plan['iterations_per_epoch']=8
            elif change=='partial':plan['train']=plan['train'][:-1]
            elif change=='swap':plan['train'][0],plan['train'][1]=plan['train'][1],plan['train'][0]
            elif change=='target':plan['train'][0]['dataset_id']='6bba_fake'
            elif change=='lr':plan['learning_rate']=0.0001
            with self.subTest(change=change),self.assertRaises(AssertionError):
                validate(plan,self.manifest)


if __name__=='__main__':unittest.main()
