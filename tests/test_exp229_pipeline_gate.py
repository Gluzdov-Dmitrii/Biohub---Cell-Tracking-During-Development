"""Reject partial/tampered prediction sets before permitting any label access."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_exp229_pipeline import gate_predictions,sha


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        out=self.root/'out';out.mkdir();(out/'receipts').mkdir()
        rows=[];records=[]
        for i in range(175):
            name=('44b6_' if i<59 else '6bba_')+str(i)
            ref=self.root/(name+'.csv');ref.write_text('node\n')
            receipt=self.root/(name+'.json');receipt.write_text('{}')
            candidate=out/('physical__'+name+'.csv');candidate.write_text('node\nedge\n')
            row={'dataset':name,'shape':[2,8,8,8],'reference_csv':str(ref),'reference_sha256':sha(ref),
                 'receipt_path':str(receipt),'receipt_sha256':sha(receipt)}
            record={'dataset':name,'fold':0 if i<59 else 1,'arm':'selected50_20','mode':'heldout',
                    'shape':row['shape'],'input_csv':str(ref),'input_sha256':sha(ref),'receipt_sha256':sha(receipt),
                    'output_csv':str(candidate),'output_sha256':sha(candidate),
                    'candidate_counts':{'nodes':2},'reference_counts':{'nodes':2}}
            (out/'receipts'/(name+'.json')).write_text(json.dumps(record))
            rows.append(row);records.append(record)
        self.config={'rows':rows,'output_dir':str(out)}
        self.complete={'status':'PASS_ALL_175_PREDICTIONS_BEFORE_LABELS','completed':175,'records':records}

    def test_complete_set(self):
        self.assertEqual(len(gate_predictions(self.config,self.complete)[0]),175)

    def test_partial_or_duplicate_set(self):
        for records in (self.complete['records'][:-1],self.complete['records'][:-1]+[self.complete['records'][0]]):
            bad=copy.deepcopy(self.complete);bad['records']=records
            with self.assertRaises(AssertionError):gate_predictions(self.config,bad)

    def test_changed_csv(self):
        Path(self.complete['records'][0]['output_csv']).write_text('changed')
        with self.assertRaises(AssertionError):gate_predictions(self.config,self.complete)

    def test_changed_receipt(self):
        (Path(self.config['output_dir'])/'receipts'/('44b6_0.json')).write_text('{}')
        with self.assertRaises(AssertionError):gate_predictions(self.config,self.complete)

    def test_changed_reference(self):
        Path(self.config['rows'][0]['reference_csv']).write_text('changed')
        with self.assertRaises(AssertionError):gate_predictions(self.config,self.complete)


if __name__=='__main__':unittest.main()
