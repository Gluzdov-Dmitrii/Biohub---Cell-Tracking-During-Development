"""Frozen EXP214 geometry-only FN diagnostic; no threshold/model selection."""
import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from analyze_submission_edge_failure_modes import (
    load_helpers, merge_verified_csv_graphs, sha256,
)


def main():
    ap = argparse.ArgumentParser()
    for key in ('repo', 'data', 'metrics', 'output'):
        ap.add_argument('--' + key, type=Path, required=True)
    args = ap.parse_args()
    started = time.time()
    metrics = json.loads(args.metrics.read_text())
    graphs, manifest = merge_verified_csv_graphs(metrics, 'public')
    _, _, matched_maps, _, td, open_dataset, evaluate, build_graph = load_helpers(args.repo)
    recorded = {r['dataset']: r for r in metrics['rows']['public']}
    counts = defaultdict(lambda: [0, 0])
    movies = []
    for name, source in sorted(graphs.items()):
        ids = sorted(source['nodes'])
        index = {node_id: i for i, node_id in enumerate(ids)}
        coords = np.asarray([source['nodes'][i] for i in ids], dtype=float).reshape(-1, 4)
        edges = [(index[s], index[t], 1., 0.) for s, t in source['edges']]
        pred = build_graph(coords, edges)
        ds = open_dataset(args.data / (name + '.zarr'), require_tracks=True, load_image=False)
        official = evaluate(pred, ds.tracks, scale=ds.scale)
        for key in ('edge_tp', 'edge_fp', 'edge_fn'):
            assert int(getattr(official, key)) == int(recorded[name][key]), (name, key)
        _, matches = matched_maps(pred, td)
        rows = list(ds.tracks.node_attrs().iter_rows(named=True))
        by_t = defaultdict(list)
        for row in rows:
            by_t[int(row['t'])].append(row)
        missed = 0
        for t, frame in sorted(by_t.items()):
            xyz = np.asarray([[r[k] for k in ('z', 'y', 'x')] for r in frame], dtype=float)
            physical = xyz * np.asarray(ds.scale)
            nearest = cKDTree(physical).query(physical, k=2)[0][:, 1] if len(frame) > 1 else np.full(1, np.inf)
            for i, row in enumerate(frame):
                fn = int(int(row[td.DEFAULT_ATTR_KEYS.NODE_ID]) not in matches)
                missed += fn
                depth = min(3, int(4 * float(row['z']) / ds.image_shape[1]))
                phase = min(3, int(4 * t / ds.image_shape[0]))
                nn = 'lt3um' if nearest[i] < 3 else '3to6um' if nearest[i] < 6 else '6to12um' if nearest[i] < 12 else 'ge12um'
                boundary = min(np.minimum(xyz[i], np.asarray(ds.image_shape[1:]) - 1 - xyz[i]) * np.asarray(ds.scale))
                for prefix in ('ALL', name.split('_')[0]):
                    for feature, value in [('total', 'all'), ('depth_quartile', str(depth)), ('time_quartile', str(phase)), ('nearest_gt_distance', nn), ('boundary', 'lt5um' if boundary < 5 else 'ge5um')]:
                        bucket = counts[(prefix, feature, value)]
                        bucket[0] += 1
                        bucket[1] += fn
        movie = {'dataset': name, 'gt_nodes': len(rows), 'missed_nodes': missed, 'miss_rate': missed / len(rows) if rows else None}
        movies.append(movie)
        print(json.dumps(movie), flush=True)
    result = {'status': 'PASS_FROZEN_OFFICIAL_MATCH_NODE_STRATA', 'evidence_class': 'development-adapted target-label diagnostic, not fresh OOF or improvement evidence', 'elapsed_seconds': time.time() - started, 'metrics_sha256': sha256(args.metrics), 'input_manifest': manifest, 'movies': movies, 'strata': [{'embryo': k[0], 'feature': k[1], 'value': k[2], 'gt_nodes': v[0], 'missed_nodes': v[1], 'miss_rate': v[1]/v[0]} for k,v in sorted(counts.items())], 'limitations': ['No raw-intensity read in this geometry-only pass.', 'Node stratification includes all annotated nodes; it is not an edge-metric decomposition.', 'Voxel quartiles describe array position, not biological depth.']}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'elapsed_seconds': result['elapsed_seconds']}), flush=True)


if __name__ == '__main__':
    main()
