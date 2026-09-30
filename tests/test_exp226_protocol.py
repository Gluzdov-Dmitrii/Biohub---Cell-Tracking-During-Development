import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from exp226_protocol import SourceAccessGuard, deterministic_split, invoke_source_training, validate_plan


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / 'data'
        self.data.mkdir()
        self.output = self.root / 'output'
        self.output.mkdir()
        self.records = []
        for i in range(12):
            name = f'44b6_{i:08x}'
            row = {'dataset_id': name}
            for key, suffix in [('zarr_path', '.zarr'), ('geff_path', '.geff')]:
                path = self.data / (name + suffix)
                path.mkdir()
                row[key] = str(path)
            self.records.append(row)
        train, val = deterministic_split(self.records, '44b6', 4)
        self.plan = {'experiment': 'EXP226', 'purpose': 'source_only_training_pilot',
                     'source_embryo': '44b6', 'target_embryo': '6bba', 'fold': 1,
                     'epochs': 2, 'iterations_per_epoch': 8, 'resume': False,
                     'checkpoint_selection': 'none_pilot_fixed_final', 'num_workers': 0,
                     'torch_compile': False, 'train': train[:4], 'inner_validation': val[:2]}

    def test_partition_independent_of_input_order(self):
        a, b = deterministic_split(self.records, '44b6', 4)
        c, d = deterministic_split(reversed(self.records), '44b6', 4)
        self.assertEqual((a, b), (c, d))
        self.assertFalse({x['dataset_id'] for x in a} & {x['dataset_id'] for x in b})
        self.assertEqual(len(a) + len(b), len(self.records))

    def test_overlap_rejected(self):
        self.plan['inner_validation'][0] = self.plan['train'][0]
        with self.assertRaisesRegex(AssertionError, 'overlap'):
            validate_plan(self.plan)

    def test_mislabeled_target_path_rejected(self):
        self.plan['train'][0]['zarr_path'] = str(self.data / '6bba_deadbeef.zarr')
        with self.assertRaisesRegex(AssertionError, 'path mismatch'):
            validate_plan(self.plan)

    def test_source_allowlist_enforces_both_labels_and_images(self):
        records = self.plan['train'] + self.plan['inner_validation']
        guard = SourceAccessGuard(records, self.output, self.data)
        for row in records:
            guard('open', (row['zarr_path'] + '/0/zarr.json',))
            guard('open', (row['geff_path'] + '/nodes/ids/c/0',))
        self.assertEqual(guard.opened_ids, guard.allowed_ids)
        for event, path in [('open', self.data/'6bba_12345678.zarr/0/zarr.json'),
                            ('open', self.data/'6bba_12345678.geff/nodes/ids/c/0'),
                            ('os.scandir', self.data),
                            ('open', self.root/'public_weights.pt')]:
            with self.assertRaises(PermissionError):
                guard(event, (str(path),))
        self.assertEqual(len(guard.denied), 4)
        guard('open', (str(self.output/'fold1/last.pt'),))

    def test_unlisted_source_movie_is_not_allowed(self):
        records = self.plan['train'] + self.plan['inner_validation']
        guard = SourceAccessGuard(records, self.output, self.data)
        missing = next(r for r in self.records if r['dataset_id'] not in guard.allowed_ids)
        with self.assertRaises(PermissionError):
            guard('open', (missing['geff_path'],))

    def test_fresh_train_call_only_no_outer_cv(self):
        calls = []
        def train_fold(*args, **kwargs):
            calls.append((args, kwargs))
            return 'own_checkpoint'
        def forbidden(*args, **kwargs):
            self.fail('Outer CV/main must never run')
        module = SimpleNamespace(train_fold=train_fold, main=forbidden, run_periodic_cv=forbidden)
        cfg = SimpleNamespace()
        got = invoke_source_training(module, cfg, self.plan, self.output, {'seed': 3407})
        self.assertEqual(got, 'own_checkpoint')
        self.assertEqual(module.PERIODIC_EPOCHS, (1, 2))
        self.assertEqual(len(calls), 1)
        args, kwargs = calls[0]
        self.assertIs(args[2], self.plan['train'])
        self.assertIs(args[3], self.plan['inner_validation'])
        self.assertEqual(kwargs, {'resume': False})

    def test_resume_or_target_selected_policy_rejected(self):
        for key, value in [('resume', True), ('checkpoint_selection', 'best_target'), ('epochs', 50)]:
            with self.subTest(key=key):
                plan = copy.deepcopy(self.plan)
                plan[key] = value
                with self.assertRaises(AssertionError):
                    validate_plan(plan)


if __name__ == '__main__':
    unittest.main()
