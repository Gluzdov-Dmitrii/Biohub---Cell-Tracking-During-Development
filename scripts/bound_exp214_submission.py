"""Bound only invalid spatial values; preserve raw graph and all valid coordinates."""
import csv
import hashlib
import json
import math
from pathlib import Path


def bound_submission(path, shapes):
    path = Path(path)
    assert path.name == 'submission.csv'
    raw = path.parent / 'raw_predictions.csv'
    temporary = path.parent / 'bounded_predictions.csv.tmp'
    assert not raw.exists() and not temporary.exists()
    original_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    changes = []
    with path.open(newline='') as source, temporary.open('x', newline='') as destination:
        reader = csv.DictReader(source)
        writer = csv.DictWriter(destination, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            if row['row_type'] == 'node':
                shape = shapes[row['dataset']]
                assert 0 <= int(row['t']) < shape[0], 'Invalid timepoint is not repaired'
                before = [float(row[key]) for key in ('z', 'y', 'x')]
                assert all(math.isfinite(value) for value in before)
                after = [value if 0 <= value < size else min(max(value, 0.), size - 1.) for value, size in zip(before, shape[1:])]
                if before != after:
                    changes.append({'dataset': row['dataset'], 'node_id': row['node_id'], 't': int(row['t']), 'before': before, 'after': after})
                    for key, value in zip(('z', 'y', 'x'), after):
                        row[key] = str(int(value)) if value.is_integer() else repr(value)
            writer.writerow(row)
    if changes:
        path.rename(raw)
        temporary.rename(path)
        assert hashlib.sha256(raw.read_bytes()).hexdigest() == original_sha
    else:
        temporary.unlink()
    report = {'status': 'PASS_SPATIAL_BOUNDARY_SERIALIZATION', 'target_labels_read': False, 'raw_sha256': original_sha, 'submission_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'changed_nodes': len(changes), 'changes': changes, 'policy': 'Only out-of-volume spatial values are clamped to nearest valid voxel; valid fractional values and all node/edge identities retained', 'raw_path': str(raw) if changes else str(path)}
    (path.parent / 'spatial_boundary_receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    return report
