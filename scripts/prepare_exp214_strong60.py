"""Freeze the bounded stronger-training comparison after the measured budget confound."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = '/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def main():
    plan = json.loads(Path('reports/exp214_equal_time_plan_20260912.json').read_text())
    control = json.loads(Path('outputs/research/exp214_data_control_20260912/comparison.json').read_text())
    assert control['status'] == 'PASS_PAIRED_DATA_REDUCTION_COMPARISON'
    plan['status'] = 'PREREGISTERED_STRONG60_PAIRED175_DEVELOPMENT_COMPARISON'
    plan['detector']['seeds'] = [2026, 314159]
    plan['detector']['initialization'] = 'Resume each own clean scratch-trained12epoch model and optimizer; no public weights'
    plan['kaggle_submission_authorized_by_this_plan'] = False
    plan.pop('equal_time_control')
    plan['scope_limits'] = 'Two biological embryos, development-adapted CV. The60epoch budget was selected after the registered20movie data control exposed severe12epoch undertraining. Clean fold weights do not make this a pristine final holdout or exact400epoch public-weight OOF. No further budget or graph tuning after this stage.'
    plan['no_metric_gate'] = 'All four60epoch checkpoints frozen by source-only selection and all175 paired graph predictions complete before any new60epoch paired175 metrics. Existing source44 single-detector20movie control is explicitly already known. No partial diagnostic score loop.'
    plan['strong60_extension'] = {
        'reason': 'Reduced12 scored0.60318 versus full12 0.77730; reduced60 recovered0.77268 at1.02193 times full12 wall time on the registered20 movies. Broad12epoch result alone cannot resolve graph-family quality under adequate training.',
        'control_comparison_sha256': hashlib.sha256(Path('outputs/research/exp214_data_control_20260912/comparison.json').read_bytes()).hexdigest(),
        'reuse_source44_seed2026': {'path': ROOT + '/runs/exp214_equal_time44b6_s2026_20260912/output/edge_predictor_best.pth', 'sha256': '6dfa9cbfc5f298c6680a63353314d9bf353466a4aec5756aa188e4e0b2bd8bba', 'training_plan_sha256': '9b1fd764a4571669d0ed7c51ea4e8f4a3cdd49d455ae8af957413b45c9e398e3', 'epochs': 60},
        'remaining_models': [['44b6', 314159], ['6bba', 2026], ['6bba', 314159]],
        'approx_remaining_gpu_hours': 10.2,
        'internal_completion_deadline_utc': '2026-09-13T18:00:00+00:00',
        'submission_policy': 'No additional POST; the two authorized12epoch diagnostics are already submitted.',
        'inference_boundary_policy': 'Preserve valid fractional values; clamp only spatial values outside the image to the nearest valid voxel. Preserve raw CSV and exact changed-row receipts; never remove nodes or edges.',
        'next_action_after_results': 'Report and compare; no automatic100/400epoch sweep or teacher training.'
    }
    destination = Path('reports/exp214_strong60_plan_20260912.json')
    write(destination, plan)
    base = json.loads(Path('reports/exp214_equal_time44b6_s2026_config_20260912.json').read_text())
    gpu = {0: 'GPU-61c0078d-a4a6-37a2-3aba-0378e7794c46', 1: 'GPU-04efb7bd-1f45-38cd-4a13-c79b6aeaa002'}
    configurations = []
    for fold, seed, lane in [('44b6', 314159, 0), ('6bba', 2026, 0), ('6bba', 314159, 1)]:
        first_run = ROOT + f'/runs/exp214_strong60_{fold}_s{seed}_p01_20260912'
        for part in range(1, 2 if fold == '44b6' else 4):
            name = f'exp214_strong60_{fold}_s{seed}_p{part:02}_20260912'
            config = copy.deepcopy(base)
            config.update(lease_id=name.replace('_', '-'), token=name, gpu=gpu[lane], cpu_affinity='0-7' if lane == 0 else '8-15', code=ROOT + '/code/exp214_strong60_v1_20260912', run=ROOT + '/runs/' + name, fold=fold, seed=seed, max_seconds=10800 if fold == '44b6' else 7200, lease_minutes=240 if fold == '44b6' else 200, warm_start=ROOT + f'/runs/exp214_reduced{fold}_s{seed}_20260912/output/checkpoint_last.pth', scope='Fixed60epoch stronger paired175 comparison; source-only checkpoint choice; no new target metrics until all models/predictions complete; no POST')
            if part > 1:
                config['resume_output'] = first_run + '/output'
            file = f'reports/exp214_strong60_{fold}_s{seed}_p{part:02}_config_20260912.json'
            write(file, config)
            configurations.append(file)
    print(json.dumps({'plan_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(), 'configurations': configurations}, indent=2))


if __name__ == '__main__':
    main()
