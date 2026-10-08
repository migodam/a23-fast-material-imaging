"""Scientific figures from saved A23 evidence; no physics calls or gate decisions.

Only saved metrics, saved reconstruction arrays, and online mesh coordinates
are read. Rejected estimates remain visible. Missing results are recorded in
the manifest, never replaced by fabricated measurements.
"""
from __future__ import annotations

import ast
import csv
import json
from pathlib import Path
import re
import shutil
from typing import Any

import numpy as np


METHODS = (
    'homogeneous_born', 'born_BP', 'dressed_linear_chi',
    'linear_a_exact_conversion', 'vanilla_IBS2', 'A23_compressed_feedback',
    'generic_randomized_linear', 'current_BP_ratio',
)
IMAGE_METHODS = ('dressed_linear_chi', 'linear_a_exact_conversion',
                 'vanilla_IBS2', 'A23_compressed_feedback')
LABELS = {
    'homogeneous_born': 'Homogeneous Born', 'born_BP': 'Born BP',
    'dressed_linear_chi': 'Dressed linear χ', 'linear_a_exact_conversion': 'Linear a → χ',
    'vanilla_IBS2': 'Vanilla IBS2', 'A23_compressed_feedback': 'A23 feedback',
    'generic_randomized_linear': 'Randomized linear', 'current_BP_ratio': 'Current BP ratio',
    'original_opm': 'Original OPM', 'cached_opm': 'Cached OPM',
    'source_anchored_opm': 'Source anchored OPM', 'source_anchored_om': 'Source anchored OM',
    'mp': 'MP', 'm_only': 'M only', 'randomized_transfer': 'Randomized transfer',
    'direct_adjoint': 'Direct adjoint', 'truth_OFFLINE': 'Truth (offline)',
}
SCENES = (2001, 2003, 2014, 2009)


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float('nan')


def _structured(value: Any, default=None):
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, str) and value:
        for parse in (json.loads, ast.literal_eval):
            try:
                return parse(value)
            except (ValueError, SyntaxError, TypeError):
                pass
    return default


def _finite(value: Any) -> bool:
    return bool(np.isfinite(_number(value)))


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline='', encoding='utf-8-sig') as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list))
                             else value for key, value in row.items()})


def _clean_json(value):
    if isinstance(value, dict):
        return {str(key): _clean_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean_json(item) for item in value]
    if isinstance(value, np.generic):
        return _clean_json(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, Path):
        return str(value)
    return value


def _bad(row: dict) -> bool:
    status = str(row.get('status', 'UNKNOWN')).upper()
    return status not in ('OK', 'PASS', 'COMPLETE', 'RUN', 'VALID')


def _method_order(rows: list[dict]) -> list[str]:
    seen = set(str(row.get('method', 'UNKNOWN')) for row in rows)
    return [method for method in METHODS if method in seen] + sorted(seen-set(METHODS))


class _Figures:
    def __init__(self, root: Path):
        self.root = root
        self.result = root/'results/a23'
        self.output = root/'figures/a23'
        self.output.mkdir(parents=True, exist_ok=True)
        self.manifest = {
            'scope': 'descriptive figures of saved A23 results; no gate evaluation',
            'scientific_interpretation': 'parent Codex',
            'sources': [], 'figures': [], 'raw_tables': [], 'missing': [], 'errors': [],
            'retained_rejected_and_failed_rows': True,
            'sha256_checks': 'NOT_RUN_user_instruction',
        }

    def source(self, path: Path):
        self.manifest['sources'].append({'path': str(path.relative_to(self.root)),
                                         'bytes': path.stat().st_size})

    def preserve_csv(self, name: str) -> list[dict]:
        path = self.result/name
        if not path.exists():
            self.manifest['missing'].append({'source': f'results/a23/{name}', 'status': 'NOT_AVAILABLE'})
            return []
        self.source(path)
        destination = self.output/'raw'/name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        rows = _read_csv(path)
        self.manifest['raw_tables'].append({'path': str(destination.relative_to(self.root)), 'rows': len(rows)})
        return rows

    def raw(self, name: str, rows: list[dict]):
        if not rows:
            return
        path = self.output/'raw'/name
        _write_csv(path, rows)
        self.manifest['raw_tables'].append({'path': str(path.relative_to(self.root)), 'rows': len(rows)})

    def save(self, figure, name: str, *, caption: str, metadata=None):
        paths = []
        for extension in ('png', 'svg'):
            path = self.output/f'{name}.{extension}'
            figure.savefig(path, dpi=180, bbox_inches='tight', facecolor='white')
            paths.append(str(path.relative_to(self.root)))
        self.plt.close(figure)
        self.manifest['figures'].append({'name': name, 'paths': paths,
                                         'caption': caption, **(metadata or {})})


def _h1_rows(builder: _Figures) -> list[dict]:
    csvrows = builder.preserve_csv('H1_ENCODER_METRICS.csv')
    merged = {}
    for row in csvrows:
        scene = int(_number(row.get('scene', row.get('parent_id'))))
        for key in ('repeats', 'metadata', 'shared_actual_cost', 'warm_wall_seconds'):
            if key in row:
                row[key] = _structured(row[key], {} if key != 'repeats' else [])
        merged[(scene, row['method'])] = row
    for path in sorted((builder.result/'h1').glob('*/H1_METRICS.json')):
        builder.source(path)
        saved = json.loads(path.read_text(encoding='utf-8'))
        rows = saved if isinstance(saved, list) else saved.get('rows', saved.get('methods', []))
        for row in rows:
            scene = int(_number(row.get('scene', row.get('parent_id'))))
            key = (scene, row['method'])
            merged[key] = {**merged.get(key, {}), **row, 'scene': scene}
    return list(merged.values())


def _h1(builder: _Figures):
    rows = _h1_rows(builder)
    if not rows:
        return
    raw = []
    counts_keys = ('L_rhs', 'L_adjoint_rhs', 'F_rhs', 'F_adjoint_rhs', 'G_rhs',
                   'S_rhs', 'S_adjoint_rhs', 'solve_forward_rhs', 'solve_adjoint_rhs',
                   'B_rhs', 'B_adjoint_rhs')
    for row in rows:
        metadata = _structured(row.get('metadata'), {})
        repeats = _structured(row.get('repeats'), [])
        cold = next((repeat for repeat in repeats if repeat.get('temperature') == 'cold'), {})
        counts = cold.get('counts', {})
        independent = metadata.get('independent_preparation') or {}
        method = row['method']
        time = _number(row.get('cold_wall_seconds'))
        if not np.isfinite(time):
            time = _number(cold.get('wall_seconds'))
        if method == 'direct_adjoint' and _finite(independent.get('cold_seconds')):
            time += float(independent['cold_seconds'])
            independent_counts = independent.get('cold_counts', {})
            counts = {key: int(counts.get(key, 0))+int(independent_counts.get(key, 0))
                      for key in set(counts)|set(independent_counts)}
        rank = _number(metadata.get('rank', row.get('rank')))
        raw.append({'scene': int(_number(row.get('scene', row.get('parent_id')))), 'method': method,
                    'status': row.get('status', 'UNKNOWN'), 'actual_rank': rank,
                    'rank_domain': 'data' if method == 'randomized_transfer' else
                                   'exact transfer' if method == 'direct_adjoint' else 'current',
                    'cold_candidate_wall_seconds': time,
                    'common_reference_geometry_seconds': _number(row.get('common_reference_geometry_seconds')),
                    'common_decoder_prepare_seconds': _number(row.get('decoder_prepare_seconds')),
                    'transfer_error': _number(row.get('transfer_error')),
                    'decoder_weighted_error': _number(row.get('decoder_weighted_error')),
                    'failed_repeats': sum(repeat.get('status') != 'OK' for repeat in repeats),
                    'all_attempt_wall_seconds': sum(_number(repeat.get('wall_seconds')) for repeat in repeats),
                    'counts': counts,
                    'counted_rhs_total': sum(int(counts.get(key, 0)) for key in counts_keys),
                    'solve_forward_rhs': counts.get('solve_forward_rhs', 0),
                    'solve_adjoint_rhs': counts.get('solve_adjoint_rhs', 0),
                    'other_operator_rhs': sum(int(counts.get(key, 0)) for key in counts_keys) -
                                          int(counts.get('solve_forward_rhs', 0))-int(counts.get('solve_adjoint_rhs', 0)),
                    'warm_wall_seconds': row.get('warm_wall_seconds', []),
                    'time_scope': 'candidate construction + evaluation + export; common reference/decoder listed separately'})
    builder.raw('H1_PLOTTED.csv', raw)
    for scene in sorted(set(row['scene'] for row in raw)):
        selected = [row for row in raw if row['scene'] == scene]
        figure, axes = builder.plt.subplots(1, 3, figsize=(14, max(4.5, .48*len(selected))), sharey=True)
        y = np.arange(len(selected))
        names = [LABELS.get(row['method'], row['method']) + (' [FAILED]' if _bad(row) else '')
                 for row in selected]
        for axis in axes:
            axis.grid(axis='x', alpha=.2)
            axis.set_yticks(y, names)
        ranks = [row['actual_rank'] if _finite(row['actual_rank']) else 0. for row in selected]
        axes[0].barh(y, ranks, color='#7c91ae')
        for index, row in enumerate(selected):
            axes[0].text(ranks[index], index, ' '+(f"{int(ranks[index])} {row['rank_domain']}" if _finite(row['actual_rank'])
                                              else 'n/a — exact transfer'), va='center', fontsize=8)
        axes[0].set_xlabel('Actual rank (domains shown explicitly)')
        forward = np.array([row['solve_forward_rhs'] for row in selected], float)
        adjoint = np.array([row['solve_adjoint_rhs'] for row in selected], float)
        other = np.array([row['counted_rhs_total'] for row in selected], float)-forward-adjoint
        axes[1].barh(y, forward, label='Forward solve RHS', color='#4287ab')
        axes[1].barh(y, adjoint, left=forward, label='Adjoint solve RHS', color='#c38939')
        axes[1].barh(y, other, left=forward+adjoint, label='Other operator RHS', color='#a0b0a2')
        axes[1].set_xlabel('Counted RHS (operator calls and solves kept distinct)')
        axes[1].legend(fontsize=7, loc='lower right')
        times = [row['cold_candidate_wall_seconds'] if _finite(row['cold_candidate_wall_seconds']) else 0.
                 for row in selected]
        axes[2].barh(y, times, color=['#b64c45' if _bad(row) else '#4a877b' for row in selected])
        for index, row in enumerate(selected):
            if not _finite(row['cold_candidate_wall_seconds']):
                axes[2].text(0., index, 'MISSING/FAILED', color='#a03030', va='center', fontsize=8)
        axes[2].set_xlabel('Cold candidate wall seconds')
        axes[0].invert_yaxis()
        figure.suptitle(f'Scene {scene} · H1 rank, actions, and measured preparation')
        figure.text(.02, -.025, 'Candidate wall includes evaluation/export. Direct includes caller-measured preparation. '
                    'Common reference/decoder costs remain in raw tables. Failed attempts are retained.', fontsize=8)
        figure.tight_layout()
        builder.save(figure, f'h1_rank_actions_time_{scene}', caption='H1 actual rank domains, distinct RHS costs, cold wall; no gate decision')


def _finite_amplitudes(builder: _Figures, rows: list[dict]):
    if not rows:
        return
    scenes = [scene for scene in SCENES if any(int(_number(row['scene'])) == scene for row in rows)]
    noises = list(dict.fromkeys(row['noise'] for row in rows))
    methods = _method_order(rows)
    colors = {method: builder.plt.get_cmap('tab10')(index % 10) for index, method in enumerate(methods)}
    for improvement in (False, True):
        figure, axes = builder.plt.subplots(len(noises), len(scenes), squeeze=False,
                                            figsize=(3.7*len(scenes), 3.3*len(noises)))
        for i, noise in enumerate(noises):
            for j, scene in enumerate(scenes):
                axis = axes[i, j]
                subset = [row for row in rows if int(_number(row['scene'])) == scene and row['noise'] == noise]
                baseline = {_number(row['t']): _number(row.get('full_chi_NRMSE')) for row in subset
                            if row['method'] == 'dressed_linear_chi'}
                failed_missing = []
                for method in methods:
                    selected = sorted([row for row in subset if row['method'] == method], key=lambda row: _number(row['t']))
                    x, y = [], []
                    for row in selected:
                        amplitude, error = _number(row['t']), _number(row.get('full_chi_NRMSE'))
                        value = error
                        if improvement:
                            base = baseline.get(amplitude, float('nan'))
                            value = 100*(base-error)/base if np.isfinite(base) and base != 0 else float('nan')
                        x.append(amplitude); y.append(value)
                        if _bad(row) and not np.isfinite(value):
                            failed_missing.append(f"{LABELS.get(method, method)} t={amplitude:g}: {row.get('status')}")
                        if _bad(row) and np.isfinite(value):
                            axis.scatter(amplitude, value, marker='x', color='#b62727', s=58, linewidth=1.5, zorder=5)
                    axis.plot(x, y, marker='o', markersize=3.5, linewidth=1.15, color=colors[method],
                              label=LABELS.get(method, method))
                if improvement:
                    axis.axhline(0., color='#555555', linewidth=.8)
                axis.set_title(f"{scene} · {noise.replace('20dB_nominal_difference', '20 dB fixed σ')}", fontsize=10)
                axis.set_xlabel('Full χ interpolation amplitude t')
                axis.set_ylabel('NRMSE improvement vs dressed linear (%)' if improvement else 'Full χ NRMSE (mass norm)')
                axis.grid(alpha=.2)
                if failed_missing:
                    axis.text(.01, .02, '\n'.join(failed_missing), transform=axis.transAxes,
                              fontsize=6, color='#b62727', va='bottom')
        handles, labels = axes[0, 0].get_legend_handles_labels()
        figure.legend(handles, labels, loc='lower center', ncol=4, fontsize=8, bbox_to_anchor=(.5, -.04))
        figure.suptitle('Saved full-material errors; rejected estimates retained' if not improvement else
                       'Offline error comparison; negative improvements retained')
        figure.tight_layout(rect=(0, .07, 1, .96))
        builder.save(figure, 'finite_amplitude_improvement' if improvement else 'finite_amplitude_full_error',
                     caption='All saved methods/conditions; red crosses denote rejected/failed candidates; no gate evaluation')


def _curvature(builder: _Figures, rows: list[dict]):
    if not rows:
        return
    scenes = [scene for scene in SCENES if any(int(_number(row['scene'])) == scene for row in rows)]
    components = [('full_Q_norm', 'Full Q'), ('feedback_Q_norm', 'Feedback Q'),
                  ('local_a_second_norm', 'Local a″'), ('finite_remainder_norm', 'Finite remainder'),
                  ('quadratic_remainder_norm', 'Remainder after Q')]
    figure, axes = builder.plt.subplots(1, len(scenes), squeeze=False, figsize=(3.7*len(scenes), 3.6))
    for axis, scene in zip(axes[0], scenes):
        selected = sorted([row for row in rows if int(_number(row['scene'])) == scene], key=lambda row: _number(row['t']))
        for key, label in components:
            axis.plot([_number(row['t']) for row in selected], [_number(row.get(key)) for row in selected],
                      marker='o', markersize=3, label=label)
        axis.set_title(str(scene)); axis.set_xlabel('Amplitude t'); axis.set_ylabel('Whitened data norm')
        axis.grid(alpha=.2)
    figure.legend(*axes[0, 0].get_legend_handles_labels(), loc='lower center', ncol=5, fontsize=8, bbox_to_anchor=(.5, -.03))
    figure.suptitle('Offline truth-direction curvature decomposition')
    figure.tight_layout(rect=(0, .06, 1, .94))
    builder.save(figure, 'curvature_components', caption='Saved offline direction diagnostics; full, feedback, local and finite remainder norms')
    spaces = [('full_tangent', 'full_tangent_numeric_rank'), ('stable_tangent', 'stable_tangent_rank'),
              ('old32_chart', 'old_chart_rank'), ('calibration_nuisance', 'nuisance_rank')]
    figure, axes = builder.plt.subplots(4, len(scenes), squeeze=False, figsize=(3.7*len(scenes), 10.5))
    for i, (space, rank_key) in enumerate(spaces):
        for j, scene in enumerate(scenes):
            axis = axes[i, j]
            selected = sorted([row for row in rows if int(_number(row['scene'])) == scene], key=lambda row: _number(row['t']))
            for component, label in [('total', 'Full Q'), ('feedback', 'Feedback Q'), ('local', 'Local a″')]:
                axis.plot([_number(row['t']) for row in selected],
                          [_number(row.get(component+'_outside_'+space)) for row in selected],
                          marker='o', markersize=3, label=label)
            ranks = '/'.join(str(row.get(rank_key, '?')) for row in selected)
            axis.set_title(f'{scene} · {space.replace("_", " ")} (rank {ranks})', fontsize=8)
            axis.set_xlabel('Amplitude t'); axis.set_ylabel('Outside-space norm'); axis.grid(alpha=.2)
            axis.ticklabel_format(axis='y', style='sci', scilimits=(-3, 3))
    figure.legend(*axes[0, 0].get_legend_handles_labels(), loc='lower center', ncol=3, fontsize=8)
    figure.suptitle('Separate saved tangent/chart/nuisance projections; numerical residuals retained')
    figure.tight_layout(rect=(0, .025, 1, .965))
    builder.save(figure, 'curvature_outside_subspaces', caption='Full tangent, stable tangent, old 32D chart and nuisance are displayed as distinct diagnostics')


def _grid(points: np.ndarray):
    points = np.asarray(points, float)
    if points.ndim != 2 or points.shape[1] != 3 or not np.all(np.isfinite(points)):
        raise ValueError('PLOT_FINITE_3D_POINTS_REQUIRED')
    axes = tuple(np.unique(points[:, index]) for index in range(3))
    shape = tuple(len(axis) for axis in axes)
    if np.prod(shape) != len(points):
        raise ValueError('PLOT_REQUIRES_FULL_CARTESIAN_GRID')
    indices = tuple(np.searchsorted(axis, points[:, index]) for index, axis in enumerate(axes))
    flat = np.ravel_multi_index(indices, shape)
    if len(np.unique(flat)) != len(points):
        raise ValueError('PLOT_DUPLICATE_OR_MISSING_GRID_POINTS')
    # This maps original cell order into ascending [x,y,z], irrespective of file ordering.
    order = np.argsort(flat)
    return axes, shape, order


def _edges(axis: np.ndarray):
    if len(axis) == 1:
        return np.array([axis[0]-.5, axis[0]+.5])
    middle = .5*(axis[1:]+axis[:-1])
    return np.r_[axis[0]-.5*(axis[1]-axis[0]), middle, axis[-1]+.5*(axis[-1]-axis[-2])]


def _planes(volume: np.ndarray, axes):
    centers = [int(np.argmin(np.abs(axis-.5*(axis[0]+axis[-1])))) for axis in axes]
    ix, iy, iz = centers
    x, y, z = axes
    return [
        {'name': 'XY', 'h': x, 'v': y, 'horizontal': 'x', 'vertical': 'y', 'fixed': 'z',
         'fixed_value': float(z[iz]), 'values': volume[:, :, iz].T},
        {'name': 'XZ', 'h': x, 'v': z, 'horizontal': 'x', 'vertical': 'z', 'fixed': 'y',
         'fixed_value': float(y[iy]), 'values': volume[:, iy, :].T},
        {'name': 'YZ', 'h': y, 'v': z, 'horizontal': 'y', 'vertical': 'z', 'fixed': 'x',
         'fixed_value': float(x[ix]), 'values': volume[ix, :, :].T},
    ]


def _range(values: np.ndarray):
    finite = np.asarray(values)[np.isfinite(values)]
    if not finite.size:
        return (-1., 1.)
    low, high = float(finite.min()), float(finite.max())
    if high == low:
        margin = max(abs(low)*.05, 1e-6)
        low -= margin; high += margin
    return low, high


def _images(builder: _Figures, metric_rows: list[dict]):
    lookup = {(int(_number(row['scene'])), row['method']): row for row in metric_rows
              if _number(row.get('t')) == 1. and row.get('noise') == '20dB_nominal_difference'}
    for scene in SCENES:
        paths = []
        for path in sorted((builder.result/'images').glob(f'scene_{scene}_t*_20dB_nominal_difference.npz')):
            matched = re.fullmatch(r'scene_(\d+)_t([0-9.eE+-]+)_20dB_nominal_difference', path.stem)
            if matched and float(matched.group(2)) == 1.:
                paths.append(path)
        if not paths:
            builder.manifest['missing'].append({'scene': scene, 'source': 'nominal noisy saved image', 'status': 'NOT_AVAILABLE'})
            continue
        if len(paths) != 1:
            raise ValueError(f'PLOT_AMBIGUOUS_NOMINAL_IMAGE:{scene}')
        path = paths[0]
        geometry = builder.root/f'data/online/scene_{scene}.npz'
        builder.source(path); builder.source(geometry)
        with np.load(geometry, allow_pickle=False) as saved:
            coordinates, shape, order = _grid(saved['points'])
        with np.load(path, allow_pickle=False) as saved:
            if 'truth_OFFLINE' not in saved:
                raise ValueError(f'PLOT_SAVED_TRUTH_MISSING:{scene}')
            truth = np.asarray(saved['truth_OFFLINE']).reshape(-1).copy()
            estimates = {method: np.asarray(saved[method]).reshape(-1).copy() for method in IMAGE_METHODS if method in saved}
        if truth.size != len(order) or not np.all(np.isfinite(truth)):
            raise ValueError(f'PLOT_SAVED_TRUTH_INVALID:{scene}')
        for method, values in estimates.items():
            if values.size != len(order):
                raise ValueError(f'PLOT_IMAGE_MESH_SIZE_MISMATCH:{scene}:{method}')
        methods = ('truth_OFFLINE',)+IMAGE_METHODS
        slice_rows = []
        for component in ('real', 'imag'):
            truth_values = getattr(truth, component)
            low, high = _range(truth_values)
            volumes = {method: getattr(truth if method == 'truth_OFFLINE' else
                                      estimates.get(method, np.full(truth.shape, np.nan+1j*np.nan)), component)[order].reshape(shape)
                       for method in methods}
            plane_sets = {method: _planes(volume, coordinates) for method, volume in volumes.items()}
            cmap = builder.plt.get_cmap('viridis').with_extremes(under='#b2182b', over='#ffe552', bad='#e1e1e1')
            figure, axes = builder.plt.subplots(3, len(methods), figsize=(13.8, 9.0), squeeze=False)
            image = None
            for j, method in enumerate(methods):
                status = 'OFFLINE_TRUTH' if method == 'truth_OFFLINE' else lookup.get((scene, method), {}).get('status', 'STATUS_MISSING')
                values = truth_values if method == 'truth_OFFLINE' else getattr(estimates.get(method, np.full(truth.shape, np.nan+1j*np.nan)), component)
                finite = values[np.isfinite(values)]
                extremes = f'min {finite.min():.3g}, max {finite.max():.3g}' if finite.size else 'NO FINITE RESULT'
                outside = f'below/above: {np.count_nonzero(values<low)}/{np.count_nonzero(values>high)}'
                for i, plane in enumerate(plane_sets[method]):
                    axis = axes[i, j]
                    image = axis.pcolormesh(_edges(plane['h']), _edges(plane['v']), np.ma.masked_invalid(plane['values']),
                                           shading='flat', cmap=cmap, vmin=low, vmax=high, rasterized=True)
                    axis.set_aspect('equal')
                    axis.set_xlabel(plane['horizontal']); axis.set_ylabel(plane['vertical'])
                    axis.set_title(f"{LABELS.get(method, method)}\n{plane['name']}, {plane['fixed']}={plane['fixed_value']:.3g}", fontsize=8)
                    axis.text(.01, -.19, f'{status}\n{extremes}\n{outside}', transform=axis.transAxes,
                              fontsize=6.5, color='#a52c2c' if method != 'truth_OFFLINE' and status != 'OK' else '#333333')
                    if method != 'truth_OFFLINE' and method not in estimates:
                        axis.text(.5, .5, 'MISSING / FAILED', transform=axis.transAxes, ha='center', color='#9e2424', fontsize=8)
                    truth_plane = plane_sets['truth_OFFLINE'][i]['values']
                    for vi, vertical in enumerate(plane['v']):
                        for hi, horizontal in enumerate(plane['h']):
                            estimate = float(plane['values'][vi, hi]); label = float(truth_plane[vi, hi])
                            slice_rows.append({'scene': scene, 't': 1., 'noise': '20dB_nominal_difference',
                                'component': component, 'method': method, 'status': status, 'plane': plane['name'],
                                'fixed_axis': plane['fixed'], 'fixed_coordinate': plane['fixed_value'],
                                'horizontal_axis': plane['horizontal'], 'horizontal_coordinate': float(horizontal),
                                'vertical_axis': plane['vertical'], 'vertical_coordinate': float(vertical),
                                'truth': label, 'estimate': estimate, 'signed_error': estimate-label,
                                'truth_global_color_min': low, 'truth_global_color_max': high})
            figure.suptitle(f'Scene {scene} · nominal noisy · χ {component}; same truth-volume color range for every method')
            figure.subplots_adjust(wspace=.55, hspace=.75, right=.9, top=.9, bottom=.1)
            coloraxis = figure.add_axes((.92, .17, .015, .66))
            figure.colorbar(image, cax=coloraxis, extend='both', label=f'χ {component}')
            figure.text(.03, .015, 'Under-range red / over-range yellow; gray = nonfinite or missing. '
                        'Labels retain full-volume extrema and rejection status. Axes are original mesh coordinates.', fontsize=8)
            builder.save(figure, f'image_{scene}_{component}', caption='Saved nominal noisy central XY/XZ/YZ slices; truth-global shared material color limits',
                         metadata={'scene': scene, 'component': component, 'color_min': low, 'color_max': high,
                                   'limits_source': 'all saved truth cells for this object/component',
                                   'array_layout': 'ascending [x,y,z], displayed horizontal/vertical coordinates explicit'})
            errors = {method: volumes[method]-volumes['truth_OFFLINE'] for method in IMAGE_METHODS}
            finite_errors = np.concatenate([values[np.isfinite(values)] for values in errors.values()])
            limit = max(float(np.max(np.abs(finite_errors))) if finite_errors.size else 0., 1e-12)
            figure, axes = builder.plt.subplots(3, len(IMAGE_METHODS), figsize=(11.8, 8.5), squeeze=False)
            for j, method in enumerate(IMAGE_METHODS):
                for i, plane in enumerate(_planes(errors[method], coordinates)):
                    axis = axes[i, j]
                    image = axis.pcolormesh(_edges(plane['h']), _edges(plane['v']), np.ma.masked_invalid(plane['values']),
                                           shading='flat', cmap='RdBu_r', vmin=-limit, vmax=limit, rasterized=True)
                    axis.set_aspect('equal'); axis.set_xlabel(plane['horizontal']); axis.set_ylabel(plane['vertical'])
                    status = lookup.get((scene, method), {}).get('status', 'STATUS_MISSING')
                    axis.set_title(f"{LABELS.get(method, method)} · {status}\n{plane['name']}, {plane['fixed']}={plane['fixed_value']:.3g}", fontsize=8)
                    if method not in estimates:
                        axis.text(.5, .5, 'MISSING / FAILED', transform=axis.transAxes, ha='center', color='#9e2424', fontsize=8)
            figure.suptitle(f'Scene {scene} · signed χ {component} error, estimate − saved truth')
            figure.subplots_adjust(wspace=.45, hspace=.5, right=.9, top=.9)
            coloraxis = figure.add_axes((.92, .17, .015, .66))
            figure.colorbar(image, cax=coloraxis, label='Signed error')
            builder.save(figure, f'image_error_{scene}_{component}', caption='Signed central-slice errors; symmetric range shared across methods and three planes',
                         metadata={'scene': scene, 'component': component, 'error_color_min': -limit, 'error_color_max': limit})
        builder.raw(f'IMAGE_SLICES_{scene}.csv', slice_rows)


def _pareto(builder: _Figures, rows: list[dict]):
    if not rows:
        return
    time_keys = ('total_time_to_image_seconds', 'total_seconds', 'total_time_seconds', 'cold_total_seconds',
                 'total_N1_seconds', 'N1_total_seconds', 'N1_seconds', 'independent_total_time_seconds',
                 'total_wall_seconds', 'time_to_image_seconds', 'total_time_N1')
    fields = set(key for row in rows for key in row)
    time_key = next((key for key in time_keys if key in fields), None)
    if time_key is None:
        builder.manifest['missing'].append({'source': 'PARETO_TABLE.csv time column', 'status': 'UNSUPPORTED_SCHEMA', 'available_fields': sorted(fields)})
        return
    quality_key = next((key for key in ('full_chi_NRMSE', 'full_material_NRMSE', 'NRMSE') if key in fields), None)
    if quality_key is None:
        builder.manifest['missing'].append({'source': 'PARETO_TABLE.csv quality column', 'status': 'UNSUPPORTED_SCHEMA'})
        return
    figure, axes = builder.plt.subplots(1, 2, figsize=(11.5, 4.5))
    methods = _method_order(rows)
    colors = {method: builder.plt.get_cmap('tab10')(index % 10) for index, method in enumerate(methods)}
    missing = []
    for row in rows:
        time, error, method = _number(row.get(time_key)), _number(row.get(quality_key)), row.get('method', 'UNKNOWN')
        if not (np.isfinite(time) and np.isfinite(error)):
            missing.append(f"{row.get('scene', '?')}/{method}: {row.get('status', 'missing metric')}")
            continue
        marker = 'x' if _bad(row) else 'o'
        axes[0].scatter(time, error, marker=marker, color=colors[method], s=38)
        axes[0].annotate(str(row.get('scene', '')), (time, error), xytext=(3, 3), textcoords='offset points', fontsize=6)
        residual = _number(row.get('datafullresidual', row.get('difference_data_residual')))
        if np.isfinite(residual):
            axes[1].scatter(time, residual, marker=marker, color=colors[method], s=38)
        else:
            missing.append(f"{row.get('scene', '?')}/{method}: full residual {row.get('full_validation', 'NOT_RUN')}")
    axes[0].set_ylabel('Full χ NRMSE'); axes[1].set_ylabel('Paid full difference-data residual')
    for axis in axes:
        axis.set_xlabel(time_key.replace('_', ' ')); axis.grid(alpha=.2)
    handles = [builder.plt.Line2D([], [], marker='o', linestyle='', color=colors[method], label=LABELS.get(method, method)) for method in methods]
    figure.legend(handles=handles, loc='lower center', ncol=4, fontsize=8, bbox_to_anchor=(.5, -.02))
    figure.suptitle('Saved quality/time rows; no recomputed Pareto or gate labels')
    if missing:
        builder.manifest['missing'].append({'source': 'PARETO_TABLE.csv individual metrics', 'rows': missing})
        figure.text(.02, -.075, f'{len(missing)} absent/nonfinite metrics retained in manifest and raw CSV. Crosses = rejected/failed rows.', fontsize=8)
    figure.tight_layout(rect=(0, .08, 1, .94))
    builder.save(figure, 'quality_time_pareto', caption='All saved quality/time rows, including rejected estimates; missing paid residuals are not plotted as zero',
                 metadata={'time_column': time_key, 'quality_column': quality_key})


def make_plots(root) -> dict:
    """Save PNG/SVG figures, source CSV copies, plotted raw tables and manifest.

    Available datasets are plotted independently. Missing production outputs
    are declared in ``figures/a23/PLOT_MANIFEST.json``. This function neither
    imports a Maxwell implementation nor loads ``data/offline_eval`` labels.
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    builder = _Figures(Path(root).resolve())
    builder.plt = plt
    full = builder.preserve_csv('FULL_IMAGE_METRICS.csv')
    curvature = builder.preserve_csv('CURVATURE_DECOMPOSITION.csv')
    pareto = builder.preserve_csv('PARETO_TABLE.csv')
    with plt.rc_context({'font.family': 'DejaVu Sans', 'font.size': 9, 'svg.fonttype': 'none',
                         'axes.spines.top': False, 'axes.spines.right': False}):
        for name, action in (
            ('H1', lambda: _h1(builder)),
            ('finite_amplitudes', lambda: _finite_amplitudes(builder, full)),
            ('curvature', lambda: _curvature(builder, curvature)),
            ('images', lambda: _images(builder, full)),
            ('pareto', lambda: _pareto(builder, pareto)),
        ):
            try:
                action()
            except Exception as exc:
                builder.manifest['errors'].append({'stage': name, 'type': type(exc).__name__, 'reason': str(exc)})
                plt.close('all')
    builder.manifest['status'] = ('PARTIAL_RENDER_ERROR' if builder.manifest['errors'] else
                                  'FIGURES_GENERATED' if builder.manifest['figures'] else 'NOT_RUN_INPUTS_MISSING')
    path = builder.output/'PLOT_MANIFEST.json'
    path.write_text(json.dumps(_clean_json(builder.manifest), indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')
    return builder.manifest


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default=str(Path(__file__).resolve().parents[2]))
    arguments = parser.parse_args()
    result = make_plots(arguments.root)
    print(json.dumps({'status': result['status'], 'figures': len(result['figures']), 'errors': result['errors']}))
