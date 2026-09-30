"""Prepare the same eight175-movie shards for the frozen60epoch comparison."""
import json
from pathlib import Path

ROOT = '/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'
PLAN_SHA = '44f507d749bc1885e4aa9349e2e611f3359ebfc1e439d94c9823f62eab3495ee'


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def main():
    configurations = []
    for fold, count in (('44b6', 5), ('6bba', 3)):
        for index in range(count):
            tag = f'{fold}_{index:02}'
            config = json.loads(Path(f'reports/exp214_paired_{tag}_config_20260912.json').read_text())
            config.update(lease_id=f'biohub-exp214-strong60-paired-{fold}-{index:02}-20260912', token=f'exp214-strong60-paired-{tag}-v7', code=ROOT + '/code/exp214_inference_v7_20260912', run=ROOT + f'/runs/exp214_strong60_paired_{tag}_20260912', gpu='GPU-61c0078d-a4a6-37a2-3aba-0378e7794c46' if fold == '44b6' else 'GPU-04efb7bd-1f45-38cd-4a13-c79b6aeaa002', cpu_affinity='0-7' if fold == '44b6' else '8-15', scope='Fixed60epoch paired175 predictions; no new metrics before every shard/arm complete; deterministic invalid-coordinate repair with raw retention; no POST')
            arguments = config['arguments']
            for flag, value in (('--notebook', ROOT + '/code/exp214_inference_v7_20260912/compact47_v20.ipynb'), ('--bundle', ROOT + f'/code/exp214_strong60_evaluation_inputs_20260912/{fold}_bundle.json'), ('--output', config['run'] + '/output')):
                arguments[arguments.index(flag) + 1] = value
            path = f'reports/exp214_strong60_paired_{tag}_config_20260912.json'
            save(path, config)
            configurations.append(path)
    manifest = json.loads(Path('reports/exp214_score175_manifest_20260912.json').read_text())
    manifest.update(training_plan_sha256=PLAN_SHA, training_epochs=60, scope='Fixed60epoch stronger paired175 comparison. Budget adapted after registered data control, no within-stage target tuning; only two embryos; no unknown-selector OOF.')
    for parts in manifest['arms'].values():
        for part in parts:
            for key in ('csv', 'receipt'):
                part[key] = part[key].replace('/runs/exp214_paired_', '/runs/exp214_strong60_paired_')
    save('reports/exp214_strong60_score175_manifest_20260912.json', manifest)
    print(json.dumps({'configs': configurations, 'movies': len(manifest['movies']), 'plan_sha256': PLAN_SHA}, indent=2))


if __name__ == '__main__':
    main()
