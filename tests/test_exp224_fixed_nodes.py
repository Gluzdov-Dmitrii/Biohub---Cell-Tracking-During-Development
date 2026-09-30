import sys,unittest,pathlib,tempfile
sys.path.insert(0,'scripts')
import run_exp224_fixed_nodes as m
class FixedNodes(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=pathlib.Path('kaggle_notebooks/exp002_rule_based/biohub-rule-based-baseline.py')
  cls.mod=m.load_classical(p,m.sha(p))
 def relink(self,nodes):
  frames,forward=m.to_frames(nodes,4);self.mod.SCALE=m.np.array([2.,.5,.5])
  g=m.tg_to_graph(self.mod.link_frames(frames,max_link_um=8.,allow_divisions=False))
  return m.remap_graph(g['nodes'],g['edges'],{v:k for k,v in forward.items()})
 def test_anisotropy_and_original_ids(self):
  nodes={91:(0,0.,0.,0.),42:(1,0.,0.,10.),711:(1,5.,0.,0.)}
  g=self.relink(nodes);self.assertEqual(g['nodes'],nodes);self.assertEqual(g['edges'],[(91,42)])
 def test_no_gap_and_keep_isolates(self):
  nodes={27:(0,1.25,2.5,3.75),400:(2,1.25,2.5,3.75)}
  g=self.relink(nodes);self.assertEqual(g['nodes'],nodes);self.assertEqual(g['edges'],[])
 def test_one_to_one_no_division(self):
  nodes={9:(0,0.,0.,0.),33:(1,0.,0.,1.),66:(1,0.,0.,2.)}
  g=self.relink(nodes);self.assertEqual(g['nodes'],nodes);self.assertEqual(len(g['edges']),1)
 def test_csv_fractional_roundtrip(self):
  import score_exp214_paired as reader
  nodes={27:(0,1.123456789012345,2.5,3.75),400:(1,1.25,2.5,3.75)};g=self.relink(nodes)
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'x.csv';m.write_csv(p,['44b6_test'],{'44b6_test':g})
   self.assertEqual(reader.read_graphs(p)['44b6_test'],g)
unittest.main()
