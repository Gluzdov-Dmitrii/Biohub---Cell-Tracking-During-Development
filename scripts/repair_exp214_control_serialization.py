"""Apply the same label-free boundary-only serialization repair to all controls."""
import csv
import hashlib
import json
from pathlib import Path
import zarr

ROOT = Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
MANIFEST = ROOT / 'code/exp214_evaluation_inputs_20260912/exp214_data_control_score_manifest_20260912.json'
OUTPUT = ROOT / 'runs/exp214_control_serialization_repair_20260912'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    spec = json.loads(MANIFEST.read_text())
    OUTPUT.mkdir(exist_ok=False)
    report = {'status': 'PASS_CONTROL_BOUNDARY_REPAIR_NO_LABELS', 'target_labels_read': False, 'parent_manifest_sha256': sha(MANIFEST), 'arms': {}}
    shapes = {}
    for arm, part in spec['arms'].items():
        receipt = json.loads(Path(part['receipt']).read_text())
        original = Path(part['csv'])
        assert sha(original) == receipt['submission_sha256']
        target = OUTPUT / (arm + '.csv')
        changes = []
        with original.open(newline='') as source, target.open('x', newline='') as destination:
            reader = csv.DictReader(source)
            writer = csv.DictWriter(destination, fieldnames=reader.fieldnames)
            writer.writeheader()
            for row in reader:
                if row['row_type'] == 'node':
                    name = row['dataset']
                    if name not in shapes:
                        shapes[name] = tuple(zarr.open_group(str(ROOT / 'data/exp213_source_view_20260912' / (name + '.zarr')), mode='r')['0'].shape)
                    shape = shapes[name]
                    assert 0 <= int(row['t']) < shape[0]
                    before = [float(row[key]) for key in ('z', 'y', 'x')]
                    after = [value if 0 <= value < size else min(max(value, 0.), size - 1.) for value, size in zip(before, shape[1:])]
                    if before != after:
                        changes.append({'movie': name, 'node_id': row['node_id'], 't': int(row['t']), 'before': before, 'after': after})
                        for key, value in zip(('z', 'y', 'x'), after):
                            row[key] = str(int(value)) if value.is_integer() else repr(value)
                writer.writerow(row)
        receipt.update(status='PASS_DETERMINISTIC_SPATIAL_SERIALIZATION_REPAIR', parent_csv=str(original), parent_csv_sha256=sha(original), parent_receipt=part['receipt'], parent_receipt_sha256=sha(part['receipt']), submission_sha256=sha(target), spatial_serialization_changes=changes, repair_policy='Only out-of-volume spatial values clamped to nearest valid voxel; valid fractional values, all nodes/edges unchanged; no labels')
        receipt_path = OUTPUT / (arm + '_receipt.json')
        receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
        part.update(csv=str(target), receipt=str(receipt_path))
        report['arms'][arm] = {'changes': changes, 'parent_csv_sha256': receipt['parent_csv_sha256'], 'repaired_csv_sha256': receipt['submission_sha256']}
    spec['parent_manifest_sha256'] = sha(MANIFEST)
    (OUTPUT / 'manifest.json').write_text(json.dumps(spec, indent=2) + '\n')
    report['manifest_sha256'] = sha(OUTPUT / 'manifest.json')
    (OUTPUT / 'repair_receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
