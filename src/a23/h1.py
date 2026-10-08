"""Frozen H1 constructions at the declared reference, with inclusive receipts.

Only the output-by-material transfer is dense.  Local injection contractions
are streamed in cell blocks; no full current-by-material Jacobian is formed.
The exact reference matrix and its decoder are evaluation controls.  Neither
is used to construct a current basis or the randomized transfer.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
import time

import numpy as np
from scipy import linalg as la

from a20.backend import BasisView, pack, unpack
from a20.costs import BudgetExceeded, write_json
from a20.opm import (
    Hierarchy, Projection, SchurFeedback, SeedBundle, orth,
)


class Reference(Protocol):
    adapter: Any
    state: Any
    chi0: np.ndarray
    book: Any
    data0: np.ndarray

    def matrix(self) -> np.ndarray: ...
    def solve_reference(self, rhs: np.ndarray, *, adjoint: bool = False) -> np.ndarray: ...


class CachedSchur(SchurFeedback):
    """Exact cached K, T, K*, T*; construction reuses the original FU/F*U.

    The original retained-core guard and LU remain authoritative.  These four
    methods do not call L or L*, for either vectors or blocks.
    """
    def __init__(self, view, U, config):
        super().__init__(view, U, config)
        self.C = self.U - self.FU
        self.CH = self.U - self.FHU

    def K(self, v):
        if not self.U.shape[1]:
            return np.asarray(v).copy()
        return self.project(v - self.C @ self.coarse(self.U.conj().T @ v))

    def T(self, v):
        if not self.U.shape[1]:
            return np.asarray(v).copy()
        pv = self.project(v)
        return pv - self.U @ self.coarse(self.CH.conj().T @ pv)

    def T_adjoint(self, v):
        if not self.U.shape[1]:
            return np.asarray(v).copy()
        return self.project(v - self.CH @ self.coarse(self.U.conj().T @ v, True))

    def K_adjoint(self, v):
        if not self.U.shape[1]:
            return np.asarray(v).copy()
        pv = self.project(v)
        return pv - self.U @ self.coarse(self.C.conj().T @ pv, True)


# These labels distinguish operator applications from direct linear solves.
# The legacy aggregate named Maxwell_matvec_rhs is deliberately not exported.
_COUNTER_NAMES = {
    'L_actions': 'L_rhs', 'L_adjoint_actions': 'L_adjoint_rhs',
    'F_actions': 'F_rhs', 'F_adjoint_actions': 'F_adjoint_rhs',
    'S_actions': 'S_rhs', 'S_adjoint_actions': 'S_adjoint_rhs',
    'full_tangent_RHS': 'solve_forward_rhs',
    'full_adjoint_RHS': 'solve_adjoint_rhs',
    'full_tangent_receiver_rhs': 'S_rhs',
    'full_adjoint_receiver_rhs': 'S_adjoint_rhs',
}


def _cost_delta(book, before):
    raw = book.delta(before)
    counts = {}
    for key, value in raw['counts'].items():
        if not value or key == 'Maxwell_matvec_rhs':
            continue
        name = _COUNTER_NAMES.get(key, key)
        counts[name] = counts.get(name, 0) + int(value)
    return {'counts': counts,
            'exclusive_walls': {k: v for k, v in raw['exclusive_walls'].items() if v}}


def _stage(book, name, action):
    before = book.snapshot()
    book.synchronize()
    started = time.perf_counter()
    with book.span('h1_' + name):
        value = action()
    book.synchronize()
    elapsed = time.perf_counter() - started
    return value, {'wall_seconds': elapsed, **_cost_delta(book, before)}


def _relative(left, right):
    return float(la.norm(left - right) / max(la.norm(right), 1e-300))


def _rng(config, parent, domain):
    seed = [int(config['master_seed']), int(parent), int(domain)]
    return np.random.default_rng(np.random.SeedSequence(seed)), seed


def _normalize_columns(value):
    value = np.asarray(value, float)
    norms = la.norm(value, axis=0)
    if np.any(norms <= 0) or not np.all(np.isfinite(norms)):
        raise ValueError('ZERO_OR_NONFINITE_FIXED_PROBE')
    return value / norms[None, :]


def fixed_probes(reference, config):
    """Eight independent full-material evaluation directions, before results.

    The first five use only the geometry (two broad, two local, one edge);
    the last three are independent Gaussian real/imaginary/mixed directions.
    These are distinct from every construction probe and use the full chart.
    """
    adapter = reference.adapter
    points = np.asarray(adapter.problem.points, float)
    N = adapter.chart.n
    if adapter.chart.Q is not None or adapter.chart.d != 2 * N:
        raise ValueError('H1_REQUIRES_FULL_CELL_REAL_MASS_CHART')
    if points.shape != (N, 3) or not N:
        raise ValueError('H1_INVALID_GEOMETRY')
    center = points.mean(axis=0)
    extent = max(float(np.max(la.norm(points - center, axis=1))), 1e-12)
    broad = np.exp(-la.norm(points - center, axis=1) ** 2 / (0.7 * extent) ** 2)
    # A geometry-selected cell, without material support or evaluator labels.
    target = center + np.array([0.4, -0.2, 0.1]) * extent
    local_center = points[np.argmin(la.norm(points - target, axis=1))]
    local = np.exp(-la.norm(points - local_center, axis=1) ** 2 / (0.18 * extent) ** 2)
    edge = broad * (points[:, 0] - center[0]) / extent
    if la.norm(edge) <= 1e-14:
        axis = int(np.argmax(np.ptp(points, axis=0)))
        edge = broad * (points[:, axis] - center[axis]) / extent
    if la.norm(edge) <= 1e-14:
        # A one-cell tiny test cannot have a geometric edge.
        edge = np.ones(N)
    rng, seed = _rng(config, adapter.problem.parent_id, 701)
    zero = np.zeros(N)
    probes = np.column_stack((
        np.r_[broad, zero], np.r_[zero, broad],
        np.r_[local, zero], np.r_[zero, local], np.r_[edge, zero],
        np.r_[rng.normal(size=N), zero], np.r_[zero, rng.normal(size=N)],
        rng.normal(size=2 * N),
    ))
    return _normalize_columns(probes), {
        'seed': seed, 'independent_of_construction': True,
        'labels': ['smooth_real', 'smooth_imag', 'local_real', 'local_imag',
                   'edge_real', 'random_real', 'random_imag', 'random_mixed'],
        'material_chart': 'full-cell real mass normalized [ReN,ImN]',
    }


def _construction_probes(reference, config):
    a = reference.adapter
    rng, seed = _rng(config, a.problem.parent_id, 702)
    material = _normalize_columns(rng.normal(size=(a.chart.d, 4)))
    observation = _normalize_columns(rng.normal(size=(2 * a.P * a.m, 4)))
    return material, observation, {'seed': seed,
        'material_probes': 4, 'observation_probes': 4,
        'observation_provenance': 'fixed independent whitened-data Gaussian probes',
        'measured_noise_or_residual_used': False}


def source_anchor(view, receiver_U, config):
    """Capture every declared reference current, then fill from receivers.

    Missing or dependent receiver columns do not cause fabricated padding.
    """
    current = np.asarray(view._state.current, complex).T
    if current.shape != (view.n, view.P):
        raise ValueError('REFERENCE_CURRENT_SHAPE')
    rtol = config.get('orthogonal_rank_rtol', 1e-10)
    retained = int(config['retained_rank'])
    with view.book.span('h1_source_anchor_orthogonalization', qr_columns=view.P):
        view.book.counts['svd_calls'] += int(current.shape[1] > 0)
        sources, source_rec = orth(current, rtol=rtol)
    if sources.shape[1] > retained:
        raise ValueError('SOURCE_SPAN_EXCEEDS_FROZEN_RETAINED_BUDGET')
    with view.book.span('h1_source_receiver_fill', qr_columns=receiver_U.shape[1]):
        view.book.counts['svd_calls'] += int(receiver_U.shape[1] > 0)
        receiver, receiver_rec = orth(receiver_U, against=sources,
                                      rank=retained - sources.shape[1], rtol=rtol)
    U = np.column_stack((sources, receiver))
    capture = float(la.norm(current - U @ (U.conj().T @ current)) /
                    max(la.norm(current), 1e-300))
    if capture > 10 * rtol:
        raise ValueError('SOURCE_ANCHOR_DOES_NOT_CAPTURE_ALL_REFERENCE_CURRENTS')
    return U, {
        'kind': 'reference_source_span_then_receiver_fill',
        'requested_rank': retained, 'rank': U.shape[1],
        'source_count': view.P, 'source_rank': sources.shape[1],
        'remaining_receiver_budget': retained - sources.shape[1],
        'receiver_rank_added': receiver.shape[1],
        'all_source_capture_relative_error': capture,
        'all_source_capture': True, 'padding_columns': 0,
        'source_deflation': source_rec, 'receiver_deflation': receiver_rec,
    }


def _seed_redundancy(view, raw_bases, raw_blocks, blocks, rtol):
    pairs = {}
    for left, right in (('O', 'P'), ('O', 'M'), ('P', 'M')):
        q, z = raw_bases[left], raw_bases[right]
        if q.shape[1] and z.shape[1]:
            angles = la.subspace_angles(q, z)
            overlap = float(la.norm(q.conj().T @ z) ** 2)
            residual = float(la.norm(raw_blocks[right] - q @ (q.conj().T @ raw_blocks[right])) /
                             max(la.norm(raw_blocks[right]), 1e-300))
            pairs[left + right] = {'raw_principal_angles_radians': angles.tolist(),
                'raw_overlap_frobenius_squared': overlap,
                'right_raw_incremental_relative_residual': residual}
        else:
            pairs[left + right] = {'raw_principal_angles_radians': [],
                'raw_overlap_frobenius_squared': 0.,
                'right_raw_incremental_relative_residual': None,
                'empty_family': True}
    joined_raw = np.column_stack([raw_bases[k] for k in 'OPM'])
    joined_capped = np.column_stack([blocks[k] for k in 'OPM'])
    view.book.counts['qr_columns'] += joined_raw.shape[1]
    view.book.counts['svd_calls'] += int(joined_raw.shape[1] > 0)
    raw_joint, joint_record = orth(joined_raw, rtol=rtol)
    return {'pairwise': pairs,
            'raw_rank_sum': sum(raw_bases[k].shape[1] for k in 'OPM'),
            'raw_joint_rank': raw_joint.shape[1],
            'raw_joint_deflation': joint_record,
            'capped_rank_sum': sum(blocks[k].shape[1] for k in 'OPM'),
            'raw_concatenated_columns': joined_raw.shape[1],
            'capped_concatenated_columns': joined_capped.shape[1]}


def build_fixed_seeds(view, schur, config, material, observation, *, families='OPM',
                      source_anchored=False):
    """Original seed formulas with reference-only O and explicit zero-P audit."""
    budgets = {k: int(config['seed_rank_' + k]) if k in families else 0 for k in 'OPM'}
    raw = {k: np.empty((view.n, 0), complex) for k in 'OPM'}
    forcing_norm = None
    if budgets['M']:
        bm = view.B(material)
        raw['M'] = schur.K(bm.transpose(1, 0, 2).reshape(view.n, -1))
    if budgets['O']:
        oy = unpack(view._a.whiten(observation, adjoint=True), view.P, view.m)
        so = view.S_adjoint(oy.transpose(1, 0, 2).reshape(view.m, -1))
        raw['O'] = schur.T_adjoint(so)
    if budgets['P']:
        forcing = view.forcing()
        forcing_norm = float(la.norm(forcing))
        raw['P'] = schur.K(forcing)
    blocks, records, raw_bases = {}, {}, {}
    rtol = config.get('orthogonal_rank_rtol', 1e-10)
    for name in 'OPM':
        value = raw[name]
        with view.book.span('h1_seed_' + name + '_compression',
                            **{'seed_' + name + '_input_rhs': value.shape[1],
                               'qr_columns': value.shape[1]}):
            view.book.counts['svd_calls'] += int(value.shape[1] > 0)
            full, rec = orth(value, against=schur.U, rtol=rtol)
        raw_rank = full.shape[1]
        p_relative = (float(la.norm(value) / max(forcing_norm, 1e-300))
                      if name == 'P' and forcing_norm is not None else None)
        structural_zero = bool(name == 'P' and source_anchored and budgets['P'] and
                               p_relative <= config.get('identity_rtol', 1e-10))
        if name == 'P' and source_anchored and budgets['P'] and not structural_zero:
            raise ValueError('SOURCE_ANCHORED_P_CANCELLATION_FAILED')
        if structural_zero:
            # Relative to the forcing, not to its roundoff-sized residual.
            full = np.empty((view.n, 0), complex)
        q = full[:, :budgets[name]]
        rec.update(raw_rank_own_scale=raw_rank, raw_effective_rank=full.shape[1],
                   rank=q.shape[1], requested_rank=budgets[name],
                   input_columns=value.shape[1],
                   deflated=value.shape[1] - q.shape[1],
                   rank_cap_deflated=max(0, full.shape[1] - q.shape[1]),
                   source_count=view.P, structural_zero=structural_zero,
                   original_column_norms=la.norm(value, axis=0).tolist(),
                   svd_shape=[view.n, value.shape[1]],
                   raw_frobenius_norm=float(la.norm(value)),
                   P_relative_to_forcing=p_relative,
                   provenance={'O': 'independent fixed whitened-data Gaussian probes, T*S*',
                               'P': 'all known reference illumination forcing, Kb',
                               'M': 'independent full-cell real physical-L2 probes, KB'}[name],
                   measured_noise_or_residual_used=False)
        blocks[name], records[name], raw_bases[name] = q, rec, full
    seeds = SeedBundle(blocks, records, list(config.get('_h1_seed', [])), material, observation)
    seeds.raw_blocks = raw
    with view.book.span('h1_seed_redundancy_audit'):
        seeds.redundancy = _seed_redundancy(view, raw_bases, raw, blocks, rtol)
    return seeds


def streamed_projection_matrix(reference, projection, *, cells_per_block=128):
    """S Z (Z*LZ)^-1 Z*B, contracted before full material expansion."""
    a = reference.adapter
    if a.chart.Q is not None:
        raise ValueError('H1_REQUIRES_FULL_CELL_REAL_MASS_CHART')
    if cells_per_block < 1:
        raise ValueError('POSITIVE_CELL_BLOCK_REQUIRED')
    projection.check()
    N, r = a.chart.n, projection.Z.shape[1]
    m_real, p = 2 * a.P * a.m, a.chart.d
    output_bytes = m_real * p * 8
    if output_bytes > 256 * 1024 ** 2:
        raise MemoryError('H1_TRANSFER_MEMORY_PREFLIGHT')
    result = np.empty((m_real, p), float)
    f = a.injection_factor(reference.chi0, reference.state)
    wh = projection.W.conj().T.reshape(r, N, 3)
    with a.book.span('h1_streamed_reduced_material_data_matrix',
                     compressed_B_current_columns=a.P * r):
        for start in range(0, N, cells_per_block):
            end = min(N, start + cells_per_block)
            c = np.einsum('qtc,ptc->pqt', wh[:, start:end], f[:, start:end])
            c /= np.sqrt(a.problem.volume)
            b = np.concatenate((c, 1j * c), axis=2)
            coeff = projection.solve(b.transpose(1, 0, 2).reshape(r, -1))
            coeff = coeff.reshape(r, a.P, -1).transpose(1, 0, 2)
            output = np.einsum('mr,prk->pmk', projection.SZ, coeff)
            data = a.whiten(pack(output))
            width = end - start
            result[:, start:end] = data[:, :width]
            result[:, N + start:N + end] = data[:, width:]
        a.book.counts['transfer_bytes'] += result.nbytes
    return result


def _true_linear(reference, directions):
    """Pay primal JVPs even when reference.matrix() is already cached."""
    a = reference.adapter
    d = np.asarray(directions)
    if d.ndim != 2 or d.shape[0] != a.chart.d or np.iscomplexobj(d):
        raise ValueError('REAL_FULL_MATERIAL_BLOCK_REQUIRED')
    b = a.apply_B(reference.chi0, reference.state, d)
    c = reference.solve_reference(b.transpose(1, 0, 2).reshape(a.n, -1))
    output = a.apply_S(c).reshape(a.m, a.P, d.shape[1]).transpose(1, 0, 2)
    return a.whiten(pack(output))


def _randomized_transfer(reference, config):
    a = reference.adapter
    requested = int(config['randomized_transfer_rank'])
    rng, seed = _rng(config, a.problem.parent_id, 703)
    omega = rng.normal(size=(a.chart.d, requested))
    Y = _true_linear(reference, omega)
    with a.book.span('h1_randomized_data_range_svd', qr_columns=requested):
        U, sv, _ = la.svd(Y, full_matrices=False, check_finite=True)
    threshold = config['OPM'].get('orthogonal_rank_rtol', 1e-10) * (sv[0] if len(sv) else 0.)
    rank = min(requested, int(np.count_nonzero(sv > threshold)))
    if not rank:
        raise ValueError('EMPTY_RANDOMIZED_REFERENCE_DATA_RANGE')
    Uy = U[:, :rank]
    # Source-mixed Uy requires P adjoint RHS per column; the original adapter
    # charges these solves.  A cached exact material matrix is not consulted.
    V = a.full_adjoint_action(reference.chi0, reference.state, Uy)
    A = Uy @ V.T
    a.book.counts['transfer_bytes'] += A.nbytes
    return A, {
        'rank': rank, 'requested_rank': requested, 'training_probe_count': requested,
        'seed': seed, 'training_distribution': 'full-material standard Gaussian',
        'training_singular_values': sv.tolist(), 'range_threshold': float(threshold),
        'formula': 'Uy @ (J.T @ Uy).T', 'auto_upscaled': False,
        'construction_uses_exact_matrix': False,
        'paid_primal_rhs': a.P * requested, 'paid_adjoint_rhs': a.P * rank,
        'data_basis': Uy, 'training_probes': omega,
    }


@dataclass
class _GramDecoder:
    """Evaluation-only Tikhonov, using a data Gram and one positive solve."""
    A: np.ndarray
    factor: Any
    lam: float

    def decode(self, data):
        return self.A.T @ la.cho_solve(self.factor, np.asarray(data, float))


def _evaluation_decoder(reference, exact, config):
    decoder = getattr(reference, 'evaluation_decoder', None)
    if decoder is not None:
        if not hasattr(decoder, 'decode'):
            raise ValueError('EVALUATION_DECODER_MUST_HAVE_DECODE')
        return decoder, {'source': 'caller_prepared_reference_decoder',
                         'lambda': float(decoder.lam),
                         'relative': float(config['tikhonov_relative']),
                         'matrix': 'exact declared reference transfer',
                         'preparation_attribution': 'caller'}
    with reference.book.span('h1_common_reference_evaluation_decoder', decoder_prepare_data_gram=1):
        gram = exact @ exact.T
        top = float(la.eigh(gram, subset_by_index=[len(gram) - 1, len(gram) - 1],
                            eigvals_only=True, check_finite=False)[0])
        lam = float(config['tikhonov_relative']) * top
        if not np.isfinite(lam) or lam <= 0:
            raise ValueError('ZERO_REFERENCE_TRANSFER')
        gram.flat[::len(gram) + 1] += lam
        factor = la.cho_factor(gram, check_finite=False)
    return _GramDecoder(exact, factor, lam), {
        'source': 'shared_exact_reference_data_gram', 'lambda': lam,
        'relative': float(config['tikhonov_relative']),
        'rule': 'lambda = relative * lambda_max(A_reference A_reference.T)',
        'material_gram_allocated': False}


def _probe_metrics(A, probes, exact_outputs, decoded_exact, decoder,
                   dual_probes, exact_dual):
    output = A @ probes
    error = output - exact_outputs
    decoded_error = decoder.decode(error)
    output_norms = la.norm(exact_outputs, axis=0)
    decoded_norms = la.norm(decoded_exact, axis=0)
    dual_error = A.T @ dual_probes - exact_dual
    return {
        'transfer_error': float(la.norm(error) / max(la.norm(exact_outputs), 1e-300)),
        'transfer_error_per_probe': (la.norm(error, axis=0) / np.maximum(output_norms, 1e-300)).tolist(),
        'decoder_weighted_error': float(la.norm(decoded_error) / max(la.norm(decoded_exact), 1e-300)),
        'decoder_weighted_error_per_probe': (la.norm(decoded_error, axis=0) /
                                           np.maximum(decoded_norms, 1e-300)).tolist(),
        'decoder_weighting': 'common exact-reference physical-L2 Tikhonov decoder',
        'dual_response_error': float(la.norm(dual_error) / max(la.norm(exact_dual), 1e-300)),
        'dual_response_error_per_probe': (la.norm(dual_error, axis=0) /
                                         np.maximum(la.norm(exact_dual, axis=0), 1e-300)).tolist(),
        'evaluation_probe_count': probes.shape[1], 'empirical_probe_metric': True,
        'no_truth_or_old_GN_used': True,
    }


def _charge_hierarchy_orthogonalizations(book, hierarchy, record):
    # Upstream spans time these SVDs, but omit their column counts.
    columns = sum(x['input_columns'] for x in record['joint_deflation'])
    shapes = [[hierarchy.view.n, x['input_columns']] for x in record['joint_deflation']
              if x['input_columns']]
    for stream in hierarchy.streams.values():
        for rec in stream.recurrence:
            if 'deflation' in rec:
                count = rec['deflation']['input_columns']
                columns += count
                if count:
                    shapes.append([hierarchy.view.n, count])
    book.counts['qr_columns'] += columns
    book.counts['svd_calls'] += len(shapes)
    record['svd_shapes'] = shapes


def _frozen_config(config):
    expected = {'cold_repeats': 1, 'warm_repeats': 5,
                'randomized_transfer_rank': 32, 'independent_transfer_probes': 8}
    for key, value in expected.items():
        if config.get(key) != value:
            raise ValueError('H1_FROZEN_CONFIG_CONFLICT:' + key)
    opm = dict(config['OPM'])
    for key, value in {'degree': 1, 'seed_rank_O': 4, 'seed_rank_P': 4,
                       'seed_rank_M': 4, 'retained_rank': 8}.items():
        if opm.get(key) != value:
            raise ValueError('H1_FROZEN_CONFIG_CONFLICT:OPM.' + key)
    if float(config['tikhonov_relative']) <= 0:
        raise ValueError('TIKHONOV_POSITIVE_REGULARIZATION_REQUIRED')
    opm['master_seed'] = int(config['master_seed'])
    opm['identity_rtol'] = float(config.get('identity_rtol', 1e-10))
    return opm


def _write_candidate(path, A, basis):
    arrays = {'matrix': A}
    if basis is not None:
        arrays['basis'] = basis
    np.savez(path, **arrays)
    return path.stat().st_size


def build_h1(reference, config, output_dir, *, direct_preparation=None):
    """Return ``(per_arm_rows, real_transfer_matrices)`` for the frozen H1.

    Every non-direct arm is actually constructed cold1/warm5, with identical
    probes and charged actions, including matrix export.  Receiver geometry
    and reference/evaluation controls are shared actual costs.  Each arm also
    reports their independent-deployment attribution separately.  The caller
    supplies direct receiver-adjoint/matrix cold1/warm5 preparation receipts;
    reusing the evaluation matrix here is never labeled a fresh construction.
    This function makes no scientific or gate decision.
    """
    opm = _frozen_config(config)
    a, book = reference.adapter, reference.book
    if a.P != 6:
        raise ValueError('H1_FROZEN_SOURCE_COUNT_REQUIRES_ALL_SIX_REFERENCE_CURRENTS')
    if a.chart.Q is not None:
        raise ValueError('H1_REQUIRES_FULL_CELL_REAL_MASS_CHART')
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    shared_before = book.snapshot()
    shared_started = time.perf_counter()
    exact, exact_cost = _stage(book, 'shared_exact_evaluation_matrix', reference.matrix)
    exact = np.asarray(exact, float)
    if exact.shape != (2 * a.P * a.m, a.chart.d) or not np.all(np.isfinite(exact)):
        raise ValueError('INVALID_EXACT_REFERENCE_TRANSFER')
    decoder_pair, decoder_cost = _stage(book, 'shared_evaluation_decoder',
                                       lambda: _evaluation_decoder(reference, exact, config))
    decoder, decoder_info = decoder_pair
    probes, probe_info = fixed_probes(reference, config)
    material, observation, construction_info = _construction_probes(reference, config)
    dual_rng, dual_seed = _rng(config, a.problem.parent_id, 704)
    dual_probes = _normalize_columns(dual_rng.normal(size=(exact.shape[0], probes.shape[1])))
    probe_info['independent_dual_seed'] = dual_seed
    opm['_h1_seed'] = construction_info['seed']
    view = BasisView(a, reference.chi0, reference.state, np.zeros_like(reference.data0))
    receiver_U, geometry_cost = _stage(book, 'shared_receiver_geometry',
                                       lambda: view.receiver(opm['retained_rank']))
    exact_outputs = exact @ probes
    exact_dual = exact.T @ dual_probes
    decoded_exact = decoder.decode(exact_outputs)
    def export_fixed_probes():
        path = output_dir / 'H1_FIXED_PROBES.npz'
        np.savez(path, evaluation=probes, material=material, observation=observation,
                 exact_outputs=exact_outputs, dual_evaluation=dual_probes, exact_dual=exact_dual)
        book.counts['cache_write_bytes'] += path.stat().st_size
    _, probe_export_cost = _stage(book, 'shared_fixed_probe_export', export_fixed_probes)
    shared_actual = {'wall_seconds': time.perf_counter() - shared_started,
                     **_cost_delta(book, shared_before),
                     'exact_matrix': exact_cost, 'evaluation_decoder': decoder_cost,
                     'receiver_geometry': geometry_cost,
                     'fixed_probe_export': probe_export_cost,
                     'accounting': 'charged once, not the sum of per-arm attributions'}
    direct_preparation = (direct_preparation if direct_preparation is not None else
                          getattr(reference, 'direct_preparation', None))

    specs = [
        ('original_opm', 'OPM', False, SchurFeedback),
        ('cached_opm', 'OPM', False, CachedSchur),
        ('source_anchored_opm', 'OPM', True, CachedSchur),
        ('source_anchored_om', 'OM', True, CachedSchur),
        ('mp', 'MP', False, CachedSchur),
        ('m_only', 'M', False, CachedSchur),
        ('randomized_transfer', None, False, None),
        ('direct_adjoint', None, False, None),
    ]
    rows, matrices = [], {}
    for name, families, anchored, schur_class in specs:
        repeat_rows = []
        last_A = None
        cold_A = None
        last_metadata = {}
        for repeat in range(1 + int(config['warm_repeats'])):
            temperature = 'cold' if repeat == 0 else 'warm'
            before = book.snapshot()
            started = time.perf_counter()
            stages, metadata, basis = {}, {}, None
            try:
                with book.scope(f'h1/{name}/{temperature}/{repeat}'):
                    if families is not None:
                        if anchored:
                            pair, stages['retained_basis'] = _stage(
                                book, 'retained_basis', lambda: source_anchor(view, receiver_U, opm))
                            U, retained_info = pair
                        else:
                            U, stages['retained_basis'] = _stage(book, 'retained_basis', receiver_U.copy)
                            retained_info = {'kind': 'receiver_geometry', 'rank': U.shape[1],
                                'requested_rank': opm['retained_rank'], 'padding_columns': 0}
                        schur, stages['schur'] = _stage(book, 'schur', lambda: schur_class(view, U, opm))
                        seeds, stages['seeds'] = _stage(book, 'seeds', lambda: build_fixed_seeds(
                            view, schur, opm, material, observation, families=families,
                            source_anchored=anchored))
                        hierarchy = Hierarchy(view, schur, seeds, opm, families=families)
                        def grow():
                            Z, rec = hierarchy.at_degree(opm['degree'])
                            _charge_hierarchy_orthogonalizations(book, hierarchy, rec)
                            return Z, rec
                        pair, stages['basis'] = _stage(book, 'basis', grow)
                        basis, hierarchy_info = pair
                        projection, stages['projection'] = _stage(book, 'projection', lambda: Projection(
                            a, reference.chi0, basis, opm, allow_petrov=False))
                        A, stages['transfer'] = _stage(book, 'transfer',
                            lambda: streamed_projection_matrix(reference, projection))
                        metadata = {'families': families, 'degree': opm['degree'],
                            'rank': basis.shape[1], 'retained': retained_info,
                            'seed_records': seeds.records, 'seed_redundancy': seeds.redundancy,
                            'hierarchy': hierarchy_info, 'projected_core': projection.stability,
                            'projection_kind': projection.kind, 'fallback': projection.fallback,
                            'retained_core': schur.stability, 'schur': schur_class.__name__,
                            'construction_uses_exact_matrix': False,
                            'streamed_cell_block_size': 128,
                            'transfer_output_bytes': A.nbytes,
                            'full_current_material_J_allocated': False}
                    elif name == 'randomized_transfer':
                        pair, stages['transfer'] = _stage(book, 'randomized_transfer',
                                                         lambda: _randomized_transfer(reference, config))
                        A, metadata = pair
                        basis = metadata.pop('data_basis')
                        training = metadata.pop('training_probes')
                        if repeat == 0:
                            def export_training():
                                path = output_dir / 'H1_RANDOMIZED_TRAINING.npz'
                                np.savez(path, material=training)
                                book.counts['cache_write_bytes'] += path.stat().st_size
                            _, stages['training_io'] = _stage(book, 'randomized_training_export', export_training)
                    else:
                        def reuse_exact():
                            book.counts['cache_read_bytes'] += exact.nbytes
                            return exact.copy()
                        A, stages['shared_matrix_read'] = _stage(book, 'shared_matrix_read', reuse_exact)
                        metadata = {'rank': None, 'exact_control': True,
                            'matrix_construction_status': 'CALLER_MEASURED' if direct_preparation is not None
                                                          else 'CALLER_COST_REQUIRED',
                            'independent_preparation': direct_preparation,
                            'local_matrix_step': 'evaluation-control cache copy only',
                            'no_fresh_construction_claim': True}
                    metrics, stages['evaluation'] = _stage(book, 'independent_probe_evaluation',
                        lambda: _probe_metrics(A, probes, exact_outputs, decoded_exact, decoder,
                                              dual_probes, exact_dual))
                    def export():
                        written = _write_candidate(output_dir / (name + '.npz'), A, basis)
                        book.counts['cache_write_bytes'] += written
                        return written
                    _, stages['io'] = _stage(book, 'candidate_export', export)
                elapsed = time.perf_counter() - started
                item = {'repeat': repeat, 'temperature': temperature, 'status': 'OK',
                    'wall_seconds': elapsed, 'stages': stages, **_cost_delta(book, before), **metrics}
                item['encoder_preparation_wall_seconds'] = sum(
                    rec['wall_seconds'] for stage, rec in stages.items() if stage != 'evaluation')
                item['evaluation_wall_seconds'] = stages['evaluation']['wall_seconds']
                item['seed_redundancy_audit_wall_seconds'] = stages.get('seeds', {}).get(
                    'exclusive_walls', {}).get('h1_seed_redundancy_audit', 0.)
                if cold_A is None:
                    cold_A = A.copy()
                item['relative_to_cold_matrix'] = _relative(A, cold_A)
                last_A, last_metadata = A, metadata
            except BudgetExceeded:
                # The parent owns the stop policy; never continue past its book.
                raise
            except Exception as exc:
                book.counts['failed_attempts'] += 1
                item = {'repeat': repeat, 'temperature': temperature, 'status': 'FAILED',
                    'error': type(exc).__name__ + ': ' + str(exc),
                    'wall_seconds': time.perf_counter() - started,
                    'stages': stages, **_cost_delta(book, before)}
            repeat_rows.append(item)
        good = [x for x in repeat_rows if x['status'] == 'OK']
        row = {'method': name, 'parent_id': int(a.problem.parent_id),
            'status': 'OK' if len(good) == len(repeat_rows) else 'FAILED',
            'cold_repeats': 1, 'warm_repeats': config['warm_repeats'],
            'repeats': repeat_rows, 'metadata': last_metadata,
            'construction_probes': construction_info, 'evaluation_probes': probe_info,
            'evaluation_decoder': decoder_info,
            'shared_receiver_geometry_attribution': geometry_cost if families else None,
            'shared_actual_cost': shared_actual,
            'reference_preparation_attribution': 'caller measured common declared-reference state',
            'wall_includes_decoder_evaluation_and_io': True,
            'cold_definition': 'first construction after shared reference and receiver geometry',
            'encoder_preparation_includes_io_and_redundancy_audit': True,
            'decoder_preparation_status': 'COMMON_FIXED_EVALUATION_DECODER_REUSED',
            'gate_decision': 'PARENT_ONLY'}
        if good:
            row.update({key: good[0][key] for key in (
                'transfer_error', 'transfer_error_per_probe', 'decoder_weighted_error',
                'decoder_weighted_error_per_probe', 'evaluation_probe_count',
                'dual_response_error', 'dual_response_error_per_probe')})
            row['cold_wall_seconds'] = good[0]['wall_seconds'] if good[0]['temperature'] == 'cold' else None
            row['warm_wall_seconds'] = [x['wall_seconds'] for x in good if x['temperature'] == 'warm']
            row['cold_encoder_preparation_wall_seconds'] = (
                good[0]['encoder_preparation_wall_seconds'] if good[0]['temperature'] == 'cold' else None)
            row['warm_encoder_preparation_wall_seconds'] = [
                x['encoder_preparation_wall_seconds'] for x in good if x['temperature'] == 'warm']
            matrices[name] = last_A
        rows.append(row)
    if 'original_opm' in matrices and 'cached_opm' in matrices:
        equality = _relative(matrices['cached_opm'], matrices['original_opm'])
        for row in rows:
            if row['method'] in ('original_opm', 'cached_opm'):
                row['old_cached_transfer_relative_error'] = equality
    with book.span('h1_final_metrics_export'):
        path = output_dir / 'H1_METRICS.json'
        write_json(path, rows)
        book.counts['cache_write_bytes'] += path.stat().st_size
    return rows, matrices
