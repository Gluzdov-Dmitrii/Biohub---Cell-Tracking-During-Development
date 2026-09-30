import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_exp228_ensemble import WEIGHTS,validate_plan


class EnsembleContract(unittest.TestCase):
    def setUp(self):
        self.plan={'experiment':'EXP228','mode':'heldout_same_fold_ensemble','weights':dict(WEIGHTS),
                   'mixture':[.5,.5],'chunk':0,'rows':[{'dataset':f'6bba_{i:08x}','fold':1,
                   'zarr':f'/data/6bba_{i:08x}.zarr','shape':[100,64,256,256]} for i in range(29)]}
    def test_fixed_candidate_valid(self):
        validate_plan(self.plan)
    def test_smaller_quadro_partition_valid(self):
        self.plan['chunk_count']=8
        self.plan['rows']=self.plan['rows'][:15]
        validate_plan(self.plan)
    def test_opposite_fold_or_weight_sweep_rejected(self):
        for key,value in [('mixture',[.75,.25]),('weights',{'selected/fold0_selected.pt':'bad'}),('mode','all_train')]:
            p=copy.deepcopy(self.plan);p[key]=value
            with self.subTest(key=key),self.assertRaises(AssertionError):validate_plan(p)
    def test_target_routing_and_path_rejected(self):
        for key,value in [('fold',0),('dataset','44b6_00000000'),('zarr','/data/44b6_00000000.zarr')]:
            p=copy.deepcopy(self.plan);p['rows'][0][key]=value
            with self.subTest(key=key),self.assertRaises(AssertionError):validate_plan(p)
    def test_missing_or_duplicate_movies_rejected(self):
        p=copy.deepcopy(self.plan);p['rows'][0]=p['rows'][1]
        with self.assertRaises(AssertionError):validate_plan(p)
        self.plan['rows'].pop()
        with self.assertRaises(AssertionError):validate_plan(self.plan)


if __name__=='__main__':unittest.main()
