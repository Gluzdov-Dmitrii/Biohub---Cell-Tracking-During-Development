"""Score preserved raw control coordinates after all three strict control gates."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
RUN = ROOT / 'runs/exp214_data_control_score_v2_20260912/output'
REPAIR = ROOT / 'runs/exp214_control_serialization_repair_20260912'
CODE = ROOT / 'code/exp214_inference_v6_20260912'
REPO = ROOT / 'code/exp214_honest_refit_v4_20260912/tracking_repo'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    gate = json.loads((RUN / 'no_metric_gate.json').read_text())
    assert gate['status'] == 'PASS_ALL_THREE_CONTROLS_BEFORE_TARGET_LABELS' and len(gate['movies']) == 20
    metrics = json.loads((RUN / 'metrics.json').read_text())
    assert metrics['status'] == 'PASS_EQUAL_TIME_DATA_REDUCTION_CONTROL'
    spec = json.loads((REPAIR / 'manifest.json').read_text())
    sys.path[:0] = [str(CODE), str(REPO / 'src'), str(REPO / 'scripts')]
    from score_exp214_paired import read_graphs
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph
    from geff import GeffMetadata
    import numpy as np
    output = {'status': 'PASS_RAW_CONTROL_BOUNDARY_SENSITIVITY_NOT_PRODUCTION_AUDIT', 'arms': {}}
    for arm, part in spec['arms'].items():
        receipt = json.loads(Path(part['receipt']).read_text())
        assert sha(receipt['parent_csv']) == receipt['parent_csv_sha256']
        names = sorted({row['movie'] for row in receipt['spatial_serialization_changes']})
        replacement = {}
        if names:
            raw_graphs = read_graphs(receipt['parent_csv'])
            for name in names:
                raw = raw_graphs[name]
                ids = sorted(raw['nodes'])
                mapping = {node: i for i, node in enumerate(ids)}
                graph = build_graph(np.asarray([raw['nodes'][node] for node in ids], dtype=float), [(mapping[s], mapping[t], 1., 0.) for s, t in raw['edges']])
                data = ROOT / 'data/exp213_source_view_20260912'
                ds = open_dataset(data / (name + '.zarr'), require_tracks=True, load_image=False)
                estimate = (GeffMetadata.read(data / (name + '.geff')).extra or {})['estimated_number_of_nodes']
                result = evaluate(graph, ds.tracks, scale=ds.scale)
                replacement[name] = {'dataset': name, **per_sample_metrics(result, float(estimate), node_recall(graph, ds.tracks))}
        raw_rows = [replacement.get(row['dataset'], row) for row in metrics['rows'][arm]]
        raw_score = summarise(raw_rows)['score']
        repaired_score = metrics['summary'][arm]['score']
        output['arms'][arm] = {'changed_coordinates': len(receipt['spatial_serialization_changes']), 'rescored_movies': names, 'raw_score': raw_score, 'repaired_score': repaired_score, 'raw_minus_repaired': raw_score - repaired_score, 'raw_rows': replacement}
    output['strict_metrics_sha256'] = sha(RUN / 'metrics.json')
    with (RUN / 'boundary_sensitivity.json').open('x') as f:
        json.dump(output, f, indent=2)
        f.write('\n')
    print(json.dumps({arm: {key: value for key, value in row.items() if key != 'raw_rows'} for arm, row in output['arms'].items()}, indent=2))


if __name__ == '__main__':
    main()
