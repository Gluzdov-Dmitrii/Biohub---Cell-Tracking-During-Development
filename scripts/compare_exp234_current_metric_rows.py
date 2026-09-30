"""Pin a read-only row comparison between current and historical metrics."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh


ROOT = Path(__file__).resolve().parents[1]
VERIFIED = ROOT / "reports/exp234_current_organizer_score_verified_20260927.json"
PREPARE = ROOT / "reports/exp234_current_organizer_prepare_20260927.json"
RECEIPT = ROOT / "reports/exp234_current_metric_row_compare_20260927.json"
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not RECEIPT.exists(), "Row comparison receipt already exists"
    verified = json.loads(VERIFIED.read_text())
    prepared = json.loads(PREPARE.read_text())
    assert verified["status"] == "VERIFIED_EXP234_TARGET175_CURRENT_ORGANIZER_METRIC_PAIRED"
    source = r'''import hashlib,json,pathlib
root=pathlib.Path(@@ROOT@@)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
current=root/'runs/exp234_current_organizer_score175_v1_20260927/output/result.json'
historical=root/'runs/exp234_target_official_score175_20260927/output/result.json'
baseline=root/'runs/exp214_gapfix_score175_20260914/output/new90/metrics.json'
assert sha(current)==@@CURRENT_SHA@@ and sha(historical)==@@HISTORICAL_SHA@@
assert sha(baseline)=='c2746b182d061fede4a255056cf177a245ad365485f46ba9f376cd240013b2e5'
new=json.loads(current.read_text());old=json.loads(historical.read_text())
base=json.loads(baseline.read_text())['rows']['public']
def indexed(rows):
 result={row['dataset']:row for row in rows}
 assert len(result)==len(rows)==175
 return result
old_candidate=indexed(old['rows']);new_candidate=indexed(new['candidate_rows'])
old_baseline=indexed(base);new_baseline=indexed(new['baseline_rows'])
assert old_candidate==new_candidate and old_baseline==new_baseline
assert old['candidate_summary']==new['candidate_summary']
print(json.dumps({'status':'PASS_EXP234_CURRENT_METRIC_ROWS_IDENTICAL_ON_SEALED175',
 'current_result_sha256':sha(current),'historical_result_sha256':sha(historical),
 'historical_baseline_metrics_sha256':sha(baseline),
 'candidate_rows_identical':175,'baseline_rows_identical':175,
 'changed_row_fields':0,'score':new['candidate_summary']['score'],
 'baseline':new['baseline_summary']['score'],
 'candidate_division_totals':{key:sum(row[key] for row in new_candidate.values())
  for key in ('division_tp','division_fp','division_fn')},
 'baseline_division_totals':{key:sum(row[key] for row in new_baseline.values())
  for key in ('division_tp','division_fp','division_fn')},
 'target_labels_read_for_comparison':False,'kaggle_post':False}))
'''.replace("@@ROOT@@", repr(REMOTE)).replace(
        "@@CURRENT_SHA@@", repr(verified["verification"]["result_sha256"])).replace(
        "@@HISTORICAL_SHA@@", repr(prepared["historical_result_sha256"]))
    comparison = ssh("nsu-quadro", "python3 -", source)
    assert comparison["status"] == "PASS_EXP234_CURRENT_METRIC_ROWS_IDENTICAL_ON_SEALED175"
    assert comparison["candidate_rows_identical"] == comparison["baseline_rows_identical"] == 175
    assert comparison["changed_row_fields"] == 0
    receipt = {**comparison, "verified_receipt_sha256": sha(VERIFIED),
               "prepare_receipt_sha256": sha(PREPARE)}
    RECEIPT.write_bytes((json.dumps(receipt, indent=2) + "\n").encode())
    print(json.dumps({"status": receipt["status"], "score": receipt["score"],
                      "receipt_sha256": sha(RECEIPT)}))


if __name__ == "__main__":
    main()
