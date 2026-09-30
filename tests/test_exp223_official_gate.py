import sys,json,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'scripts'))
import score_exp223_official as s
import analyze_submission_edge_failure_modes as analyze
class FullGate(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.code=self.root/'code';self.code.mkdir();files={}
  for name in ['selected/resolved_config.json','selected/fold0_selected.pt','selected/fold1_selected.pt','fixed_last/fold0_last.pt','fixed_last/fold1_last.pt']:
   p=self.code/name;p.parent.mkdir(exist_ok=True);p.write_text(name);files[name]=s.sha(p)
  self.put(self.code/'code_manifest.json',files);self.codehash=s.sha(self.code/'code_manifest.json')
  self.rows=[{'dataset':('44b6_' if i<59 else '6bba_')+str(i),'fold':0 if i<59 else 1,'shape':[2,4,4,4]} for i in range(175)]
  cp=self.root/'cohort.json';self.put(cp,{'rows':self.rows});self.cohash=s.sha(cp);chunks=[];self.receipts=[]
  for n in range(8):
   run=self.root/f'run{n}';out=run/'output';out.mkdir(parents=True);(run/'supervision').mkdir();subset=self.rows[n::8]
   ex={'returncode':0,'hard_timeout':False,'pid':123,'start':'1'};self.put(run/'exit.json',ex);self.put(run/'supervision/complete.json',{'status':'RELEASED_AFTER_VERIFIED_EXIT','exit':ex});self.put(run/'supervision/control.json',{'action':'release','queue':{'state':'RELEASED','run_path':str(run)}})
   records=[]
   for arm in s.ARMS:
    for row in subset:
     ds=row['dataset'];fold=row['fold'];csvp=out/f'{arm}__{ds}.csv';s.write_mini_csv(csvp,ds)
     folder,suffix=('selected','selected') if arm==s.ARMS[0] else ('fixed_last','last')
     contract={'arm':arm,'dataset':ds,'fold':fold,'mode':'heldout','weight_sha256':s.sha(self.code/folder/f'fold{fold}_{suffix}.pt'),'manifest_sha256':self.cohash,'decoder_sha256':s.sha(self.code/'selected/resolved_config.json'),'code_sha256':self.codehash}
     rec={'contract':contract,'csv_sha256':s.sha(csvp),'shape':row['shape']};rp=csvp.with_suffix('.json');self.put(rp,rec);self.receipts.append(rp);records.append(rec)
   self.put(out/'complete.json',{'status':'PASS_NO_LABEL_CHUNK','mode':'heldout','records':records})
   pp=self.root/f'plan{n}.json';self.put(pp,{'code':str(self.code),'code_manifest_sha256':self.codehash,'manifest_sha256':self.cohash,'mode':'heldout','arms':list(s.ARMS),'movies':[r['dataset'] for r in subset],'output':str(out)})
   chunks.append({'plan':str(pp),'sha256':s.sha(pp),'run':str(run),'n_movies':len(subset)})
  rp=self.root/'rollout.json';self.put(rp,{'chunks':chunks});self.cfg={'code_path':str(self.code),'code_manifest_sha256':self.codehash,'cohort_path':str(cp),'cohort_sha256':self.cohash,'rollout_path':str(rp),'rollout_sha256':s.sha(rp)}
 def tearDown(self):self.temp.cleanup()
 def put(self,p,x):p.write_text(json.dumps(x))
 def gate(self):return s.gate_all(self.cfg,analyze)
 def test_complete175(self):self.assertEqual(sum(map(len,self.gate()[0].values())),350)
 def test_missing_last_arm(self):
  self.receipts[-1].unlink()
  with self.assertRaises(SystemExit):self.gate()
 def test_wrong_fold(self):
  p=self.receipts[-1];r=json.loads(p.read_text());r['contract']['fold']=1-r['contract']['fold'];self.put(p,r)
  with self.assertRaisesRegex(SystemExit,'fold leak'):self.gate()
 def test_code_tamper(self):
  (self.code/'selected/resolved_config.json').write_text('changed')
  with self.assertRaisesRegex(SystemExit,'sha mismatch'):self.gate()
 def test_weight_tamper(self):
  p=self.receipts[-1];r=json.loads(p.read_text());r['contract']['weight_sha256']='fake';self.put(p,r)
  with self.assertRaisesRegex(SystemExit,'weight sha'):self.gate()
 def test_not_released(self):
  p=self.root/'run7/supervision/control.json';r=json.loads(p.read_text());r['queue']['state']='RUNNING';self.put(p,r)
  with self.assertRaisesRegex(SystemExit,'not wrapper_exit0'):self.gate()
 def test_extra_output(self):
  (self.root/'run0/output/extra.csv').write_text('')
  with self.assertRaisesRegex(SystemExit,'extra/missing'):self.gate()
if __name__=='__main__':unittest.main()
