"""Small operator tests only; no scene inputs, images, or research gates."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

import numpy as np
from scipy import linalg as la

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from a20.backend import Adapter, BasisView, MaterialChart, pack
from a20.costs import CostBook
from a20.opm import Projection, ReducedJacobian, SchurFeedback, UnsafeCore, orth
from a23.h1 import (CachedSchur, build_fixed_seeds, build_h1, fixed_probes,
                    source_anchor, streamed_projection_matrix)


class _SyntheticModel:
    def __init__(self, L, S, P):
        self.L_matrix, self.GS, self.P = L, S, P
        self.n, self.N, self.m = len(L), len(L) // 3, len(S)
        self._gs_svd = None

    def gs_modes(self):
        if self._gs_svd is None:
            _, _, vh = la.svd(self.GS, full_matrices=False)
            self._gs_svd = {'V': vh.conj().T}
        return self._gs_svd


class _SyntheticState:
    def __init__(self, a, forcing, exciting, da):
        self.chi, self.model = a.problem.init.copy(), a.model
        self.current = la.solve(a._operator_L, forcing).T
        self.exciting, self.da = exciting, da
        self.L = a._operator_L
        self._adapter = a

    def vjp(self, data):
        a = self._adapter
        rhs = a.model.GS.conj().T @ data.T
        fields = la.solve(self.L.conj().T, rhs).T.reshape(a.P, a.model.N, 3)
        factor = self.exciting.reshape(a.P, a.model.N, 3) * self.da[None, :, None]
        factor /= np.sqrt(a.problem.volume)
        return np.einsum('ptc,ptc->t', factor.conj(), fields)


class _SyntheticReference:
    """Exercise original adapter bookkeeping without running a solver job."""
    def __init__(self, *, N=9, m=12, seed=2718):
        rng = np.random.default_rng(seed)
        n, P, volume = 3 * N, 6, 0.04
        F = 0.014 * (rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n)))
        L = np.eye(n) - F
        S = rng.normal(size=(m, n)) + 1j * rng.normal(size=(m, n))
        points = rng.uniform(-1, 1, size=(N, 3))
        chart = MaterialChart(volume, N, None, 'full_cell')
        problem = SimpleNamespace(parent_id=991, points=points, volume=volume,
                                  init=np.full(N, 0.1 + 0.04j), chart=chart)
        book = CostBook(enforce=False)
        # Original Adapter methods (actions, B/B*, whitening and packing).
        a = object.__new__(Adapter)
        a.problem, a.chart, a.book, a.device = problem, chart, book, 'cpu'
        a.model = _SyntheticModel(L, S, P)
        a.P, a.n, a.m, a.p = P, n, m, chart.d
        a.whitening = 1.7
        a._operator_L, a._operator_chi, a._version = L, problem.init.copy(), 1
        a._operator_gpu = None
        a._full_cache = None
        forcing = rng.normal(size=(n, P)) + 1j * rng.normal(size=(n, P))
        exciting = rng.normal(size=(P, n)) + 1j * rng.normal(size=(P, n))
        da = rng.normal(size=N) + 1j * rng.normal(size=N)
        self.adapter, self.book, self.chi0 = a, book, problem.init.copy()
        self.state = _SyntheticState(a, forcing, exciting, da)
        self.data0 = a.whiten(pack(self.state.current @ S.T))
        self._forcing, self._matrix = forcing, None
        def known_forcing(_x):
            with book.span('synthetic_forcing', forcing_rhs=P):
                return forcing.copy()
        a.forcing = known_forcing

    def solve_reference(self, rhs, *, adjoint=False):
        columns = 1 if rhs.ndim == 1 else rhs.shape[1]
        counter = 'solve_adjoint_rhs' if adjoint else 'solve_forward_rhs'
        with self.book.span('synthetic_reference_solve', **{counter: columns}):
            L = self.adapter._operator_L
            return la.solve(L.conj().T if adjoint else L, rhs)

    def matrix(self):
        if self._matrix is None:
            a = self.adapter
            # A tiny per-column oracle, never a full current-material array.
            columns = []
            for k in range(a.p):
                d = np.zeros(a.p)
                d[k] = 1.
                b = a.apply_B(self.chi0, self.state, d)
                c = self.solve_reference(b.T)
                columns.append(a.whiten(pack((a.model.GS @ c).T)))
            self._matrix = np.column_stack(columns)
        return self._matrix

    def linear(self, _d):
        raise AssertionError('A cached linear convenience method must not construct randomized H1')

    def linear_adjoint(self, _w):
        raise AssertionError('A cached adjoint convenience method must not construct randomized H1')


def _config():
    return json.loads((Path(__file__).resolve().parents[1] / 'FROZEN_CONFIG.json').read_text())


def _view(reference, residual=None):
    return BasisView(reference.adapter, reference.chi0, reference.state,
                     reference.data0 * 0 if residual is None else residual)


def _random_basis(n, r, seed=3):
    rng = np.random.default_rng(seed)
    return orth(rng.normal(size=(n, r)) + 1j * rng.normal(size=(n, r)))[0]


class TestA23H1(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)

    def test_cached_matches_original_block_actions_without_new_L(self):
        for columns in (None, 7):
            with self.subTest(columns=columns):
                self._check_cached(columns)

    def _check_cached(self, columns):
        reference = _SyntheticReference()
        view = _view(reference)
        U = _random_basis(view.n, 8)
        old = SchurFeedback(view, U, _config()['OPM'])
        cached = CachedSchur(view, U, _config()['OPM'])
        rng = np.random.default_rng(23)
        shape = (view.n,) if columns is None else (view.n, columns)
        v = rng.normal(size=shape) + 1j * rng.normal(size=shape)
        for name in ('K', 'T', 'K_adjoint', 'T_adjoint'):
            target = getattr(old, name)(v)
            before = dict(reference.book.counts)
            result = getattr(cached, name)(v)
            np.testing.assert_allclose(result, target, rtol=1e-12, atol=1e-12)
            for counter in ('L_actions', 'L_adjoint_actions', 'F_actions', 'F_adjoint_actions'):
                assert reference.book.counts[counter] == before.get(counter, 0)
        for name in ('F', 'F_adjoint'):
            np.testing.assert_allclose(getattr(old, name)(v), getattr(cached, name)(v),
                                       rtol=1e-12, atol=1e-12)


    def test_empty_retained_basis_is_exact_identity_without_actions(self):
        reference = _SyntheticReference()
        view = _view(reference)
        empty = np.empty((view.n, 0), complex)
        cached = CachedSchur(view, empty, _config()['OPM'])
        v = np.arange(view.n) + 0.4j
        before = dict(reference.book.counts)
        for name in ('K', 'T', 'K_adjoint', 'T_adjoint'):
            np.testing.assert_array_equal(getattr(cached, name)(v), v)
        assert dict(reference.book.counts) == before


    def test_unitary_gauge_preserves_cached_operators_and_projection_transfer(self):
        reference = _SyntheticReference()
        view = _view(reference)
        U = _random_basis(view.n, 8)
        gauge = _random_basis(8, 8, seed=18)
        original = CachedSchur(view, U, _config()['OPM'])
        changed = CachedSchur(view, U @ gauge, _config()['OPM'])
        v = _random_basis(view.n, 5, seed=7)
        for name in ('K', 'T', 'K_adjoint', 'T_adjoint', 'F', 'F_adjoint'):
            np.testing.assert_allclose(getattr(original, name)(v), getattr(changed, name)(v),
                                       rtol=1e-12, atol=1e-12)
        p1 = Projection(reference.adapter, reference.chi0, U, _config()['OPM'], allow_petrov=False)
        p2 = Projection(reference.adapter, reference.chi0, U @ gauge, _config()['OPM'], allow_petrov=False)
        np.testing.assert_allclose(streamed_projection_matrix(reference, p1, cells_per_block=2),
                                   streamed_projection_matrix(reference, p2, cells_per_block=3),
                                   rtol=1e-12, atol=1e-12)


    def test_source_anchor_P_cancellation_and_approximate_residual_identity(self):
        reference = _SyntheticReference()
        view = _view(reference)
        receiver = view.receiver(8)
        U, rec = source_anchor(view, receiver, _config()['OPM'])
        assert rec['source_count'] == 6 and rec['all_source_capture']
        assert U.shape[1] <= 8 and rec['padding_columns'] == 0
        cached = CachedSchur(view, U, _config()['OPM'])
        b = view.forcing()
        assert la.norm(cached.K(b)) / la.norm(b) < 1e-12
        rng = np.random.default_rng(71)
        material = rng.normal(size=(view.chart.d, 4))
        observation = rng.normal(size=(2 * view.P * view.m, 4))
        seeds = build_fixed_seeds(view, cached, _config()['OPM'], material, observation,
                                  source_anchored=True)
        assert seeds.blocks['P'].shape[1] == 0
        assert seeds.records['P']['structural_zero']
        assert seeds.records['P']['P_relative_to_forcing'] < 1e-12
        # For an approximate source anchor, Kb = K(b-Lj_approx) exactly.
        approx = reference.state.current.T + 1e-3 * (
            rng.normal(size=b.shape) + 1j * rng.normal(size=b.shape))
        Ua = orth(approx)[0]
        ca = CachedSchur(view, Ua, _config()['OPM'])
        residual = b - view.L(approx)
        np.testing.assert_allclose(ca.K(b), ca.K(residual), rtol=1e-10, atol=1e-12)


    def test_seed_blocks_cached_original_identity_and_measured_residual_independence(self):
        reference = _SyntheticReference()
        view = _view(reference)
        noisy_view = _view(reference, residual=np.full_like(reference.data0, 1e7))
        U = view.receiver(8)
        rng = np.random.default_rng(9)
        material = rng.normal(size=(view.chart.d, 4))
        observation = rng.normal(size=(2 * view.P * view.m, 4))
        old = build_fixed_seeds(view, SchurFeedback(view, U, _config()['OPM']),
                                _config()['OPM'], material, observation)
        new = build_fixed_seeds(noisy_view, CachedSchur(noisy_view, U, _config()['OPM']),
                                _config()['OPM'], material, observation)
        for family in 'OPM':
            np.testing.assert_allclose(old.raw_blocks[family], new.raw_blocks[family],
                                       rtol=1e-12, atol=1e-12)
            q, z = old.blocks[family], new.blocks[family]
            np.testing.assert_allclose(q @ q.conj().T, z @ z.conj().T, rtol=1e-11, atol=1e-11)
        assert not new.records['O']['measured_noise_or_residual_used']


    def test_streamed_projection_matches_original_real_transfer_and_adjoint(self):
        reference = _SyntheticReference()
        a = reference.adapter
        U = _random_basis(a.n, 13)
        projection = Projection(a, reference.chi0, U, _config()['OPM'], allow_petrov=False)
        streamed = streamed_projection_matrix(reference, projection, cells_per_block=2)
        original = ReducedJacobian(a, reference.chi0, reference.state, projection).matrix()
        np.testing.assert_allclose(streamed, original, rtol=1e-12, atol=1e-12)
        rng = np.random.default_rng(81)
        d, w = rng.normal(size=a.p), rng.normal(size=2 * a.P * a.m)
        reduced = ReducedJacobian(a, reference.chi0, reference.state, projection)
        np.testing.assert_allclose(w @ (streamed @ d), d @ reduced.pullback(w), rtol=1e-12, atol=1e-12)


    def test_unsafe_core_rejects_without_petrov_jitter_or_inverse_repair(self):
        reference = _SyntheticReference()
        a = reference.adapter
        L = np.eye(a.n, dtype=complex)
        L[0, 0] = 0
        a._operator_L = L
        U = np.eye(a.n, 1, dtype=complex)
        with self.assertRaises(UnsafeCore):
            CachedSchur(_view(reference), U, _config()['OPM'])
        with self.assertRaises(UnsafeCore):
            Projection(a, reference.chi0, U, _config()['OPM'], allow_petrov=False)


    def test_fixed_probes_are_full_material_deterministic_and_independent(self):
        reference = _SyntheticReference()
        probes, rec = fixed_probes(reference, _config())
        again, _ = fixed_probes(reference, _config())
        np.testing.assert_array_equal(probes, again)
        assert probes.shape == (reference.adapter.p, 8)
        np.testing.assert_allclose(la.norm(probes, axis=0), 1.)
        assert {'smooth_real', 'local_real', 'random_mixed'} <= set(rec['labels'])
        assert rec['independent_of_construction']


    def test_build_h1_frozen_repeats_paid_randomized_actions_and_cost_override(self):
        tmp_path = self.directory
        reference = _SyntheticReference()
        direct = {'cold_seconds': 0.25, 'warm_seconds': [0.2] * 5,
                  'accounting': 'synthetic caller fixture'}
        rows, matrices = build_h1(reference, _config(), tmp_path, direct_preparation=direct)
        assert len(rows) == 8 and len(matrices) == 8
        lookup = {row['method']: row for row in rows}
        for row in rows:
            assert row['status'] == 'OK', row
            assert len(row['repeats']) == 6
            assert len(row['warm_wall_seconds']) == 5
            assert all(x['relative_to_cold_matrix'] < 1e-11 for x in row['repeats'])
            assert len(row['transfer_error_per_probe']) == 8
            assert len(row['decoder_weighted_error_per_probe']) == 8
        assert lookup['original_opm']['old_cached_transfer_relative_error'] < 1e-11
        for item in lookup['original_opm']['repeats']:
            seed_counts = item['stages']['seeds']['counts']
            assert seed_counts['L_rhs'] == 6 * 4 + 6
            assert seed_counts['L_adjoint_rhs'] == 6 * 4
        for item in lookup['cached_opm']['repeats']:
            assert item['stages']['seeds']['counts'].get('L_rhs', 0) == 0
            assert item['stages']['seeds']['counts'].get('L_adjoint_rhs', 0) == 0
        for method in ('source_anchored_opm', 'source_anchored_om'):
            assert lookup[method]['metadata']['retained']['all_source_capture']
            assert lookup[method]['metadata']['seed_records']['P']['rank'] == 0
        random = lookup['randomized_transfer']
        assert random['metadata']['requested_rank'] == 32
        assert random['metadata']['rank'] <= 32
        assert not random['metadata']['construction_uses_exact_matrix']
        for item in random['repeats']:
            counts = item['stages']['transfer']['counts']
            assert counts['solve_forward_rhs'] == 6 * 32
            assert counts['solve_adjoint_rhs'] == 6 * random['metadata']['rank']
        assert lookup['direct_adjoint']['metadata']['independent_preparation'] == direct
        assert lookup['direct_adjoint']['transfer_error'] == 0.
        assert (tmp_path / 'H1_METRICS.json').exists()
        assert 'Maxwell' not in (tmp_path / 'H1_METRICS.json').read_text()


    def test_frozen_repeats_cannot_be_silently_reduced(self):
        tmp_path = self.directory
        config = _config()
        config['warm_repeats'] = 1
        with self.assertRaisesRegex(ValueError, 'H1_FROZEN_CONFIG_CONFLICT:warm_repeats'):
            build_h1(_SyntheticReference(), config, tmp_path)


if __name__ == "__main__":
    unittest.main()
