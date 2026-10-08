"""Call-cap and durable reservation tests using mocks; no Maxwell solves."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np

from a20.costs import BudgetExceeded, CostBook
from a23 import cli
from a23.physics import ReferencePhysics


PHASES = (
    ('OFFLINE_CLEAN_LABEL_GENERATION', 'clean_label_full_state_calls', 'clean_full_forward_cap', 12),
    ('ONLINE_FULL_PREDICTION_VALIDATION', 'primary_prediction_full_state_calls', 'primary_prediction_full_forward_cap', 12),
    ('ONLINE_CALIBRATION_PREDICTION_VALIDATION', 'calibration_prediction_full_state_calls', 'calibration_prediction_full_forward_cap', 8),
)


def mock_reference(ledger: Path, *, prior=None, full_state=None):
    """Use actual validation/predict logic while replacing the full-state action."""
    reference = ReferencePhysics.__new__(ReferencePhysics)
    reference.chi0 = np.array([.1+.04j])
    reference.config = {key: limit for _, _, key, limit in PHASES}
    reference.config.update(physical_real_lower=-.5, physical_imag_lower=0.,
                            pole_relative_floor=1e-10, _prior_counts=prior or {})
    reference.book = CostBook(ledger, device='cpu', enforce=False,
                              metadata={'scope': 'guard_mock_only'})
    action = mock.Mock(return_value=SimpleNamespace(field=np.array([[1.+2.j]])))
    if full_state is not None:
        action.side_effect = full_state
    reference.adapter = SimpleNamespace(
        problem=SimpleNamespace(volume=.22**3, frequency=2.),
        full_state=action, whiten=lambda values: values,
    )
    return reference


def ledger_rows(path: Path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


class PredictionCapTests(unittest.TestCase):
    def test_cumulative_caps_include_prior_jobs_for_each_registered_phase(self):
        for phase, counter, key, limit in PHASES:
            with self.subTest(phase=phase), tempfile.TemporaryDirectory(prefix='a23-guard-') as directory:
                reference = mock_reference(Path(directory)/'actions.jsonl', prior={counter: limit-1})
                with reference.book.scope(phase):
                    reference.predict(reference.chi0)
                    with self.assertRaisesRegex(BudgetExceeded, 'PHYSICAL_CALL_CAP:'+key):
                        reference.predict(reference.chi0)
                self.assertEqual(reference.adapter.full_state.call_count, 1)
                self.assertEqual(reference.book.counts[counter], 1)
                self.assertEqual(reference.book.phase, 'online')

    def test_exhausting_one_phase_does_not_consume_other_phase_caps(self):
        prior = {counter: limit if phase == PHASES[0][0] else limit-1
                 for phase, counter, _, limit in PHASES}
        with tempfile.TemporaryDirectory(prefix='a23-guard-') as directory:
            reference = mock_reference(Path(directory)/'actions.jsonl', prior=prior)
            with reference.book.scope(PHASES[0][0]):
                with self.assertRaises(BudgetExceeded):
                    reference.predict(reference.chi0)
            for phase, counter, _, _ in PHASES[1:]:
                with reference.book.scope(phase):
                    reference.predict(reference.chi0)
                self.assertEqual(reference.book.counts[counter], 1)
            self.assertEqual(reference.book.counts[PHASES[0][1]], 0)
            self.assertEqual(reference.adapter.full_state.call_count, 2)

    def test_reservation_is_on_disk_before_a_simulated_failed_full_state(self):
        with tempfile.TemporaryDirectory(prefix='a23-guard-') as directory:
            path = Path(directory)/'actions.jsonl'
            phase, counter, _, _ = PHASES[1]
            seen = []

            def failing_full_state(_chi):
                # Inspection occurs inside the action, before its failed span exits.
                rows = ledger_rows(path)
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]['event'], 'PHYSICAL_CALL_RESERVED')
                self.assertEqual(rows[0]['status'], 'RESERVED')
                self.assertEqual(rows[0]['phase'], phase)
                self.assertEqual(rows[0]['counters'], {counter: 1})
                seen.append(rows[0])
                raise ValueError('simulated full-state failure')

            reference = mock_reference(path, full_state=failing_full_state)
            with reference.book.scope(phase):
                with self.assertRaisesRegex(ValueError, 'simulated full-state failure'):
                    reference.predict(reference.chi0)
            self.assertEqual(len(seen), 1)
            self.assertEqual(reference.book.counts[counter], 1)
            rows = ledger_rows(path)
            self.assertEqual([row['status'] for row in rows], ['RESERVED', 'FAILED'])
            self.assertEqual(sum(row.get('counters', {}).get(counter, 0) for row in rows), 1)
            self.assertIn('simulated full-state failure', rows[-1]['error'])

    def test_physically_rejected_material_does_not_reserve_a_full_call(self):
        for phase, counter, _, _ in PHASES:
            with self.subTest(phase=phase), tempfile.TemporaryDirectory(prefix='a23-guard-') as directory:
                path = Path(directory)/'actions.jsonl'
                reference = mock_reference(path)
                with reference.book.scope(phase):
                    for material in [np.array([-.51+.04j]), np.array([.1-.001j]), np.array([np.nan+.04j])]:
                        with self.assertRaises(ValueError):
                            reference.predict(material)
                self.assertEqual(reference.book.counts[counter], 0)
                reference.adapter.full_state.assert_not_called()
                self.assertEqual(ledger_rows(path), [])


class DurableHistoryTests(unittest.TestCase):
    def test_history_takes_per_job_maximum_of_receipt_and_log_then_sums_jobs(self):
        clean, primary, calibration = [item[1] for item in PHASES]
        with tempfile.TemporaryDirectory(prefix='a23-guard-history-') as directory:
            root = Path(directory)
            first = root/'results/a23/jobs/first'
            second = root/'results/a23/jobs/second'
            first.mkdir(parents=True); second.mkdir()
            (first/'job_receipt.json').write_text(json.dumps({'counts': {clean: 2, primary: 4}}))
            rows = [
                {'status': 'RESERVED', 'counters': {clean: 1}},
                {'status': 'FAILED', 'counters': {clean: 1, primary: 1}},
                {'status': 'OK', 'counters': {clean: 1, primary: 1}},
                {'status': 'RESERVED', 'counters': {calibration: 1}},
            ]
            (first/'ACTION_LEDGER.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
            (second/'job_receipt.json').write_text(json.dumps({'counts': {clean: 2}}))
            (second/'ACTION_LEDGER.jsonl').write_text(json.dumps({'status': 'OK', 'counters': {clean: 2}})+'\n')
            counts = cli.prior_counts(root)
            self.assertEqual(counts[clean], 5)  # max(2,3)+max(2,2), never receipt+log.
            self.assertEqual(counts[primary], 4)  # Receipt is newer for this counter.
            self.assertEqual(counts[calibration], 1)  # The durable failed/reserved attempt survives.

    def test_reserved_failed_call_is_recovered_when_no_receipt_was_written(self):
        with tempfile.TemporaryDirectory(prefix='a23-guard-history-') as directory:
            root = Path(directory)
            folder = root/'results/a23/jobs/interrupted'
            folder.mkdir(parents=True)
            reference = mock_reference(folder/'ACTION_LEDGER.jsonl', full_state=ValueError('interrupted action'))
            phase, counter, _, _ = PHASES[0]
            with reference.book.scope(phase):
                with self.assertRaises(ValueError):
                    reference.predict(reference.chi0)
            self.assertFalse((folder/'job_receipt.json').exists())
            self.assertEqual(cli.prior_counts(root)[counter], 1)

    def test_orphan_manifest_blocks_new_work_before_book_or_job_creation(self):
        with tempfile.TemporaryDirectory(prefix='a23-guard-history-') as directory:
            root = Path(directory)
            folder = root/'results/a23/jobs/interrupted'
            folder.mkdir(parents=True)
            (folder/'job_manifest.json').write_text(json.dumps({'stage': 'pilot', 'device': 'cuda'}))
            (root/'FROZEN_CONFIG.json').write_text('{}')
            with self.assertRaisesRegex(BudgetExceeded, 'ORPHAN_JOB_COST_UNRESOLVED'):
                cli.prior_cost(root)
            with mock.patch.object(cli, 'CostBook') as book_factory:
                with self.assertRaisesRegex(BudgetExceeded, 'ORPHAN_JOB_COST_UNRESOLVED'):
                    cli.main(['micro', '--root', str(root), '--job', 'blocked-next-job', '--device', 'cpu'])
            book_factory.assert_not_called()
            self.assertFalse((root/'results/a23/jobs/blocked-next-job').exists())

    def test_completed_failed_job_keeps_cost_and_allows_accounting(self):
        with tempfile.TemporaryDirectory(prefix='a23-guard-history-') as directory:
            root = Path(directory)
            folder = root/'results/a23/jobs/failed-complete-receipt'
            folder.mkdir(parents=True)
            (folder/'job_manifest.json').write_text('{}')
            (folder/'job_receipt.json').write_text(json.dumps({
                'status': 'FAILED', 'process_cpu_seconds': 2.5, 'gpu_occupation_seconds': 3.75,
            }))
            self.assertEqual(cli.prior_cost(root), (2.5, 3.75))


if __name__ == '__main__':
    unittest.main()
