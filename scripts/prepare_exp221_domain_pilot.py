"""Prepare isolated EXP221 paired source-only domain augmentation pilot."""
import hashlib
import json
from pathlib import Path

ROOT = '/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'


def main():
    out = Path('outputs/research/exp221_domain_pilot_code_20260921')
    out.mkdir(parents=True, exist_ok=True)
    trainer = Path('scripts/train_exp214_equal_time.py').read_text()
    trainer = trainer.replace("    args = p.parse_args()", "    args = p.parse_args()\n    assert args.image_cache, 'EXP221 requires frozen exact cache'")
    trainer = trainer.replace("    train_epoch = upstream.train_epoch", "    from exp221_domain_augmentation import domain_augment\n    if plan['exp221_arm'] == 'domain':\n        upstream.DEFAULT_AUGMENTATIONS = [*upstream.DEFAULT_AUGMENTATIONS, domain_augment]\n    train_epoch = upstream.train_epoch", 1)
    trainer = trainer.replace("    contract_path = args.output/'contract.json'", "    contract['domain_module_sha256'] = sha(Path(__file__).with_name('exp221_domain_augmentation.py'))\n    contract['cache_loader_sha256'] = sha(Path(__file__).with_name('exp214_cache_loader.py'))\n    assert contract['warm_start_sha256'] == 'f8a43239be4136bc0d3d44ff19cfb8d69deb7b852e3abfc39f4a44c54a78a638'\n    contract_path = args.output/'contract.json'")
    trainer = trainer.replace("    initial_epoch = epoch", "    initial_epoch = epoch\n    # Select only post-intervention checkpoints in both matched arms.\n    if not last.exists():\n        best_score = -1.")
    trainer = trainer.replace("            receipt['precision_check'] = precision_check", "            assert np.isfinite([edge_loss,detection_loss]).all(), 'Nonfinite smoke losses'\n            receipt['edge_loss'] = edge_loss\n            receipt['detection_loss'] = detection_loss\n            receipt['precision_check'] = precision_check")
    (out/'train_exp213_detector.py').write_text(trainer)
    cache = Path('scripts/exp214_cache_loader.py').read_text()
    cache = cache.replace("    ast.fix_missing_locations(tree)", "    # Original default_rng() bypasses seed_all; fix equally in both arms.\n    for item in ast.walk(tree):\n        if isinstance(item, ast.Call) and ast.unparse(item.func) == 'np.random.default_rng':\n            assert not item.args and not item.keywords\n            item.args = [ast.parse('int(np.random.randint(0, 2**31))', mode='eval').body]\n    ast.fix_missing_locations(tree)")
    (out/'exp214_cache_loader.py').write_text(cache)
    for name in ['prepare_exp213_honest_refit.py', 'exp221_domain_augmentation.py', 'exp213_remote_job.py']:
        (out/name).write_bytes((Path('scripts')/name).read_bytes())
    wrapper = (out/'exp213_remote_job.py').read_text()
    wrapper = wrapper.replace("    for key in ('window_selection', 'image_cache', 'warm_start'):", "    if config.get('benchmark_steps'):\n        command.extend(['--benchmark-steps', str(config['benchmark_steps'])])\n    for key in ('window_selection', 'image_cache', 'warm_start'):")
    (out/'exp213_remote_job.py').write_text(wrapper)
    base = json.loads(Path('reports/exp214_equal_time_plan_20260912.json').read_text())
    base['experiment'] = 'EXP221'
    base['status'] = 'PREREGISTERED_SOURCE_ONLY_DOMAIN_PILOT'
    base['detector']['epochs'] = 24
    base['exp221_protocol'] = {'arms':['control','domain'], 'source':'44b6', 'seed':2026,
        'initialization':'same clean reduced epoch12 model AND optimizer', 'additional_epochs':12,
        'selection':'source validation only; best post-intervention checkpoint',
        'target_data_opened':False, 'kaggle_post':False,
        'budget':'same 12 additional epochs (matched updates); wall time reported, max 2h chunk',
        'known_limit':'Development-adapted pilot; source validation is not target generalization evidence',
        'stop':'finite 24 epochs; do not expand training without paired target evidence'}
    configs = []
    for lane, arm in enumerate(['control','domain']):
        plan = dict(base, exp221_arm=arm)
        plan_path = out/f'plan_{arm}.json'
        plan_path.write_text(json.dumps(plan, indent=2)+'\n')
        c = json.loads(Path('reports/exp214_equal_time44b6_s2026_config_20260912.json').read_text())
        stem = f'exp221_{arm}_44b6_s2026_20260921'
        c.update(experiment='EXP221', lease_id=stem.replace('_','-'), token=stem,
                 code=ROOT+f'/code/exp221_{arm}_v1_20260921', run=ROOT+'/runs/'+stem,
                 max_seconds=7200, lease_minutes=180, cpu_affinity='0-7' if lane==0 else '8-15',
                 gpu=['GPU-61c0078d-a4a6-37a2-3aba-0378e7794c46','GPU-04efb7bd-1f45-38cd-4a13-c79b6aeaa002'][lane],
                 retention='Keep best and latest optimizer checkpoint; review 2026-09-22; no automatic continuation beyond24epochs',
                 scope='EXP221 fixed12 additional source-only epochs, matched clean epoch12 initialization; no target metrics/POST')
        path = Path('reports')/(stem+'_config.json')
        path.write_text(json.dumps(c, indent=2)+'\n')
        configs.append(str(path))
        smoke = dict(c, run=c['run']+'_smoke', lease_id=c['lease_id']+'-smoke', token=c['token']+'_smoke',
                     benchmark_steps=2, max_seconds=600, lease_minutes=70,
                     scope='EXP221 two-step GPU finite-loss/shape smoke; benchmark state never promoted')
        Path('reports',stem+'_smoke_config.json').write_text(json.dumps(smoke,indent=2)+'\n')
    receipt = {'experiment':'EXP221','configs':configs,'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()},'protocol':base['exp221_protocol']}
    Path('reports/exp221_domain_pilot_prepare_20260921.json').write_text(json.dumps(receipt, indent=2)+'\n')
    launcher = Path('scripts/launch_exp214_job.py').read_text()
    launcher = launcher.replace("stem=a.config.name.replace('_config_','_monitor_').removesuffix('.json')", "stem=a.config.stem.removesuffix('_config')+'_monitor'")
    launcher = launcher.replace("in ('EXP214','EXP215','EXP217','EXP218')", "== 'EXP221'")
    for line in launcher.splitlines():
        if "assert (c['run'].startswith" in line:
            launcher = launcher.replace(line, "    assert c['run'].startswith(root+'/runs/exp221_')")
        if "assert (c['code'].startswith" in line:
            launcher = launcher.replace(line, "    assert c['code'].startswith(root+'/code/exp221_')")
    Path('scripts/launch_exp221_job.py').write_text(launcher)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
