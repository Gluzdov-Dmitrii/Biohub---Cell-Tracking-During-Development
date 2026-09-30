"""Repair recorded spatial boundary violations without labels or graph edits."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import zarr


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for key in ('manifest', 'diagnostic', 'data', 'output'):
        parser.add_argument('--' + key, type=Path, required=True)
    args = parser.parse_args()
    diagnostic = json.loads(args.diagnostic.read_text())
    assert diagnostic['target_labels_read'] is False
    assert diagnostic['out_of_bounds_count'] == {'public': 1}
    assert len(diagnostic['examples']) == 1
    expected = diagnostic['examples'][0]
    assert expected['point'] == [61., 64., 140., 139.]
    manifest = json.loads(args.manifest.read_text())
    args.output.mkdir(exist_ok=False)
    repaired = []
    for arm, parts in manifest['arms'].items():
        for index, part in enumerate(parts):
            if part['csv'] != expected['csv']:
                continue
            assert arm == expected['arm']
            original = Path(part['csv'])
            receipt = json.loads(Path(part['receipt']).read_text())
            assert sha(original) == receipt['submission_sha256']
            shapes = {name: tuple(zarr.open_group(str(args.data / (name + '.zarr')), mode='r')['0'].shape) for name in receipt['movies']}
            target = args.output / f'{arm}_{index}_submission.csv'
            changes = []
            with original.open(newline='') as source, target.open('x', newline='') as destination:
                reader = csv.DictReader(source)
                writer = csv.DictWriter(destination, fieldnames=reader.fieldnames)
                writer.writeheader()
                for row in reader:
                    if row['row_type'] == 'node':
                        shape = shapes[row['dataset']]
                        assert 0 <= int(row['t']) < shape[0]
                        before = [float(row[key]) for key in ('z', 'y', 'x')]
                        after = [value if 0 <= value < size else min(max(value, 0.), size - 1.) for value, size in zip(before, shape[1:])]
                        if before != after:
                            changes.append({'movie': row['dataset'], 'node_id': row['node_id'], 't': int(row['t']), 'before': before, 'after': after})
                            for key, value in zip(('z', 'y', 'x'), after):
                                row[key] = str(int(value)) if value.is_integer() else repr(value)
                    writer.writerow(row)
            assert changes == [{'movie': expected['movie'], 'node_id': expected['id'], 't': 61, 'before': [64., 140., 139.], 'after': [63., 140., 139.]}]
            receipt.update(status='PASS_DETERMINISTIC_SPATIAL_SERIALIZATION_REPAIR', parent_csv=str(original), parent_csv_sha256=sha(original), parent_receipt=part['receipt'], parent_receipt_sha256=sha(part['receipt']), submission_sha256=sha(target), spatial_serialization_changes=changes, repair_policy='Clamp spatial coordinates to [0, image_shape - 1]; retain all nodes and edges; no labels')
            receipt_path = args.output / f'{arm}_{index}_inference_receipt.json'
            receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
            part.update(csv=str(target), receipt=str(receipt_path))
            repaired.append(receipt)
    assert len(repaired) == 1
    manifest['parent_manifest_sha256'] = sha(args.manifest)
    manifest['serialization_repair'] = 'One public z=64->63; local predictions unchanged. Original public artifact retained for official-metric sensitivity.'
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    result = {'status': 'PASS_ONE_SPATIAL_SERIALIZATION_REPAIR_NO_LABELS', 'target_labels_read': False, 'diagnostic_sha256': sha(args.diagnostic), 'parent_manifest_sha256': sha(args.manifest), 'manifest_sha256': sha(args.output / 'manifest.json'), 'changes': repaired[0]['spatial_serialization_changes'], 'parent_csv_sha256': repaired[0]['parent_csv_sha256'], 'repaired_csv_sha256': repaired[0]['submission_sha256']}
    (args.output / 'repair_receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
