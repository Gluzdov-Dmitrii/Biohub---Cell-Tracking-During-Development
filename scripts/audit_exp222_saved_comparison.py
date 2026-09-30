"""Local JSON/source audit only. Does not execute detector or scorer code."""
import ast
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/research/exp222_classical_full175_20260921'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    result = json.loads((OUT/'result.json').read_text())
    receipt = json.loads((ROOT/'reports/exp222_full175_status_20260921.json').read_text())
    prereg = json.loads((OUT/'preregistration.json').read_text())
    gate = json.loads((OUT/'no_metric_gate.json').read_text())
    baseline_path = ROOT/'outputs/research/exp214_gapfix_score175_20260914/output/new90/metrics.json'
    baseline = json.loads(baseline_path.read_text())
    checks = {}
    checks['completed_and_stopped'] = result['status']=='PASS_FIXED_CLASSICAL_FULL175_BENCHMARK' and receipt['live_process_group']==[]
    checks['all_export_hashes'] = all(digest(OUT/name)==value for name,value in receipt['sha256'].items())
    source = ROOT/'kaggle_notebooks/exp002_rule_based/biohub-rule-based-baseline.py'
    checks['classical_source_identity'] = digest(source)==result['source_sha256']==prereg['source_sha256']==gate['source_sha256']
    checks['gate_hash'] = digest(OUT/'no_metric_gate.json')==result['no_metric_gate_sha256']
    checks['prediction_hash_consistent_receipts'] = result['prediction_sha256']==gate['prediction_sha256']
    names = sorted(prereg['movies'])
    checks['exact_175_cohort'] = len(names)==175 and len(set(names))==175 and names==sorted(gate['movies'])==sorted(r['dataset'] for r in gate['timing'])==sorted(r['dataset'] for r in baseline['rows']['public'])
    checks['both_arms_exact_cohort'] = all(sorted(r['dataset'] for r in rr)==names for rr in result['rows'].values())
    old = {r['dataset']:r for r in baseline['rows']['public']}
    mismatches = []
    for row in result['rows']['exp214']:
        for key,value in row.items():
            other = old[row['dataset']].get(key)
            equal = math.isclose(value,other,abs_tol=1e-12,rel_tol=0) if isinstance(value,float) else value==other
            if not equal:mismatches.append([row['dataset'],key,value,other])
    checks['all_baseline_per_movie_fields_match'] = not mismatches
    checks['baseline_csv_manifest_match'] = [(r['csv'],r['sha256']) for r in result['baseline_manifest']]==[(r['csv'],r['sha256']) for r in baseline['input_hashes']['public']]
    source_tree = ast.parse(source.read_text())
    cfg_class = next(n for n in source_tree.body if isinstance(n,ast.ClassDef) and n.name=='Config')
    cfg = {n.target.id:ast.literal_eval(n.value) for n in cfg_class.body if isinstance(n,ast.AnnAssign)}
    overrides = next(ast.literal_eval(n.value) for n in source_tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CONFIG_OVERRIDE' for t in n.targets))
    cfg.update(overrides)
    checks['fixed_classical_configuration'] = cfg['detector']=='blob' and cfg['linker']=='hungarian' and cfg['dog_scales']==[[1.5,4.0],[2.2,5.5]] and cfg['max_link_um']==8.0 and cfg['close_gaps'] is True and cfg['max_gap']==1 and cfg['gap_dist_um']==6.0
    wrapper = ROOT/'scripts/run_exp222_classical_pilot.py'
    text = wrapper.read_text()
    checks['local_wrapper_gate_precedes_gt_access'] = text.index("(RUN/'no_metric_gate.json').write_text") < text.index('require_tracks=True')
    checks['local_wrapper_fixed_cfg_and_shared_evaluator'] = 'module.Config(**module.CONFIG_OVERRIDE)' in text and "for arm, graphs in [('classical',predictions),('exp214',baseline)]" in text and 'metric = evaluate(graph,ds.tracks,scale=ds.scale)' in text
    scores = {}
    for arm,rows in result['rows'].items():
        den = sum(r['edge_tp']+r['edge_fp']+r['edge_fn'] for r in rows)
        edge = sum((r['edge_tp']+r['edge_fp']+r['edge_fn'])*r['adj_edge_jaccard'] for r in rows)/den
        dt = sum(r['division_tp'] for r in rows)
        dd = sum(r['division_tp']+r['division_fp']+r['division_fn'] for r in rows)
        scores[arm] = edge+0.1*(dt/dd if dd else 0)
    checks['official_aggregation_reproduces_scores'] = all(abs(scores[k]-result['summary'][k]['score'])<1e-12 for k in scores)
    output = {'status':'PASS_SAVED_COMPARISON_WITH_PROVENANCE_LIMITS' if all(checks.values()) else 'FAIL_SAVED_COMPARISON', 'checks':checks,'scores':scores,'delta_classical_minus_exp214':scores['classical']-scores['exp214'],'effective_classical_config':cfg,'source_sha256':digest(source),'local_wrapper_sha256':digest(wrapper),'baseline_metrics_sha256':digest(baseline_path),'result_sha256':digest(OUT/'result.json'),'cohort_by_embryo':{p:sum(n.startswith(p+'_') for n in names) for p in ['44b6','6bba']},'mismatches':mismatches,'evidence_limits':['Exact runtime evaluator source SHA and remote wrapper SHA were not saved in the exported completion receipt; same code path is evidenced by local launcher/wrapper and exact baseline replay, not independently proven byte identity.','Full prediction CSV remains remote; this audit checks agreement of recorded CSV hashes, not a new hash of CSV bytes.','No learned parameters or target-label fitting in EXP222; image-dependent intensity normalization is inference preprocessing. Historical classical parameter-selection provenance before EXP002 remains incomplete.','This175movie cohort has been reused for development. Correct label gating does not make it a pristine independent final test.','Training-fold OOF terminology applies to EXP214 learned checkpoints, not a nontrained classical algorithm. EXP222 is a fixed classical same-cohort heldout benchmark.']}
    (ROOT/'reports/exp222_saved_comparison_audit_20260921.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'status':output['status'],'checks':checks,'scores':scores,'config':cfg},indent=2))
    assert all(checks.values()), output


if __name__=='__main__':
    run()
