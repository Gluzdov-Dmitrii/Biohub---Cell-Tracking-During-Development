import sys,unittest,tempfile,json,pathlib,csv
sys.path.insert(0,'scripts');from run_exp223_inference import validate_rows,route,sha,resume_receipt,atomic_json
class Gates(unittest.TestCase):
 def rows(self):return [dict(id='0',dataset='44b6_x',row_type='node',node_id='0',t='0',z='0',y='0',x='0'),dict(id='1',dataset='44b6_x',row_type='node',node_id='1',t='1',z='0',y='0',x='0'),dict(id='2',dataset='44b6_x',row_type='edge',source_id='0',target_id='1')]
 def test_valid(self):self.assertEqual(validate_rows(self.rows(),[2,1,1,1],'44b6_x')['edges'],1)
 def test_bounds(self):
  r=self.rows();r[0]['z']='1'
  with self.assertRaises(AssertionError):validate_rows(r,[2,1,1,1],'44b6_x')
 def test_skip(self):
  r=self.rows();r[1]['t']='2'
  with self.assertRaises(AssertionError):validate_rows(r,[3,1,1,1],'44b6_x')
 def test_duplicate(self):
  r=self.rows();r.append(dict(r[-1],id='3'))
  with self.assertRaises(AssertionError):validate_rows(r,[2,1,1,1],'44b6_x')
 def test_route(self):
  self.assertEqual(route({'dataset':'44b6_x','fold':0}),0);self.assertEqual(route({'dataset':'44b6_x','fold':0},True),1)
  with self.assertRaises(AssertionError):route({'dataset':'6bba_x','fold':0})
 def test_tamper(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'x';p.write_text('a');digest=sha(p);p.write_text('b');self.assertNotEqual(digest,sha(p))
 def test_resume_and_corruption(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'movie.csv';r=pathlib.Path(d)/'receipt.json';rows=self.rows()
   fields=['id','dataset','row_type','node_id','t','z','y','x','source_id','target_id']
   with p.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
   contract={'fold':0};record={'contract':contract,'csv_sha256':sha(p)};atomic_json(r,record)
   row={'shape':[2,1,1,1],'dataset':'44b6_x'}
   self.assertEqual(resume_receipt(r,p,contract,row),record)
   with self.assertRaises(AssertionError):resume_receipt(r,p,{'fold':1},row)
   p.write_text(p.read_text()+'\n')
   with self.assertRaises(AssertionError):resume_receipt(r,p,contract,row)
unittest.main()
