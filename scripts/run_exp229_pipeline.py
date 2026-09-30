"""Produce all frozen-node predictions, replay Horaz, then score one fixed policy.

The producer runs in a separate process with a permanent label-access guard.
Only after every CSV and receipt passes does this process import the scorer.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, obj):
    path = Path(path)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(obj, indent=2)+'\n')
    temporary.replace(path)


def gate_predictions(config, complete):
    assert complete['status'] == 'PASS_ALL_175_PREDICTIONS_BEFORE_LABELS'
    assert complete['completed'] == 175 and len(complete['records']) == 175
    rows = {r['dataset']: r for r in config['rows']}
    records = {r['dataset']: r for r in complete['records']}
    assert len(rows) == 175 and rows.keys() == records.keys()
    out = Path(config['output_dir']).resolve()
    for name, row in rows.items():
        record = records[name]
        assert record['fold'] == (0 if name.startswith('44b6_') else 1)
        assert record['arm'] == 'selected50_20' and record['mode'] == 'heldout'
        assert record['shape'] == row['shape']
        assert sha(row['reference_csv']) == row['reference_sha256'] == record['input_sha256']
        assert sha(row['receipt_path']) == row['receipt_sha256'] == record['receipt_sha256']
        assert record['input_csv'] == row['reference_csv']
        csv = out / ('physical__'+name+'.csv')
        assert Path(record['output_csv']).resolve() == csv
        assert sha(csv) == record['output_sha256']
        assert json.loads((out/'receipts'/(name+'.json')).read_text()) == record
        assert record['candidate_counts']['nodes'] == record['reference_counts']['nodes']
    assert {p.name for p in out.glob('*.csv')} == {'physical__'+n+'.csv' for n in rows}
    return rows, records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', type=Path, required=True)
    ap.add_argument('--config-sha256', required=True)
    args = ap.parse_args()
    assert sha(args.config) == args.config_sha256
    cfg = json.loads(args.config.read_text())
    code = Path(__file__).resolve().parent
    for name, digest in json.loads((code/'code_manifest.json').read_text()).items():
        assert sha(code/name) == digest, name
    out = Path(cfg['output_dir'])
    out.mkdir(exist_ok=False)
    started = time.time()
    assert sha(cfg['producer_config']) == cfg['producer_config_sha256']
    pcfg = json.loads(Path(cfg['producer_config']).read_text())
    subprocess.run([sys.executable, str(code/'run_exp229_fixed_nodes.py'), '--config', cfg['producer_config'],
                    '--config-sha256', cfg['producer_config_sha256']], check=True)
    completion_path = Path(pcfg['output_dir'])/'complete.json'
    complete = json.loads(completion_path.read_text())
    assert complete['provenance']['config_sha256'] == cfg['producer_config_sha256']
    rows, records = gate_predictions(pcfg, complete)
    save(out/'no_metric_gate.json', {'status':'PASS_ALL_175_PREDICTIONS_BEFORE_LABELS',
         'complete_sha256':sha(completion_path), 'n_movies':175, 'at':time.time()})
    # No producer module import here: its audit hook must remain active only in
    # the producer subprocess. The official scorer intentionally opens GEFF now.
    import score_exp223_official as score
    score.evaluator_pins(cfg)
    score.must_sha(cfg['analyze_path'],cfg['analyze_sha256'],'graph reader')
    score.must_sha(cfg['baseline_result_path'],cfg['baseline_result_sha256'],'Horaz baseline')
    analyze = score.load_mod(cfg['analyze_path'],'exp229_graph_reader')
    frozen = json.loads(Path(cfg['baseline_result_path']).read_text())
    expected = {r['dataset']:r for r in frozen['rows']['selected50_20']}
    assert expected.keys() == rows.keys()
    sys.path[:0] = [cfg['repo_path']+'/src',cfg['repo_path']+'/scripts']
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate,node_recall,per_sample_metrics,summarise
    from geff import GeffMetadata
    from predict_unet_transformer import build_graph
    results = {'reference':[], 'physical':[]}
    for arm in ('reference','physical'):
        for index, name in enumerate(sorted(rows), 1):
            row = rows[name]
            csv = row['reference_csv'] if arm == 'reference' else records[name]['output_csv']
            graph = analyze.read_graphs(Path(csv))[name]
            if arm == 'physical':
                reference = analyze.read_graphs(Path(row['reference_csv']))[name]
                assert graph['nodes'] == reference['nodes'], 'Node lock failed before scoring'
                del reference
            ds = open_dataset(row['zarr'],require_tracks=True,load_image=False)
            estimate = (GeffMetadata.read(str(Path(cfg['data_path'])/(name+'.geff'))).extra or {})['estimated_number_of_nodes']
            result = score.score_one(name,graph,ds,estimate,evaluate,node_recall,per_sample_metrics,build_graph)
            if arm == 'reference':score.rows_close(result,expected[name])
            results[arm].append(result)
            save(out/'progress.json', {'phase':arm,'done':index,'total':175,'dataset':name})
            if index % 10 == 0:print(json.dumps({'phase':arm,'done':index}),flush=True)
            del graph,ds
        if arm == 'reference':
            score.rows_close(summarise(results[arm]),frozen['summary']['selected50_20'])
            save(out/'baseline_replay.json',{'status':'PASS_ALL_175_ROWS_1e-12','summary':summarise(results[arm])})
    result = {'status':'PASS_EXP229_FIXED_NODE_OFFICIAL175','elapsed_seconds':time.time()-started,
              'baseline_replay':'PASS_ALL_175_ROWS_1e-12', 'rows':results,
              'summary':{a:summarise(r) for a,r in results.items()},
              'summary_by_embryo':{a:score.by_embryo(r,summarise) for a,r in results.items()},
              'producer_complete_sha256':sha(completion_path),
              'note':'Fixed hypothesis; selected checkpoints retain historical outer-fold selection bias. Two embryos, development-adapted.'}
    save(out/'result.json',result)
    print(json.dumps({'status':result['status'],'summary':result['summary']}),flush=True)


if __name__ == '__main__':main()
