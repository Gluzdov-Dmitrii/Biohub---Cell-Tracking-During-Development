"""Exact EXP002 inference, then official paired four-movie diagnostic."""
import hashlib
import importlib.util
import csv
import json
from pathlib import Path
import sys
import time

ROOT = Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
RUN = Path(__file__).resolve().parent
DATA = ROOT / 'data/exp213_source_view_20260912'
REPO = ROOT / 'code/exp214_honest_refit_v4_20260912/tracking_repo'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    start = time.time()
    spec = json.loads((RUN / 'preregistration.json').read_text())
    source = RUN / 'exp002_exact.py'
    assert sha(source) == spec['source_sha256']
    module_spec = importlib.util.spec_from_file_location('exp002_exact', source)
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    # Packaging-only adaptation: pandas is used only by original CSV writer.
    text = source.read_text()
    assert text.count('import pandas as pd\n') == 1
    exec(compile(text.replace('import pandas as pd\n', ''), str(source), 'exec'), module.__dict__)
    cfg = module.Config(**module.CONFIG_OVERRIDE)
    rows = []
    timing = []
    for name in spec['movies']:
        t0 = time.time()
        graph = module.run_one(str(DATA / (name + '.zarr')), cfg)
        rows.extend(module.graph_to_rows(name, graph))
        timing.append({'dataset': name, 'seconds': time.time()-t0, 'nodes': graph.n_nodes, 'edges': graph.n_edges})
        print(json.dumps(timing[-1]), flush=True)
    csv_path = RUN / 'predictions.csv'
    columns = ['id','dataset','row_type','node_id','t','z','y','x','source_id','target_id']
    with csv_path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row_id, row in enumerate(rows):
            writer.writerow({'id':row_id, **row})
    from analyze_submission_edge_failure_modes import read_graphs, merge_verified_csv_graphs
    predictions = read_graphs(csv_path)
    assert set(predictions) == set(spec['movies'])
    import zarr
    for name, graph in predictions.items():
        shape = zarr.open_group(str(DATA / (name+'.zarr')), mode='r')['0'].shape
        assert all(all(0 <= v < s for v,s in zip(point,shape)) for point in graph['nodes'].values())
    gate = {'status':'PASS_ALL_PREDICTIONS_BEFORE_LABEL_ACCESS','movies':spec['movies'],'prediction_sha256':sha(csv_path),'timing':timing,'source_sha256':sha(source)}
    (RUN/'no_metric_gate.json').write_text(json.dumps(gate,indent=2)+'\n')
    # Only after the complete no-label inference gate open ground truth/scoring.
    sys.path[:0] = [str(REPO/'src'), str(REPO/'scripts')]
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph
    import numpy as np
    baseline_path = ROOT/'runs/exp214_gapfix_score175_20260914/output/new90/metrics.json'
    frozen = json.loads(baseline_path.read_text())
    baseline, baseline_manifest = merge_verified_csv_graphs(frozen, 'public')
    frozen_rows = {r['dataset']:r for r in frozen['rows']['public']}
    result_rows = {'classical':[], 'exp214':[]}
    for name in spec['movies']:
        ds = open_dataset(DATA/(name+'.zarr'), require_tracks=True, load_image=False)
        estimate = (GeffMetadata.read(DATA/(name+'.geff')).extra or {})['estimated_number_of_nodes']
        for arm, graphs in [('classical',predictions),('exp214',baseline)]:
            g = graphs[name]
            ids = sorted(g['nodes']); indices = {n:i for i,n in enumerate(ids)}
            points = np.asarray([g['nodes'][n] for n in ids],dtype=float).reshape(-1,4)
            edges = [(indices[s],indices[t],1.,0.) for s,t in g['edges']]
            graph = build_graph(points,edges)
            metric = evaluate(graph,ds.tracks,scale=ds.scale)
            recall = node_recall(graph,ds.tracks) if graph.num_nodes() and graph.num_edges() else 0.
            if arm == 'exp214':
                for key in ('edge_tp','edge_fp','edge_fn'):
                    assert int(getattr(metric,key)) == int(frozen_rows[name][key])
            result_rows[arm].append({'dataset':name, **per_sample_metrics(metric,float(estimate),recall)})
        print(json.dumps({'scored':name}),flush=True)
    result = {'status':'PASS_FIXED_CLASSICAL_FULL175_BENCHMARK' if len(spec['movies'])==175 else 'PASS_FIXED_CLASSICAL_FOUR_MOVIE_DIAGNOSTIC','scope':spec['scope'],'elapsed_seconds':time.time()-start,'rows':result_rows,'summary':{arm:summarise(rows) for arm,rows in result_rows.items()},'baseline_manifest':baseline_manifest,'prediction_sha256':sha(csv_path),'source_sha256':sha(source),'no_metric_gate_sha256':sha(RUN/'no_metric_gate.json')}
    (RUN/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'elapsed_seconds':result['elapsed_seconds'],'summary':result['summary']}),flush=True)


if __name__ == '__main__':
    main()
