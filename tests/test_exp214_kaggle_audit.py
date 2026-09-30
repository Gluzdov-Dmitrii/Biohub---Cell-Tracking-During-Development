import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import pytest

spec=importlib.util.spec_from_file_location('exp214_audit',Path(__file__).parents[1]/'scripts/audit_exp214_kaggle_output.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


def fixture(tmp_path,family):
    path=tmp_path/'submission.csv'
    with path.open('w',newline='') as f:
        w=csv.writer(f);w.writerow(audit.COLUMNS)
        for i,t in enumerate((0,1,1)):w.writerow([i,'synthetic','node',i,t,1.5,2.,3.,-1,-1])
        for i,t in enumerate((1,2),3):w.writerow([i,'synthetic','edge',-1,-1,-1,-1,-1,0,t])
    receipt={'status':'PASS_FULL_INFERENCE','graph_family':family,'runtime_datasets':['synthetic'],
             'rows':5,'submission_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    (tmp_path/'exp214_runtime_receipt.json').write_text(json.dumps(receipt))


def test_public_division_is_valid(tmp_path,monkeypatch):
    fixture(tmp_path,'public');out=tmp_path/'audit.json'
    monkeypatch.setattr(sys,'argv',['audit',str(tmp_path),'--receipt',str(out)])
    audit.main();assert json.loads(out.read_text())['maximum_out_degree']==2


def test_local_division_is_policy_violation(tmp_path,monkeypatch):
    fixture(tmp_path,'local');monkeypatch.setattr(sys,'argv',['audit',str(tmp_path),'--receipt',str(tmp_path/'audit.json')])
    with pytest.raises(AssertionError):audit.main()


def test_nested_submission_blocks_audit(tmp_path,monkeypatch):
    fixture(tmp_path,'public');(tmp_path/'nested').mkdir();(tmp_path/'nested/submission.csv').write_text('duplicate')
    monkeypatch.setattr(sys,'argv',['audit',str(tmp_path),'--receipt',str(tmp_path/'audit.json')])
    with pytest.raises(AssertionError):audit.main()
