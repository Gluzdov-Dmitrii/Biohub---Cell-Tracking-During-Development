"""Quantify one preserved raw boundary coordinate after the full strict CV gate."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
RUN = ROOT / 'runs/exp214_final_cpu_scoring_v2_20260912'
REPAIR = ROOT / 'runs/exp214_spatial_serialization_repair_20260912'
CODE = ROOT / 'code/exp214_inference_v6_20260912'
REPO = ROOT / 'code/exp214_honest_refit_v4_20260912/tracking_repo'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    gate = json.loads((RUN / 'paired175/no_metric_gate.json').read_text())
    assert gate['status'] == 'PASS_ALL_ARMS_COMPLETE_BEFORE_LABEL_ACCESS' and len(gate['movies']) == 175
    metrics_path = RUN / 'paired175/metrics.json'
    metrics = json.loads(metrics_path.read_text())
    assert metrics['status'] == 'PASS_HONEST_PAIRED_CV'
    paths = list(REPAIR.glob('*_inference_receipt.json'))
    assert len(paths) == 1
    receipt = json.loads(paths[0].read_text())
    assert sha(receipt['parent_csv']) == receipt['parent_csv_sha256']
    assert len(receipt['spatial_serialization_changes']) == 1
    name = receipt['spatial_serialization_changes'][0]['movie']
    sys.path[:0] = [str(CODE), str(REPO / 'src'), str(REPO / 'scripts')]
    from score_exp214_paired import read_graphs
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph
    from geff import GeffMetadata
    import numpy as np
    raw = read_graphs(receipt['parent_csv'])[name]
    ids = sorted(raw['nodes'])
    mapping = {node: i for i, node in enumerate(ids)}
    graph = build_graph(np.asarray([raw['nodes'][node] for node in ids], dtype=float), [(mapping[s], mapping[t], 1., 0.) for s, t in raw['edges']])
    data = ROOT / 'data/exp213_source_view_20260912'
    ds = open_dataset(data / (name + '.zarr'), require_tracks=True, load_image=False)
    estimate = (GeffMetadata.read(data / (name + '.geff')).extra or {})['estimated_number_of_nodes']
    result = evaluate(graph, ds.tracks, scale=ds.scale)
    raw_row = {'dataset': name, **per_sample_metrics(result, float(estimate), node_recall(graph, ds.tracks))}
    repaired_row = next(row for row in metrics['rows']['public'] if row['dataset'] == name)
    rows = [raw_row if row['dataset'] == name else row for row in metrics['rows']['public']]
    raw_score = summarise(rows)['score']
    repaired_score = metrics['summary']['public']['score']
    output = {'status': 'PASS_RAW_BOUNDARY_SENSITIVITY_ONLY_NOT_PRODUCTION_AUDIT', 'movie': name, 'raw_row': raw_row, 'repaired_row': repaired_row, 'raw_public175_score': raw_score, 'repaired_public175_score': repaired_score, 'raw_minus_repaired': raw_score - repaired_score, 'full_metrics_sha256': sha(metrics_path), 'raw_csv_sha256': receipt['parent_csv_sha256'], 'scope': 'Original public prediction retained and scored by the official spatial metric. Raw image-bounds audit still fails; this is not approval for deployment.'}
    with (RUN / 'paired175/boundary_sensitivity.json').open('x') as f:
        json.dump(output, f, indent=2)
        f.write('\n')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
