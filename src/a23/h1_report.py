"""Mechanical H1 receipt tables; no physics execution or gate decisions.

Cold encoder cost attributes the declared reference, receiver modes when
needed, and the arm's encoder/export increment.  The direct arm additionally
attributes its separately measured receiver-adjoint construction.  Warm
increments reuse the cold reference and receiver geometry.  No RHS categories
are summed into a synthetic total, and no legacy aliases are double counted.
"""
from __future__ import annotations

import ast
import csv
import json
import math
from pathlib import Path
from statistics import mean, median


ACTION_KEYS = (
    'L_rhs', 'L_adjoint_rhs', 'F_rhs', 'F_adjoint_rhs', 'G_rhs', 'G_adjoint_rhs',
    'S_rhs', 'S_adjoint_rhs', 'solve_forward_rhs', 'solve_adjoint_rhs',
    'B_rhs', 'B_adjoint_rhs', 'L_adjoint_residual_audit_rhs', 'forcing_rhs',
    'reduced_core_rhs', 'qr_columns', 'svd_calls', 'retained_factorizations',
    'projected_factorizations', 'full_LU_factorizations',
    'cache_read_bytes', 'cache_write_bytes', 'transfer_bytes', 'failed_attempts',
)


def _structured(value, expected, *, label):
    if isinstance(value, expected):
        return value
    if value is None or value == '':
        return expected()
    if not isinstance(value, str):
        raise ValueError('INVALID_H1_STRUCTURED_FIELD:' + label)
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        # The original CSV writer serialized nested objects with Python repr.
        # literal_eval accepts its None/True syntax without executing code.
        try:
            parsed = ast.literal_eval(value)
        except (ValueError, SyntaxError) as exc:
            raise ValueError('INVALID_H1_STRUCTURED_FIELD:' + label) from exc
    if not isinstance(parsed, expected):
        raise ValueError('INVALID_H1_STRUCTURED_TYPE:' + label)
    return parsed


def _number(value):
    if value is None or value == '' or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _integer(value):
    number = _number(value)
    return int(number) if number is not None and number.is_integer() else None


def _sum_required(*values):
    return sum(values) if all(value is not None for value in values) else None


def _json(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def _location(root):
    root = Path(root).resolve()
    result = root if (root / 'H1_ENCODER_METRICS.csv').is_file() else root / 'results/a23'
    return root, result


def _display(path, root):
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _read_rows(root, result):
    path = result / 'H1_ENCODER_METRICS.csv'
    csv.field_size_limit(max(csv.field_size_limit(), 16 * 1024 ** 2))
    with path.open(newline='', encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError('H1_INPUT_HAS_NO_ROWS')
    json_refs = {}
    for saved_path in sorted((result / 'h1').glob('scene_*/H1_METRICS.json')):
        saved = json.loads(saved_path.read_text(encoding='utf-8'))
        if isinstance(saved, list):
            items, prefix = saved, ''
        elif isinstance(saved, dict) and isinstance(saved.get('rows'), list):
            items, prefix = saved['rows'], '/rows'
        else:
            raise ValueError('UNRECOGNIZED_H1_JSON_TOPOLOGY:' + str(saved_path))
        for index, row in enumerate(items):
            scene = _integer(row.get('scene', row.get('parent_id')))
            json_refs[(scene, row['method'])] = (
                _display(saved_path, root) + '#' + prefix + '/' + str(index) + '/metadata')
    seen = set()
    for record, row in enumerate(rows, 2):
        scene = _integer(row.get('scene', row.get('parent_id')))
        if scene is None:
            raise ValueError('H1_INVALID_SCENE_RECORD:' + str(record))
        key = (scene, row['method'])
        if key in seen:
            raise ValueError('H1_DUPLICATE_SCENE_METHOD:' + repr(key))
        seen.add(key)
        row['_scene'] = scene
        row['_metadata'] = _structured(row.get('metadata'), dict, label='metadata')
        row['_repeats'] = _structured(row.get('repeats'), list, label='repeats')
        row['_receiver'] = _structured(row.get('shared_receiver_geometry_attribution'), dict,
                                      label='shared_receiver_geometry_attribution')
        row['_metadata_reference'] = json_refs.get(key, _display(path, root) +
                                                     '#record=' + str(record) + '&field=metadata')
        row['_source_csv_record'] = record
    return rows


def _timings(row, concerns):
    method, scene = row['method'], row['_scene']
    metadata, repeats = row['_metadata'], row['_repeats']
    cold = repeats[0] if repeats else {}
    if not repeats or cold.get('temperature') != 'cold' or cold.get('repeat') != 0:
        concerns.append(f'{scene}/{method}: repeats[0] is missing or is not the frozen cold attempt')
    independent = metadata.get('independent_preparation') or {}
    if not isinstance(independent, dict):
        raise ValueError('INVALID_DIRECT_PREPARATION_METADATA')
    common = _number(row.get('common_reference_geometry_seconds'))
    if common is None:
        common = _number(independent.get('common_reference_geometry_seconds'))
    receiver = _number(row['_receiver'].get('wall_seconds')) if row['_receiver'] else 0.
    decoder = _number(row.get('decoder_prepare_seconds'))
    if decoder is None:
        decoder = _number(independent.get('decoder_prepare_seconds'))
    increment = _number(cold.get('encoder_preparation_wall_seconds'))
    if increment is None:
        increment = _number(row.get('cold_encoder_preparation_wall_seconds'))
    direct = _number(independent.get('cold_seconds')) if method == 'direct_adjoint' else 0.
    if method == 'direct_adjoint' and direct is None:
        concerns.append(f'{scene}/{method}: independent direct construction cold cost is missing')
    if common is None:
        concerns.append(f'{scene}/{method}: common reference/geometry cold cost is missing')
    cold_encoder = _sum_required(increment, direct)
    full = _sum_required(common, receiver, cold_encoder)

    warm_attempts = [repeat for repeat in repeats if repeat.get('temperature') == 'warm']
    warm_local = [_number(repeat.get('encoder_preparation_wall_seconds')) for repeat in warm_attempts]
    saved_warm = _structured(row.get('warm_encoder_preparation_wall_seconds'), list,
                             label='warm_encoder_preparation_wall_seconds')
    if len(saved_warm) == len(warm_local):
        warm_local = [local if local is not None else _number(saved_warm[index])
                      for index, local in enumerate(warm_local)]
    direct_warm = independent.get('warm_seconds', []) if method == 'direct_adjoint' else [0.] * len(warm_local)
    if not isinstance(direct_warm, list):
        raise ValueError('INVALID_DIRECT_WARM_COST_VECTOR')
    if method == 'direct_adjoint' and len(direct_warm) != len(warm_local):
        concerns.append(f'{scene}/{method}: direct warm costs do not match warm attempt slots')
    warm_independent = [_number(direct_warm[index]) if index < len(direct_warm) else None
                        for index in range(len(warm_local))]
    warm = [_sum_required(local, independent_cost)
            for local, independent_cost in zip(warm_local, warm_independent)]
    valid_warm = [value for value in warm if value is not None]
    evaluation = _number(cold.get('evaluation_wall_seconds'))
    if evaluation is None:
        evaluation = _number(cold.get('stages', {}).get('evaluation', {}).get('wall_seconds'))
    return {
        'common_reference_geometry_seconds': common,
        'receiver_geometry_cold_attribution_seconds': receiver,
        'cold_encoder_local_increment_seconds': increment,
        'direct_independent_cold_seconds': direct,
        'cold_encoder_with_independent_construction_seconds': cold_encoder,
        'full_cold_encoder_seconds': full,
        'common_evaluation_decoder_prepare_seconds': decoder,
        'full_cold_encoder_plus_evaluation_decoder_seconds': _sum_required(full, decoder),
        'cold_evaluation_seconds': evaluation,
        'cold_local_wall_including_evaluation_seconds': _number(cold.get('wall_seconds')),
        'warm_local_encoder_increments_json': _json(warm_local),
        'warm_direct_independent_seconds_json': _json(warm_independent),
        'warm_encoder_increments_seconds_json': _json(warm),
        'warm_encoder_increment_mean_seconds': mean(valid_warm) if valid_warm else None,
        'warm_encoder_increment_median_seconds': median(valid_warm) if valid_warm else None,
        'warm_valid_time_slots': len(valid_warm),
        'warm_reference_and_receiver_geometry': 'cold reference and receiver geometry reused; costs excluded',
        'cold_time_scope': 'reference + receiver modes when used + arm encoder/export + direct construction when used; probe evaluation excluded',
        'cold_repeat_status': cold.get('status', 'NOT_RECORDED'),
        'warm_repeat_statuses_json': _json([repeat.get('status', 'NOT_RECORDED') for repeat in warm_attempts]),
        'recorded_attempt_count': len(repeats),
        'failed_attempt_count': sum(repeat.get('status') != 'OK' for repeat in repeats),
    }


def _actions(row, concerns):
    # Only repeats[0], plus direct's independent cold receipt, exactly once.
    cold = row['_repeats'][0] if row['_repeats'] else {}
    local = cold.get('counts') or {}
    direct = ((row['_metadata'].get('independent_preparation') or {}).get('cold_counts') or {}
              if row['method'] == 'direct_adjoint' else {})
    if not isinstance(local, dict) or not isinstance(direct, dict):
        raise ValueError('INVALID_H1_COUNT_RECEIPT')
    result = {}
    for key in ACTION_KEYS:
        values = [_integer(receipt.get(key, 0)) for receipt in (local, direct)]
        if any(value is None or value < 0 for value in values):
            raise ValueError('INVALID_H1_NONNEGATIVE_ACTION_COUNT:' + key)
        result[key] = sum(values)
    aliases = ('L_actions', 'L_adjoint_actions', 'F_actions', 'F_adjoint_actions',
               'S_actions', 'S_adjoint_actions', 'full_tangent_RHS', 'full_adjoint_RHS',
               'full_tangent_receiver_rhs', 'full_adjoint_receiver_rhs', 'Maxwell_matvec_rhs')
    nonzero_aliases = {key: direct[key] for key in aliases if _number(direct.get(key))}
    if nonzero_aliases:
        concerns.append(f"{row['_scene']}/{row['method']}: nonzero legacy aliases remain in the direct receipt; see raw metadata, aliases not summed")
    result['action_scope'] = 'repeats[0].counts + direct independent cold_counts once; common preparation actions excluded'
    return result


def _source_P_evidence(rows, identity_rtol):
    evidence = {}
    for row in rows:
        if row['method'] != 'source_anchored_opm':
            continue
        metadata = row['_metadata']
        p = metadata.get('seed_records', {}).get('P', {})
        retained = metadata.get('retained', {})
        relative = _number(p.get('P_relative_to_forcing'))
        verified = bool(p.get('structural_zero') is True and
                        _integer(p.get('raw_effective_rank')) == 0 and
                        _integer(p.get('rank')) == 0 and
                        (_integer(p.get('input_columns')) or 0) > 0 and
                        retained.get('all_source_capture') is True and
                        relative is not None and relative <= identity_rtol)
        evidence[row['_scene']] = {
            'verified': verified, 'relative': relative,
            'reference': row['_metadata_reference'] + '/seed_records/P'}
    return evidence


def _seed_rows(row, evidence, concerns):
    metadata = row['_metadata']
    records = metadata.get('seed_records', {})
    redundancy = metadata.get('seed_redundancy', {})
    hierarchy = metadata.get('hierarchy', {})
    joint = hierarchy.get('joint_deflation', [])
    compact_joint = [{key: item.get(key) for key in ('input_columns', 'rank', 'deflated')}
                     for item in joint]
    joint_deflated = sum(_integer(item.get('deflated')) or 0 for item in joint) if joint else None
    pairwise = redundancy.get('pairwise', {})
    rows = []
    for channel in 'OPM':
        seed = records.get(channel, {})
        applicable = channel in records
        omitted = applicable and _integer(seed.get('requested_rank')) == 0
        source_P = row['method'].startswith('source_anchored_') and channel == 'P'
        e = evidence.get(row['_scene']) if source_P else None
        own_verified = bool(source_P and not omitted and e and e['verified'])
        if source_P and not omitted and applicable and not own_verified:
            concerns.append(f"{row['_scene']}/{row['method']}: saved source-P cancellation is not verified")
        angles = {pair: details.get('raw_principal_angles_radians', [])
                  for pair, details in pairwise.items() if channel in pair}
        overlap = {pair: details.get('raw_overlap_frobenius_squared')
                   for pair, details in pairwise.items() if channel in pair}
        residuals = {pair: details.get('right_raw_incremental_relative_residual')
                     for pair, details in pairwise.items() if channel in pair}
        status = ('NOT_APPLICABLE_NO_CURRENT_SEEDS' if not applicable else
                  'OMITTED' if omitted else 'STRUCTURAL_ZERO_VERIFIED' if own_verified else 'CONSTRUCTED')
        rows.append({
            'scene': row['_scene'], 'method': row['method'], 'arm_status': row.get('status'),
            'channel': channel, 'channel_status': status,
            'input_columns': _integer(seed.get('input_columns')),
            'requested_rank': _integer(seed.get('requested_rank')),
            'raw_rank_own_scale': _integer(seed.get('raw_rank_own_scale')),
            'raw_effective_rank': _integer(seed.get('raw_effective_rank')),
            'capped_rank': _integer(seed.get('rank')),
            'raw_to_capped_deflated_columns': _integer(seed.get('deflated')),
            'rank_cap_deflated': _integer(seed.get('rank_cap_deflated')),
            'raw_frobenius_norm': _number(seed.get('raw_frobenius_norm')),
            'raw_column_norms_json': _json(seed.get('original_column_norms', [])),
            'raw_joint_rank': _integer(redundancy.get('raw_joint_rank')),
            'raw_rank_sum': _integer(redundancy.get('raw_rank_sum')),
            'raw_joint_deflated_columns': _integer(redundancy.get('raw_joint_deflation', {}).get('deflated')),
            'capped_rank_sum': _integer(redundancy.get('capped_rank_sum')),
            'retained_rank': _integer(metadata.get('retained', {}).get('rank')),
            'hierarchy_complement_joint_rank': _integer(hierarchy.get('added_rank')),
            'hierarchy_full_current_rank': _integer(hierarchy.get('rank')),
            'hierarchy_joint_deflated_columns': joint_deflated,
            'joint_degree_deflation_json': _json(compact_joint),
            'P_relative_to_forcing': _number(seed.get('P_relative_to_forcing')),
            'structural_zero_recorded': seed.get('structural_zero') if applicable else None,
            'structural_zero_verified_from_own_saved_receipt': own_verified if source_P and applicable and not omitted else None,
            'source_anchor_P_evidence_verified': e['verified'] if e else None,
            'source_anchor_P_evidence_reference': e['reference'] if e else None,
            'source_anchor_P_evidence_relative_to_forcing': e['relative'] if e else None,
            'source_anchor_P_evidence_scope': ('own saved P construction' if own_verified else
                                              'same-scene source_anchored_opm; this arm omitted P' if source_P and omitted else None),
            'principal_angles_radians_json': _json(angles),
            'pairwise_overlap_frobenius_squared_json': _json(overlap),
            'pairwise_incremental_residual_json': _json(residuals),
            'metadata_reference': row['_metadata_reference'],
            'principal_angles_reference': row['_metadata_reference'] + '/seed_redundancy/pairwise' if applicable else None,
            'joint_deflation_reference': row['_metadata_reference'] + '/hierarchy/joint_deflation' if applicable else None,
            'channel_provenance': seed.get('provenance'),
        })
    return rows


def _tables(root, result):
    rows = _read_rows(root, result)
    config_path = root / 'FROZEN_CONFIG.json'
    config = json.loads(config_path.read_text(encoding='utf-8')) if config_path.is_file() else {}
    identity_rtol = float(config.get('identity_rtol', 1e-10))
    evidence = _source_P_evidence(rows, identity_rtol)
    summary, seeds, concerns = [], [], []
    for row in rows:
        metadata, method = row['_metadata'], row['method']
        rank = _integer(metadata.get('rank'))
        if rank is None:
            concerns.append(f"{row['_scene']}/{method}: actual rank is not recorded; no rank inferred from matrix dimensions")
        compact = {
            'scene': row['_scene'], 'method': method, 'status': row.get('status', 'NOT_RECORDED'),
            'actual_rank': rank,
            'rank_domain': ('real_data_range' if method == 'randomized_transfer' else
                            'exact_real_material_data_transfer' if method == 'direct_adjoint' else
                            'complex_current_basis'),
            'rank_status': 'RECORDED' if rank is not None else 'NOT_RECORDED',
            'retained_rank': _integer(metadata.get('retained', {}).get('rank')),
            'source_rank': _integer(metadata.get('retained', {}).get('source_rank')),
            'transfer_error': _number(row.get('transfer_error')),
            'decoder_weighted_error': _number(row.get('decoder_weighted_error')),
            'dual_response_error': _number(row.get('dual_response_error')),
            'old_cached_transfer_relative_error': _number(row.get('old_cached_transfer_relative_error')),
            **_timings(row, concerns), **_actions(row, concerns),
            'metadata_reference': row['_metadata_reference'],
            'input_csv_record_number': row['_source_csv_record'],
        }
        summary.append(compact)
        seeds.extend(_seed_rows(row, evidence, concerns))
    return summary, seeds, list(dict.fromkeys(concerns))


def _write_csv(path, rows):
    keys = list(dict.fromkeys(key for row in rows for key in row))
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def summarize_h1(root):
    """Write two mechanical CSVs and return compact tables plus concerns.

    ``root`` is the research workspace (or the result directory).  The source
    CSV, receipts, configuration and all experimental outputs stay unchanged.
    Unknown costs/ranks remain empty CSV cells, rather than becoming zero.
    """
    root, result = _location(root)
    summary, seeds, concerns = _tables(root, result)
    summary_path, seed_path = result / 'H1_SUMMARY.csv', result / 'SEED_REDUNDANCY.csv'
    _write_csv(summary_path, summary)
    _write_csv(seed_path, seeds)
    return {'summary_rows': summary, 'seed_rows': seeds, 'metadata_concerns': concerns,
            'paths': {'H1_SUMMARY.csv': str(summary_path), 'SEED_REDUNDANCY.csv': str(seed_path)}}
