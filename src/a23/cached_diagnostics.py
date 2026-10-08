"""Offline diagnostics from saved arrays only, with a standalone CPU receipt.

No physics/decoder is executed, no labels are generated, and rejected saved
estimates are included.  The old chart is exactly offline.old_chart_basis;
its projection is applied as W(W.T x), without allocating W W.T densely.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import time

import numpy as np

from .offline import old_chart_basis


_IMAGE_PATTERN = re.compile(r'^scene_(\d+)_t([0-9.]+)_(.+)\.npz$')
_CALIBRATION_PATTERN = re.compile(r'^scene_(\d+)_calibration\.npz$')
_RESERVED = {'truth_OFFLINE', 'measured', 'noise', 'source_gain', 'receiver_gain',
             'clean', 'raw_field', 'sigma_physical', 'sigma_whitened'}
_METHODS = ('dressed_linear_chi', 'vanilla_IBS2', 'A23_compressed_feedback')
_OUTPUTS = ('CHART_DIAGNOSTICS.csv', 'FEASIBILITY_DIAGNOSTICS.csv',
            'QUADRATIC_CORRECTION_DIAGNOSTICS.csv', 'SKETCH_MEAN_DIAGNOSTICS.csv')
_IDENTITY_TOLERANCE = 1e-9


def _number(value):
    if value is None or value == '':
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _ratio(numerator, denominator):
    return numerator / denominator if denominator > 0 else None


def _mass_vector(material, volume):
    material = np.asarray(material)
    return np.sqrt(volume) * np.concatenate((material.real, material.imag))


def _split_energy(vector, W):
    inside = W @ (W.T @ vector)
    outside = vector - inside
    total_sq = float(vector @ vector)
    inside_sq, outside_sq = float(inside @ inside), float(outside @ outside)
    energy_absolute = abs(total_sq - inside_sq - outside_sq)
    energy_relative = energy_absolute / max(total_sq, 1e-300)
    orthogonality = abs(float(inside @ outside)) / max(total_sq, 1e-300)
    if energy_relative > _IDENTITY_TOLERANCE or orthogonality > _IDENTITY_TOLERANCE:
        raise AssertionError('OLD_CHART_ENERGY_OR_ORTHOGONALITY_IDENTITY_FAILED')
    return {
        'inside_norm': float(np.linalg.norm(inside)),
        'outside_norm': float(np.linalg.norm(outside)),
        'total_norm': float(np.linalg.norm(vector)),
        'inside_fraction': _ratio(inside_sq, total_sq),
        'outside_fraction': _ratio(outside_sq, total_sq),
        'energy_absolute_residual': energy_absolute,
        'energy_relative_residual': energy_relative,
        'in_out_orthogonality_relative_residual': orthogonality,
    }


def _condition(path):
    match = _IMAGE_PATTERN.match(path.name)
    if match:
        return int(match[1]), float(match[2]), match[3]
    match = _CALIBRATION_PATTERN.match(path.name)
    if match:
        return int(match[1]), 1., '20dB_calibration'
    raise ValueError('UNREGISTERED_SAVED_IMAGE_NAME:' + path.name)


def _published_rows(path):
    with path.open(newline='', encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle))
    index = {}
    for row in rows:
        key = (int(row['scene']), float(row['t']), row['noise'], row['method'])
        if key in index:
            raise ValueError('DUPLICATE_PUBLISHED_IMAGE_ROW:' + repr(key))
        index[key] = row
    return index


def _chart_row(base, estimate, truth, background, volume, W, truth_split, W_error):
    error = _mass_vector(estimate - truth, volume)
    finite = bool(np.all(np.isfinite(error)))
    split = _split_energy(error, W) if finite else {}
    inside_error, outside_error = split.get('inside_norm'), split.get('outside_norm')
    inside_truth, outside_truth = truth_split['inside_norm'], truth_split['outside_norm']
    return {
        **base, 'diagnostic_status': 'COMPUTED' if finite else 'NONFINITE_ESTIMATE_RETAINED',
        'chart_source': 'a23.offline.old_chart_basis(points, volume)',
        'chart_rank': W.shape[1], 'chart_orthogonality_error': W_error,
        'material_metric': 'sqrt(volume) * [Re(delta chi), Im(delta chi)]',
        'truth_energy_reference': 'truth minus frozen declared background',
        'truth_delta_full_mass_norm': truth_split['total_norm'],
        'truth_delta_in_chart_mass_norm': inside_truth,
        'truth_delta_out_chart_mass_norm': outside_truth,
        'truth_delta_in_chart_energy_fraction': truth_split['inside_fraction'],
        'truth_delta_out_chart_energy_fraction': truth_split['outside_fraction'],
        'full_absolute_mass_error': split.get('total_norm'),
        'in_chart_absolute_mass_error': inside_error,
        'out_chart_absolute_mass_error': outside_error,
        'in_chart_delta_NRMSE': _ratio(inside_error, inside_truth) if finite else None,
        'out_chart_delta_NRMSE': _ratio(outside_error, outside_truth) if finite else None,
        'in_chart_denominator_status': 'NONZERO' if inside_truth > 0 else 'ZERO_UNDEFINED',
        'out_chart_denominator_status': 'NONZERO' if outside_truth > 0 else 'ZERO_UNDEFINED',
        'truth_energy_absolute_decomposition_residual': truth_split['energy_absolute_residual'],
        'truth_energy_relative_decomposition_residual': truth_split['energy_relative_residual'],
        'error_energy_absolute_decomposition_residual': split.get('energy_absolute_residual'),
        'error_energy_relative_decomposition_residual': split.get('energy_relative_residual'),
        'error_in_out_orthogonality_relative_residual': split.get('in_out_orthogonality_relative_residual'),
        'identity_assertion_tolerance': _IDENTITY_TOLERANCE,
        'evaluation_only': True,
    }


def _feasibility_row(base, estimate, published, config):
    real, imag = estimate.real, estimate.imag
    finite = bool(np.all(np.isfinite(estimate)))
    min_real, max_real = _number(np.min(real)), _number(np.max(real))
    min_imag, max_imag = _number(np.min(imag)), _number(np.max(imag))
    lower_real, lower_imag = float(config['physical_real_lower']), float(config['physical_imag_lower'])
    real_count = int(np.count_nonzero(real < lower_real - 1e-10))
    imag_count = int(np.count_nonzero(imag < lower_imag - 1e-10))
    violation = (max(0., lower_real - min_real, lower_imag - min_imag)
                 if min_real is not None and min_imag is not None else None)
    saved_violation = _number(published.get('physical_violation'))
    saved_status = published.get('status', 'NOT_RECORDED')
    boundary_rejection = real_count > 0 or imag_count > 0 or not finite
    status_match = ((saved_status == 'OK' and not boundary_rejection) or
                    (saved_status == 'REJECTED_PHYSICAL' and boundary_rejection))
    if saved_status not in ('OK', 'REJECTED_PHYSICAL'):
        status_match = None
    value_match = (abs(violation - saved_violation) <= 1e-9 * max(1., violation, saved_violation)
                   if violation is not None and saved_violation is not None else None)
    return {
        **base, 'minimum_real_chi': min_real, 'maximum_real_chi': max_real,
        'minimum_imag_chi': min_imag, 'maximum_imag_chi': max_imag,
        'real_below_frozen_lower_minus_1e_10_count': real_count,
        'imag_below_frozen_lower_minus_1e_10_count': imag_count,
        'physical_real_lower': lower_real, 'physical_imag_lower': lower_imag,
        'feasibility_tolerance': 1e-10,
        'nonfinite_cell_count': int(np.count_nonzero(~np.isfinite(estimate))),
        'physical_violation': violation, 'published_physical_violation': saved_violation,
        'physical_violation_matches_published_value': value_match,
        'boundary_rejection_matches_published_status': status_match,
        'status_comparison_scope': 'material bounds/nonfinite only; constitutive-pole checks are not rerun',
        'clipping_applied': False,
    }


def _correction_row(condition, estimates, published, background, volume, image_reference):
    scene, amplitude, noise = condition
    present = [method in estimates for method in _METHODS]
    row = {'scene': scene, 't': amplitude, 'noise': noise, 'image_reference': image_reference,
           'diagnostic_status': 'COMPUTED' if all(present) else 'MISSING_SAVED_CORRECTION_ESTIMATE',
           'dressed_status': published.get((*condition, _METHODS[0]), {}).get('status', 'NOT_RECORDED'),
           'vanilla_status': published.get((*condition, _METHODS[1]), {}).get('status', 'NOT_RECORDED'),
           'A23_status': published.get((*condition, _METHODS[2]), {}).get('status', 'NOT_RECORDED'),
           'quantity_domain': 'cached material-mass correction after the common decoder',
           'relative_deviation_definition': 'norm(c_comp-c_full)/norm(c_full)',
           'not_a_data_space_Q_capture_measure': True}
    if not all(present):
        return row
    dressed, vanilla, compressed = (estimates[method] for method in _METHODS)
    x1 = _mass_vector(dressed - background, volume)
    c_full = _mass_vector(dressed - vanilla, volume)
    c_comp = _mass_vector(dressed - compressed, volume)
    if not all(np.all(np.isfinite(value)) for value in (x1, c_full, c_comp)):
        row['diagnostic_status'] = 'NONFINITE_ESTIMATE_RETAINED'
        return row
    n1, nf, nc = (float(np.linalg.norm(value)) for value in (x1, c_full, c_comp))
    nd = float(np.linalg.norm(c_comp - c_full))
    row.update(
        dressed_delta_mass_norm=n1,
        full_quadratic_correction_mass_norm=nf,
        compressed_quadratic_correction_mass_norm=nc,
        correction_difference_mass_norm=nd,
        correction_relative_deviation=_ratio(nd, nf),
        correction_cosine=_ratio(float(c_full @ c_comp), nf * nc),
        compressed_to_full_correction_norm_ratio=_ratio(nc, nf),
        full_correction_relative_to_dressed_delta=_ratio(nf, n1),
        compressed_correction_relative_to_dressed_delta=_ratio(nc, n1),
    )
    return row


def _sketch_rows(root, result, config, inputs):
    audit_path = result / 'QUADRATIC_SKETCH_AUDIT.json'
    inputs.add(audit_path)
    audit = json.loads(audit_path.read_text(encoding='utf-8'))
    if not isinstance(audit, list):
        raise ValueError('UNRECOGNIZED_QUADRATIC_SKETCH_AUDIT')
    by_scene = {int(row['scene']): row for row in audit}
    rows = []
    for scene in config['scenes']:
        scene = int(scene)
        path = result / f'QUADRATIC_SKETCH_{scene}.npz'
        inputs.add(path)
        with np.load(path, allow_pickle=False) as saved:
            Uy, responses = saved['Uy'].copy(), saved['probe_response'].copy()
        if Uy.ndim != 2 or responses.ndim != 2 or Uy.shape[0] != responses.shape[0]:
            raise ValueError('INVALID_CACHED_QUADRATIC_SKETCH_SHAPE')
        if np.iscomplexobj(Uy) or np.iscomplexobj(responses) or not np.all(np.isfinite(Uy)) or not np.all(np.isfinite(responses)):
            raise ValueError('CACHED_QUADRATIC_SKETCH_MUST_BE_FINITE_REAL')
        mean_response = responses.mean(axis=1)
        retained = Uy @ (Uy.T @ mean_response)
        mean_norm = float(np.linalg.norm(mean_response))
        retained_norm = float(np.linalg.norm(retained))
        error_norm = float(np.linalg.norm(mean_response - retained))
        saved_audit = by_scene[scene]
        holdout = saved_audit['independent_probe_errors']
        if len(holdout) != int(saved_audit['holdout_probes']):
            raise ValueError('SAVED_HOLDOUT_ERROR_COUNT_MISMATCH')
        rows.append({
            'scene': scene, 'rank': Uy.shape[1], 'published_audit_rank': saved_audit['rank'],
            'rank_matches_published_audit': Uy.shape[1] == saved_audit['rank'],
            'frozen_requested_data_rank': config['quadratic_data_rank'],
            'training_probe_count': responses.shape[1],
            'published_mean_retained': saved_audit.get('mean_retained'),
            'training_mean_norm': mean_norm, 'retained_training_mean_norm': retained_norm,
            'training_mean_absolute_retention_error': error_norm,
            'training_mean_relative_retention_error': _ratio(error_norm, mean_norm),
            'basis_orthogonality_error': float(np.linalg.norm(Uy.T @ Uy - np.eye(Uy.shape[1]))),
            'heldout_probe_count': len(holdout),
            'heldout_relative_errors_json': json.dumps(holdout, separators=(',', ':'), allow_nan=False),
            'heldout_error_mean': float(np.mean(holdout)),
            'heldout_error_median': float(np.median(holdout)),
            'heldout_error_minimum': float(np.min(holdout)),
            'heldout_error_maximum': float(np.max(holdout)),
            'heldout_error_source': 'unchanged saved QUADRATIC_SKETCH_AUDIT.json values',
            'heldout_probes_recomputed': False,
            'sketch_reference': str(path.relative_to(root)),
            'audit_reference': str(audit_path.relative_to(root)),
        })
    return rows


def _build_tables(root):
    result = root / 'results/a23'
    config_path = root / 'FROZEN_CONFIG.json'
    metric_path = result / 'FULL_IMAGE_METRICS.csv'
    config = json.loads(config_path.read_text(encoding='utf-8'))
    inputs = {config_path, metric_path}
    background = complex(*config['background'])
    published = _published_rows(metric_path)
    geometry = {}
    chart_rows, feasibility_rows, correction_rows, concerns, seen = [], [], [], [], set()
    paths = sorted((result / 'images').glob('scene_*.npz'))
    if not paths:
        raise ValueError('NO_CACHED_IMAGES')
    for path in paths:
        condition = _condition(path)
        scene, amplitude, noise = condition
        if scene not in config['scenes']:
            raise ValueError('SAVED_IMAGE_SCENE_NOT_IN_FROZEN_CONFIG')
        if scene not in geometry:
            geometry_path = root / f'data/online/scene_{scene}.npz'
            inputs.add(geometry_path)
            with np.load(geometry_path, allow_pickle=False) as online:
                points, volume = online['points'].copy(), float(online['volume'])
            W = np.asarray(old_chart_basis(points, volume), float)
            W_error = float(np.linalg.norm(W.T @ W - np.eye(W.shape[1])))
            if W.shape != (2 * len(points), 32) or W_error > _IDENTITY_TOLERANCE:
                raise AssertionError('EXACT_FIXED_OLD32_CHART_ORTHOGONALITY_FAILED')
            geometry[scene] = (points, volume, W, W_error)
        points, volume, W, W_error = geometry[scene]
        inputs.add(path)
        with np.load(path, allow_pickle=False) as image:
            truth = image['truth_OFFLINE'].copy()
            estimates = {key: image[key].copy() for key in image.files if key not in _RESERVED}
        if truth.shape != (len(points),) or not np.all(np.isfinite(truth)):
            raise ValueError('INVALID_SAVED_OFFLINE_TRUTH')
        truth_split = _split_energy(_mass_vector(truth - background, volume), W)
        image_reference = str(path.relative_to(root))
        for method, estimate in estimates.items():
            if estimate.shape != truth.shape:
                raise ValueError('SAVED_ESTIMATE_GEOMETRY_MISMATCH:' + method)
            key = (*condition, method)
            seen.add(key)
            published_row = published.get(key, {})
            if not published_row:
                concerns.append(f'{scene}/{amplitude}/{noise}/{method}: no published metric row')
            base = {'scene': scene, 't': amplitude, 'noise': noise, 'method': method,
                    'published_status': published_row.get('status', 'NOT_RECORDED'),
                    'image_reference': image_reference}
            chart_rows.append(_chart_row(base, estimate, truth, background, volume, W, truth_split, W_error))
            feasible = _feasibility_row(base, estimate, published_row, config)
            feasibility_rows.append(feasible)
            if feasible['physical_violation_matches_published_value'] is False:
                concerns.append(f'{scene}/{amplitude}/{noise}/{method}: physical violation differs from published value')
            if feasible['boundary_rejection_matches_published_status'] is False:
                concerns.append(f'{scene}/{amplitude}/{noise}/{method}: material bounds alone do not match published status; pole checks were not rerun')
        correction_rows.append(_correction_row(condition, estimates, published, background, volume, image_reference))
    missing = sorted(set(published) - seen)
    if missing:
        concerns.append(f'{len(missing)} published metric rows have no saved reconstruction')
    sketch_rows = _sketch_rows(root, result, config, inputs)
    return {
        'chart_rows': chart_rows, 'feasibility_rows': feasibility_rows,
        'correction_rows': correction_rows, 'sketch_mean_rows': sketch_rows,
        'metadata_concerns': concerns, 'published_rows_without_saved_output': [list(key) for key in missing],
        'saved_condition_count': len(paths), 'saved_scene_count': len(geometry),
        'input_paths': sorted(str(path.relative_to(root)) for path in inputs),
    }


def _write_csv(path, rows):
    keys = list(dict.fromkeys(key for row in rows for key in row))
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def summarize_cached(root):
    """Generate only the four new derived CSVs and a standalone CPU receipt.

    A second invocation with existing output names is rejected, so original
    receipts or derived files are never overwritten by this single-pass job.
    """
    root = Path(root).resolve()
    result = root / 'results/a23'
    paths = {name: result / name for name in _OUTPUTS}
    receipt_path = result / 'theory_verification/CACHED_DIAGNOSTICS_RECEIPT.json'
    if any(path.exists() for path in (*paths.values(), receipt_path)):
        raise FileExistsError('CACHED_DIAGNOSTIC_OUTPUT_ALREADY_EXISTS')
    started_wall, started_cpu = time.perf_counter(), time.process_time()
    receipt = {'started_utc': datetime.now(timezone.utc).isoformat(),
               'status': 'FAILED', 'kind': 'saved-array offline diagnostics',
               'device': 'CPU', 'physical_operator_actions': 0, 'new_label_calls': 0,
               'parameter_changes': False, 'original_raw_data_writes': False,
               'gate_decisions': False, 'new_hash_checks': 0}
    try:
        tables = _build_tables(root)
        for filename, key in zip(_OUTPUTS, ('chart_rows', 'feasibility_rows',
                                          'correction_rows', 'sketch_mean_rows')):
            _write_csv(paths[filename], tables[key])
        receipt.update(status='COMPLETED',
            row_counts={filename: len(tables[key]) for filename, key in zip(
                _OUTPUTS, ('chart_rows', 'feasibility_rows', 'correction_rows', 'sketch_mean_rows'))},
            saved_condition_count=tables['saved_condition_count'],
            saved_scene_count=tables['saved_scene_count'], input_paths=tables['input_paths'],
            metadata_concerns=tables['metadata_concerns'])
        tables['paths'] = {name: str(path) for name, path in paths.items()}
        tables['paths']['receipt'] = str(receipt_path)
        return tables
    except BaseException as exc:
        receipt['error'] = type(exc).__name__ + ': ' + str(exc)
        raise
    finally:
        receipt['wall_seconds'] = time.perf_counter() - started_wall
        receipt['process_cpu_seconds'] = time.process_time() - started_cpu
        receipt['timer_scope'] = 'cached reads/computation/four CSV exports; receipt export excluded'
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n', encoding='utf-8')
