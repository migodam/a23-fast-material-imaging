"""Mechanical, repeatable accounting over saved A23 receipts.

``summarize_cost(root)`` rebuilds four derived snapshots under results/a23.
It neither executes physics nor changes gates or source receipts. Resource
charges use inclusive terminal lifetimes; nested action spans are diagnostic.
Missing measurements remain null, with conservative allowances shown apart.
No hashes, connection values, executable paths or raw exception text are saved.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import json
import math
import os
from pathlib import Path
import tempfile
import time


_TERMINAL = {'COMPLETE', 'FAILED', 'TIMEOUT', 'BUDGET_BLOCKED', 'PASS', 'FAIL'}
_REMOTE_BILLING = (
    'action', 'status', 'transport_attempt', 'job_id', 'stage', 'device',
    'physics_job_launched', 'child_stop_confirmed', 'child_CPU_measurement_available',
    'remote_process_cpu_seconds', 'remote_controller_cpu_seconds', 'queue_query_cpu_seconds',
    'child_process_CPU_seconds', 'child_CPU_tail_seconds', 'gpu_tail_seconds',
    'controller_gpu_elapsed_seconds', 'job_gpu_seconds_already_paid',
    'job_receipt_summary', 'job_receipt_synthesized', 'job_receipt_preserved',
)


def _number(value):
    return (float(value) if type(value) in (int, float)
            and math.isfinite(value) and value >= 0 else None)


def _safe_label(value, default=None):
    if isinstance(value, str) and not any(ord(c) < 32 for c in value):
        return value
    return default


def _counts(value):
    if not isinstance(value, dict):
        return {}
    return {k: v for k, v in value.items()
            if _safe_label(k) is not None and _number(v) is not None}


def _family(label):
    """Classify raw names, without merging or summing instrumentation aliases."""
    if label in ('Maxwell_matvec_rhs',):
        return 'aggregate_instrumentation_no_alias_sum'
    if 'factorization' in label or 'LU_' in label:
        return 'factorizations_raw'
    if label.startswith(('full_forward_', 'full_tangent_', 'full_adjoint_')):
        if label.endswith(('RHS', 'rhs')):
            return 'full_solve_rhs_raw'
        if label.endswith('calls'):
            return 'full_solve_calls_raw'
    if label.startswith(('solve_', 'reduced_solve_', 'reduced_adjoint_')) and label.lower().endswith('rhs'):
        return 'linear_solve_rhs_raw'
    if label.startswith('L_') or 'residual_L_' in label:
        return 'L_matvec_and_audit_raw'
    if label.startswith('F_'):
        return 'F_matvec_raw'
    if label.startswith('G_') or 'Goff_' in label:
        return 'G_matvec_raw'
    if label.startswith('S_') or label.endswith('receiver_rhs'):
        return 'S_matvec_and_receiver_contraction_raw'
    if label.endswith('_bytes'):
        return 'bytes_raw'
    return 'other_raw'


def _atomic_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', newline='\n',
                                     dir=path.parent, delete=False) as output:
        temporary = Path(output.name)
        output.write(text)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class _Report:
    def __init__(self, root):
        self.root = root
        self.costs, self.timings, self.actions, self.issues = [], [], [], []
        self.counts = defaultdict(Counter)
        self.inputs = set()
        self.action_ids = set()

    def relative(self, path):
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return 'external_receipt/' + path.name

    def issue(self, code, source, **safe_fields):
        self.issues.append(dict(code=code, source=source, **safe_fields))

    def read(self, path):
        name = self.relative(path)
        self.inputs.add(name)
        try:
            value = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(value, dict):
                raise ValueError('expected object')
            return value
        except (OSError, ValueError, UnicodeError):
            self.issue('UNREADABLE_OR_PARTIAL_JSON_RECEIPT', name)
            return None

    def lines(self, path):
        name = self.relative(path)
        self.inputs.add(name)
        try:
            with path.open(encoding='utf-8') as source:
                for index, line in enumerate(source, 1):
                    if not line.strip():
                        continue
                    try:
                        row = json.loads(line)
                        if not isinstance(row, dict):
                            raise ValueError('expected object')
                        yield index, row
                    except ValueError:
                        self.issue('UNREADABLE_OR_PARTIAL_JSONL_ROW', name, line=index)
        except (OSError, UnicodeError):
            self.issue('UNREADABLE_OR_PARTIAL_JSONL_INPUT', name)

    def cost(self, identity, source, kind, scope, *, cpu=None, gpu=None,
             cpu_charge=None, gpu_charge=None, cpu_exact=True, gpu_exact=True,
             wall=None, status=None, quality='MEASURED', **fields):
        cpu, gpu = _number(cpu), _number(gpu)
        cpu_charge, gpu_charge = _number(cpu_charge), _number(gpu_charge)
        value = dict(schema='a23.cost_component.v1', component_id=identity,
            source=source, component_kind=kind, scope=scope,
            status=status, accounting_quality=quality,
            measured_process_cpu_seconds=cpu if cpu_exact else None,
            measured_gpu_occupation_seconds=gpu if gpu_exact else None,
            cpu_budget_charge_seconds=cpu if cpu_charge is None else cpu_charge,
            gpu_budget_charge_seconds=gpu if gpu_charge is None else gpu_charge,
            cpu_measurement_incomplete=cpu is None or not cpu_exact,
            gpu_measurement_incomplete=gpu is None or not gpu_exact,
            inclusive_wall_seconds=_number(wall), **fields)
        self.costs.append(value)
        if value['inclusive_wall_seconds'] is not None:
            self.timings.append(dict(schema='a23.timing.v1', source_id=identity,
                source=source, scope=scope, raw_event_label=None, record_kind='inclusive_lifetime',
                wall_seconds=value['inclusive_wall_seconds'], additive_runtime=False,
                reason='inclusive lifetime; never add nested spans or overlapping controller/local walls'))

    def receipt_counts(self, identity, source, scope, value):
        original = value
        value = _counts(value)
        if isinstance(original, dict) and len(value) != len(original):
            self.issue('INVALID_OR_UNMEASURED_RECEIPT_COUNTER', source,
                       raw_counter_labels=[k for k in original if _safe_label(k) and k not in value])
        self.counts[scope].update(value)
        for label, count in sorted(value.items()):
            self.actions.append(dict(schema='a23.action.v1', source_id=identity,
                source=source, scope=scope, record_kind='receipt_counter',
                raw_event_label=None, raw_counter_label=label, count=count,
                family=_family(label), contributes_to_count_summary=True))

    def event(self, identity, source, scope, row, *, counts_authoritative=False):
        if identity in self.action_ids:
            return
        self.action_ids.add(identity)
        counters = _counts(row.get('counters', {}))
        event = _safe_label(row.get('event'))
        fields = {k: row[k] for k in ('job', 'stage', 'test_book', 'test_scope', 'scene',
                                     'method', 'repeat', 'phase')
                  if isinstance(row.get(k), (str, int, float, bool))}
        error = row.get('error')
        error_type = error.get('type') if isinstance(error, dict) else str(error).split(':', 1)[0]
        error_type = error_type if isinstance(error_type, str) and error_type.isidentifier() else 'RECORDED_ERROR'
        self.actions.append(dict(schema='a23.action.v1', source_id=identity,
            source=source, scope=scope, record_kind='saved_action', raw_event_label=event,
            counters=counters, status=_safe_label(row.get('status')),
            contributes_to_count_summary=counts_authoritative,
            process_cpu_seconds=_number(row.get('process_cpu_seconds')),
            error_type=error_type if error else None,
            **fields))
        if counts_authoritative:
            self.counts[scope].update(counters)
        self.timings.append(dict(schema='a23.timing.v1', source_id=identity, source=source,
            scope=scope, raw_event_label=event, record_kind='action_span',
            wall_seconds=_number(row.get('wall_seconds')),
            exclusive_wall_seconds=_number(row.get('exclusive_wall_seconds')),
            process_cpu_seconds=_number(row.get('process_cpu_seconds')),
            additive_runtime=False, additive_resource_charge=False,
            reason='parent receipt bills this lifetime; CPU spans may overlap', **fields))


def _merge(report, target, identity, row, source, priority, fields):
    """Prefer terminal files to copied envelopes; do not bill copies again."""
    if identity not in target:
        target[identity] = (row, source, priority)
        return
    old, old_source, old_priority = target[identity]
    conflicts = [k for k in fields if k in old and k in row and old[k] != row[k]]
    if conflicts:
        report.issue('DUPLICATE_RECEIPT_VALUE_CONFLICT', source,
                     identity=identity, conflicting_fields=conflicts,
                     preferred_source=old_source if old_priority >= priority else source)
    if priority > old_priority:
        merged = dict(old); merged.update(row)
        target[identity] = (merged, source, priority)
    else:
        merged = dict(row); merged.update(old)
        target[identity] = (merged, old_source, old_priority)


def _remote_candidates(report, value, source, default_identity=None):
    """Known envelope keys only; private helper fields are never serialized."""
    if not isinstance(value, dict):
        return
    identity = _safe_label(value.get('transport_attempt'))
    if identity and any(k in value for k in ('remote_process_cpu_seconds',
                                            'remote_controller_cpu_seconds', 'job_receipt_summary')):
        yield identity, value, source
    for key in ('remote', 'remote_accounting', 'remote_receipt'):
        nested = value.get(key)
        if isinstance(nested, dict):
            yield from _remote_candidates(report, nested, source + ':' + key,
                                          identity or default_identity)


def _transport_inputs(report, base):
    local, remote = {}, {}
    unreadable = []
    directory = base / 'transport'
    for pattern, kind in (('local-*.json', 'local'), ('remote-*.json', 'remote')):
        for path in sorted(directory.glob(pattern)):
            row = report.read(path)
            if row is None:
                unreadable.append((kind, path.stem.split('-', 1)[-1], report.relative(path)))
                continue
            identity = _safe_label(row.get('transport_attempt'))
            if not identity:
                report.issue('TRANSPORT_ATTEMPT_ID_MISSING', report.relative(path))
                continue
            if kind == 'local':
                _merge(report, local, identity, row, report.relative(path), 3,
                       ('local_process_cpu_seconds', 'local_wall_seconds', 'action', 'status'))
            else:
                _merge(report, remote, identity, row, report.relative(path), 3, _REMOTE_BILLING)
            for rid, value, source in _remote_candidates(report, row, report.relative(path)):
                _merge(report, remote, rid, value, source, 3 if kind == 'remote' else 1, _REMOTE_BILLING)
    for filename, kind in (('LOCAL_TRANSPORT_LEDGER.jsonl', 'local'),
                           ('REMOTE_TRANSPORT_LEDGER.jsonl', 'remote')):
        path = directory / filename
        if not path.is_file():
            continue
        for index, row in report.lines(path):
            source = report.relative(path) + ':' + str(index)
            identity = _safe_label(row.get('transport_attempt'))
            if not identity:
                report.issue('TRANSPORT_ATTEMPT_ID_MISSING', source)
                continue
            if kind == 'local':
                _merge(report, local, identity, row, source, 2,
                       ('local_process_cpu_seconds', 'local_wall_seconds', 'action', 'status'))
            else:
                _merge(report, remote, identity, row, source, 2, _REMOTE_BILLING)
            for rid, value, nested_source in _remote_candidates(report, row, source):
                _merge(report, remote, rid, value, nested_source, 2 if kind == 'remote' else 1, _REMOTE_BILLING)
    for kind, identity, source in unreadable:
        if identity in (local if kind == 'local' else remote):
            continue  # An immutable file/ledger copy recovered this incomplete input.
        report.cost('unreadable_' + kind + ':' + identity, source,
                    'unreadable_transport_receipt', 'overhead', cpu=None,
                    gpu=0.0 if kind == 'local' else None,
                    status='UNKNOWN', quality='UNREADABLE_OR_PARTIAL_RECEIPT')
    return local, remote


def _scope(stage, device='cpu'):
    return 'cpu_tests' if stage == 'phase0' else 'production'


def _jobs(report, base, remote):
    jobs, provenance = {}, {}
    for identity, (row, source, _) in remote.items():
        job = _safe_label(row.get('job_id'))
        summary = row.get('job_receipt_summary')
        if job and isinstance(summary, dict):
            value = dict(summary, job=job, stage=row.get('stage'), device=row.get('device'),
                         synthesized_by_transport=bool(row.get('job_receipt_synthesized')),
                         child_CPU_measurement_available=row.get('child_CPU_measurement_available'))
            _merge(report, jobs, job, value, source + ':job_receipt_summary', 1,
                   ('process_cpu_seconds', 'gpu_occupation_seconds', 'counts', 'status'))
            provenance[job] = 'PROVISIONAL_TRANSPORT_JOB_SUMMARY'
    directories = sorted((base / 'jobs').glob('*'))
    for directory in directories:
        if not directory.is_dir():
            continue
        manifest = report.read(directory / 'job_manifest.json') if (directory / 'job_manifest.json').is_file() else {}
        receipt = directory / 'job_receipt.json'
        row = report.read(receipt) if receipt.is_file() else None
        job = _safe_label((row or {}).get('job', (row or {}).get('job_id')), directory.name)
        if row is not None:
            row = dict(row)
            for key in ('stage', 'device'):
                if row.get(key) is None and manifest:
                    row[key] = manifest.get(key)
            _merge(report, jobs, job, row, report.relative(receipt), 3,
                   ('process_cpu_seconds', 'gpu_occupation_seconds', 'counts', 'status'))
            provenance[job] = 'TERMINAL_JOB_RECEIPT'
        elif job not in jobs:
            jobs[job] = (dict(manifest or {}, status='ORPHAN_OR_ACTIVE'),
                         report.relative(directory), 0)
            provenance[job] = 'ORPHAN_OR_ACTIVE_JOB'
            report.issue('JOB_TERMINAL_RECEIPT_MISSING', report.relative(directory), job=job)
    for job, (row, source, _) in sorted(jobs.items()):
        stage, device = row.get('stage'), row.get('device')
        scope = _scope(stage, device)
        synthetic = bool(row.get('synthesized_by_transport'))
        terminal = row.get('status') in _TERMINAL
        exact = terminal and not synthetic
        cpu, gpu = _number(row.get('process_cpu_seconds')), _number(row.get('gpu_occupation_seconds'))
        if synthetic and row.get('child_CPU_measurement_available') is not True:
            cpu = None  # An unavailable Windows measurement is not a zero charge.
        if device == 'cpu' and gpu is None:
            gpu = 0.0  # A declared CPU job does not occupy the CUDA resource.
        report.cost('job:' + job, source, 'terminal_job', scope, cpu=cpu, gpu=gpu,
                    cpu_charge=cpu, gpu_charge=gpu, cpu_exact=exact,
                    gpu_exact=exact or (device == 'cpu' and gpu == 0.0),
                    wall=row.get('wall_seconds'), status=row.get('status'),
                    quality='SYNTHETIC_CONSERVATIVE' if synthetic else provenance[job], job=job,
                    stage=stage, device=device, counts_in_receipt='counts' in row)
        ledger = base / 'jobs' / job / 'ACTION_LEDGER.jsonl'
        if isinstance(row.get('counts'), dict):
            report.receipt_counts('job:' + job, source, scope, row['counts'])
            if synthetic or not terminal:
                report.issue('PARTIAL_JOB_ACTION_COUNTS', source, job=job)
            if stage == 'phase0' and not row['counts']:
                report.issue('PHASE0_PARENT_COUNTERS_DO_NOT_CAPTURE_INNER_UNIT_BOOKS', source, job=job)
        elif terminal:
            report.issue('TERMINAL_JOB_ACTION_COUNTS_MISSING', source, job=job)
        if ledger.is_file():
            for index, event in report.lines(ledger):
                report.event('job:' + job + ':event:' + str(index),
                             report.relative(ledger) + ':' + str(index), scope, event,
                             counts_authoritative=not isinstance(row.get('counts'), dict))
        elif provenance[job] == 'PROVISIONAL_TRANSPORT_JOB_SUMMARY':
            report.issue('JOB_ACTION_LEDGER_NOT_PULLED', source, job=job)
        if isinstance(row.get('exclusive_walls'), dict):
            for label, duration in sorted(row['exclusive_walls'].items()):
                report.timings.append(dict(schema='a23.timing.v1', source_id='job:' + job,
                    source=source, scope=scope, raw_event_label=label,
                    record_kind='receipt_exclusive_span', exclusive_wall_seconds=_number(duration),
                    additive_runtime=False, additive_resource_charge=False))
    return jobs


def _transport_costs(report, local, remote, jobs):
    transfers = []
    for identity, (row, source, _) in sorted(local.items()):
        report.cost('local_transport:' + identity, source, 'local_transport', 'overhead',
            cpu=row.get('local_process_cpu_seconds'), gpu=0.0, wall=row.get('local_wall_seconds'),
            status=row.get('status'), action=row.get('action'), transport_attempt=identity)
        if identity not in remote:
            report.issue('REMOTE_TRANSPORT_RECEIPT_MISSING', source, transport_attempt=identity)
            launched = (row.get('remote') or {}).get('physics_job_launched')
            report.cost('remote_transport_missing:' + identity, source, 'remote_controller_query',
                'overhead', cpu=None, gpu=0.0 if launched is False else None,
                status='UNKNOWN', quality='REMOTE_RECEIPT_NOT_AVAILABLE', transport_attempt=identity)
    for identity, (row, source, _) in sorted(remote.items()):
        if identity not in local:
            report.issue('LOCAL_TRANSPORT_RECEIPT_MISSING', source, transport_attempt=identity)
            report.cost('local_transport_missing:' + identity, source, 'local_transport',
                        'overhead', cpu=None, gpu=0.0, status='UNKNOWN',
                        quality='LOCAL_RECEIPT_NOT_AVAILABLE', transport_attempt=identity)
        aggregate = _number(row.get('remote_process_cpu_seconds'))
        controller = _number(row.get('remote_controller_cpu_seconds'))
        query = _number(row.get('queue_query_cpu_seconds'))
        exact = aggregate is not None or (controller is not None and query is not None)
        cpu = aggregate if aggregate is not None else (
            controller + query if controller is not None and query is not None else controller)
        report.cost('remote_controller:' + identity, source, 'remote_controller_query', 'overhead',
            cpu=cpu, cpu_charge=cpu, cpu_exact=exact, gpu=0.0,
            wall=row.get('remote_wall_seconds'), status=row.get('status'),
            transport_attempt=identity, action=row.get('action'),
            raw_remote_controller_cpu_seconds=controller, raw_queue_query_cpu_seconds=query,
            combined_cpu_used_once=True)
        if row.get('physics_job_launched'):
            job = _safe_label(row.get('job_id'))
            device = row.get('device')
            cpu_tail = _number(row.get('child_CPU_tail_seconds'))
            measured = row.get('child_CPU_measurement_available') is True
            if not measured:
                cpu_tail = None  # The driver may carry a placeholder zero when measurement failed.
            if cpu_tail is None and measured and job in jobs:
                child_cpu = _number(row.get('child_process_CPU_seconds'))
                paid_cpu = _number(jobs[job][0].get('process_cpu_seconds'))
                if child_cpu is not None and paid_cpu is not None:
                    cpu_tail = max(0.0, child_cpu - paid_cpu)
            gpu_tail = _number(row.get('gpu_tail_seconds'))
            if device == 'cpu' and gpu_tail is None:
                gpu_tail = 0.0
            stopped = row.get('child_stop_confirmed') is True and row.get('status') != 'STOP_UNCONFIRMED'
            report.cost('child_tail:' + identity, source, 'child_cpu_and_gpu_tail',
                _scope(row.get('stage'), device), cpu=cpu_tail, cpu_charge=cpu_tail,
                cpu_exact=measured and stopped, gpu=gpu_tail, gpu_charge=gpu_tail,
                gpu_exact=stopped, status=row.get('status'), transport_attempt=identity,
                job=job, stage=row.get('stage'), device=device,
                quality='MEASURED_TAIL' if stopped else 'PARTIAL_OR_STOP_UNCONFIRMED')
            if job not in jobs:
                report.issue('LAUNCHED_JOB_WITHOUT_TERMINAL_OR_PROVISIONAL_RECEIPT', source, job=job)
                report.cost('orphan_job:' + str(job), source, 'orphan_job',
                            _scope(row.get('stage'), device), cpu=None,
                            gpu=0.0 if device == 'cpu' else None, status='UNKNOWN', job=job)
        if row.get('action') == 'pull':
            transfers.append(dict(transport_attempt=identity, status=row.get('status'),
                pulled_uncompressed_bytes=_number(row.get('uncompressed_bytes')),
                pulled_member_count=_number(row.get('member_count')),
                cache_skipped_bytes=_number(row.get('regenerable_cache_bytes_skipped')),
                cache_skipped_members=_number(row.get('regenerable_cache_members_skipped')),
                remote_caches_retained=row.get('remote_caches_retained'),
                metadata_policy=row.get('metadata_policy')))
    return transfers


def _test_inputs(report, base):
    directory = base / 'theory_verification'
    standalone, book_counts, validator_copies = {}, Counter(), set()
    for path in sorted(directory.glob('*.json')):
        row = report.read(path)
        if row is None:
            report.cost('unreadable_test:' + path.stem, report.relative(path),
                        'unreadable_unit_receipt', 'cpu_tests', cpu=None, gpu=0.0,
                        status='UNKNOWN', quality='UNREADABLE_OR_PARTIAL_RECEIPT')
            continue
        if not any(k in row for k in ('process_cpu_seconds', 'child_cpu_seconds', 'book_receipts')):
            continue
        identity = 'test:' + path.stem
        standalone[identity] = row
        if _safe_label(row.get('script')) and 'child_cpu_seconds' in row:
            validator_copies.add((row.get('script'), row.get('return_code'),
                                  row.get('wall_seconds'), row.get('child_cpu_seconds'), row.get('device')))
        cpu = row.get('process_cpu_seconds', row.get('child_cpu_seconds'))
        gpu = row.get('gpu_occupation_seconds', 0.0 if row.get('device') == 'cpu' else None)
        status = row.get('status', 'PASS' if row.get('success') is True else
                         'FAIL' if row.get('success') is False else 'RECORDED')
        report.cost(identity, report.relative(path), 'standalone_unit_parent', 'cpu_tests',
                    cpu=cpu, gpu=gpu, wall=row.get('wall_seconds'), status=status,
                    book_lifetimes_overlap_and_are_not_billed=True,
                    tests_run=row.get('tests_run'), run_id=row.get('run_id'))
        books = row.get('book_receipts', [])
        if isinstance(books, list):
            for index, book in enumerate(books):
                if not isinstance(book, dict):
                    continue
                source = report.relative(path) + ':book_receipts:' + str(index)
                bid = identity + ':book:' + str(book.get('test_book', index))
                counts = _counts(book.get('counts', {}))
                book_counts.update(counts)
                report.receipt_counts(bid, source, 'cpu_tests', counts)
                report.timings.append(dict(schema='a23.timing.v1', source_id=bid, source=source,
                    scope='cpu_tests', raw_event_label=None, record_kind='overlapping_test_book',
                    wall_seconds=_number(book.get('wall_seconds')),
                    process_cpu_seconds=_number(book.get('process_cpu_seconds')),
                    additive_runtime=False, additive_resource_charge=False))
                if isinstance(book.get('exclusive_walls'), dict):
                    for label, duration in sorted(book['exclusive_walls'].items()):
                        report.timings.append(dict(schema='a23.timing.v1', source_id=bid, source=source,
                            scope='cpu_tests', raw_event_label=label, record_kind='test_book_exclusive_span',
                            exclusive_wall_seconds=_number(duration), additive_runtime=False,
                            additive_resource_charge=False))
        if not books and isinstance(row.get('counts'), dict):
            report.receipt_counts(identity, report.relative(path), 'cpu_tests', row['counts'])
    adapter = directory / 'ADAPTER_ACTION_LEDGER.jsonl'
    if adapter.is_file():
        ledger_counts = Counter()
        rows = list(report.lines(adapter))
        for index, event in rows:
            ledger_counts.update(_counts(event.get('counters', {})))
            report.event('adapter:event:' + str(index), report.relative(adapter) + ':' + str(index),
                         'cpu_tests', event, counts_authoritative=not standalone)
        if standalone:
            report.issue('ADAPTER_LEDGER_PARENT_RUN_MAPPING_NOT_RECORDED', report.relative(adapter),
                         action_cost_billed_via_test_parent_receipts=True)
            if ledger_counts - book_counts:
                report.issue('ADAPTER_ACTION_COUNTERS_WITHOUT_MATCHING_BOOK_RECEIPTS',
                             report.relative(adapter), raw_counts=dict(ledger_counts - book_counts))
        else:
            report.cost('adapter_orphan_lifetime', report.relative(adapter), 'orphan_test_lifetime',
                        'cpu_tests', cpu=None, gpu=0.0, status='UNKNOWN')
    validator = directory / 'ORIGINAL_VALIDATORS_LEDGER.jsonl'
    if validator.is_file():
        for index, row in report.lines(validator):
            source = report.relative(validator) + ':' + str(index)
            fingerprint = (row.get('script'), row.get('return_code'), row.get('wall_seconds'),
                           row.get('child_cpu_seconds'), row.get('device'))
            if fingerprint in validator_copies:
                report.issue('DUPLICATE_VALIDATOR_COPY_NOT_BILLED', source)
                continue
            report.cost('validator:' + str(index), source, 'standalone_validator_child', 'cpu_tests',
                cpu=row.get('child_cpu_seconds'), gpu=0.0 if row.get('device') == 'cpu' else None,
                wall=row.get('wall_seconds'), status='PASS' if row.get('return_code') == 0 else 'FAIL',
                script=_safe_label(row.get('script')), source_byte_preserved=row.get('source_byte_preserved'))
    return standalone


def _external_inputs(report, base):
    path = base / 'EXTERNAL_CPU_LEDGER.jsonl'
    rows = list(report.lines(path)) if path.is_file() else []
    has_h1, has_asset = False, False
    for index, row in rows:
        source = report.relative(path) + ':' + str(index)
        event = _safe_label(row.get('event'), 'external_cpu')
        description = ' '.join(str(row.get(k, '')) for k in ('event', 'scope', 'measurement', 'cost_kind')).casefold()
        has_h1 |= 'h1' in description and any(k in description for k in ('standalone', 'delegated', 'verification'))
        has_asset |= 'preflight' in description and ('asset' in description or 'initial' in description)
        allowance = any(k in description for k in ('allowance', 'conservative', 'unmeasured', 'estimated'))
        allowance |= row.get('measured') is False
        cpu = row.get('cpu_seconds', row.get('process_cpu_seconds', row.get('child_cpu_seconds')))
        charge = row.get('cpu_allowance_seconds', row.get('conservative_cpu_seconds', cpu))
        if 'cpu_allowance_seconds' in row or 'conservative_cpu_seconds' in row:
            allowance = True
        report.cost('external_cpu:' + str(index), source, 'external_cpu', 'overhead',
            cpu=cpu, cpu_charge=charge, cpu_exact=not allowance, gpu=0.0,
            wall=row.get('wall_seconds'), status=row.get('status', 'RECORDED'),
            quality='CONSERVATIVE_ALLOWANCE' if allowance else 'MEASURED', raw_event_label=event)
    if not has_h1:
        report.cost('parent_allowance:h1_standalone', 'parent_authorized_allowance/h1_standalone',
            'delegated_h1_unit_verification', 'cpu_tests', cpu=None, cpu_charge=1.0, gpu=0.0,
            wall=0.147, status='RECORDED', quality='CONSERVATIVE_ALLOWANCE',
            measured_cpu_not_recorded=True, action_counts_not_recorded=True,
            allowance_authority='parent supplied 1 second; wall 0.147 seconds')
    if not has_asset:
        report.cost('parent_allowance:initial_asset_preflight', 'parent_authorized_allowance/initial_asset_preflight',
            'initial_asset_transport_preflight', 'overhead', cpu=0.06473, cpu_charge=0.1,
            cpu_exact=False, gpu=0.0, wall=3.250824, status='RECORDED',
            quality='PARTIAL_MEASUREMENT_WITH_CONSERVATIVE_ALLOWANCE',
            known_partial_cpu_seconds=0.06473,
            known_local_and_controller_cpu_seconds=0.06473,
            queue_query_cpu_unmeasured=True, allowance_authority='parent supplied 0.1 second total charge')


def _resource_summary(costs, resource):
    measured_key = ('measured_process_cpu_seconds' if resource == 'cpu'
                    else 'measured_gpu_occupation_seconds')
    charge_key = resource + '_budget_charge_seconds'
    unknown_key = resource + '_measurement_incomplete'
    measured = sum(r[measured_key] for r in costs if r[measured_key] is not None)
    partial = sum(_number(r.get('known_partial_cpu_seconds')) or 0.0 for r in costs) if resource == 'cpu' else 0.0
    charge = sum(r[charge_key] for r in costs if r[charge_key] is not None)
    unknown = [r['component_id'] for r in costs if r[unknown_key]]
    uncharged = [r['component_id'] for r in costs if r[charge_key] is None]
    return dict(exact_total_seconds=None if unknown else measured,
                known_measured_seconds=measured, conservative_budget_charge_seconds=charge,
                known_partial_measured_seconds=partial, known_measured_lower_bound_seconds=measured + partial,
                unknown_component_ids=unknown, uncharged_unknown_component_ids=uncharged,
                complete=not unknown, conservative_charge_complete=not uncharged)


def summarize_cost(root) -> dict:
    """Save COST/TIMING/ACTION ledgers and COST_SUMMARY without running jobs.

    Full terminal receipts override transport job summaries. A transport attempt
    is counted once across files, append ledgers and copied envelopes. Combined
    remote-process CPU already contains controller/query CPU. Child CPU tails
    and GPU tails are separate additional resource components. Receipt counts
    override their event copies; test-book lifetimes never bill their parent a
    second time. Conservative CPU allowances are not exact measurements.
    """
    started_wall, started_cpu = time.perf_counter(), time.process_time()
    root = Path(root).expanduser().resolve()
    base = root / 'results/a23'
    report = _Report(root)
    local, remote = _transport_inputs(report, base)
    jobs = _jobs(report, base, remote)
    transfers = _transport_costs(report, local, remote, jobs)
    _test_inputs(report, base)
    _external_inputs(report, base)
    raw_counts = {scope: dict(sorted(value.items())) for scope, value in sorted(report.counts.items())}
    families = {}
    for scope, counts in raw_counts.items():
        families[scope] = {}
        for label, count in counts.items():
            families[scope].setdefault(_family(label), {})[label] = count
    cpu, gpu = _resource_summary(report.costs, 'cpu'), _resource_summary(report.costs, 'gpu')
    transfer_totals = {key: sum(row[key] for row in transfers if row[key] is not None)
        for key in ('pulled_uncompressed_bytes', 'pulled_member_count',
                    'cache_skipped_bytes', 'cache_skipped_members')}
    summary = dict(schema='a23.cost_summary.v1',
        status='COMPLETE' if cpu['complete'] and gpu['complete'] else 'COMPLETE_WITH_UNKNOWN_COSTS',
        resources={'cpu': cpu, 'gpu': gpu},
        process_cpu_seconds=cpu['exact_total_seconds'],
        gpu_occupation_seconds=gpu['exact_total_seconds'],
        cpu_budget_charge_seconds=cpu['conservative_budget_charge_seconds'],
        gpu_budget_charge_seconds=gpu['conservative_budget_charge_seconds'],
        cpu_soft_target_seconds=7200.0, gpu_occupation_cap_seconds=7200.0,
        cost_components=len(report.costs), job_entries_total=len(jobs),
        terminal_or_provisional_jobs=sum(row.get('status') in _TERMINAL for row, _, _ in jobs.values()),
        orphan_or_active_jobs=sum(row.get('status') not in _TERMINAL for row, _, _ in jobs.values()),
        unique_local_transport_attempts=len(local), unique_remote_transport_attempts=len(remote),
        raw_action_counts_by_scope=raw_counts, canonical_action_families_by_scope=families,
        instrumentation_aliases_are_not_added=True,
        prior_costs_in_job_manifests_are_not_added_again=True,
        unit_action_count_coverage='partial: separate delegated H1 has no receipt counters; phase0 parent books do not capture inner test books',
        transport_transfers=transfers, transfer_totals=transfer_totals,
        issues=report.issues, input_sources=sorted(report.inputs),
        resource_rule='terminal CUDA job lifetime plus unique controller GPU tail; all host work included',
        cpu_rule='job CPU + child CPU tail + remote controller/query once + local transport + standalone measured costs; allowances separate',
        wall_rule='runtime uses inclusive lifetime per record; nested exclusive spans and overlapping walls are never summed',
        standalone_unit_costs_separate_from_production=True,
        method_cost_attribution='not inferred by this mechanical summary; parent owns independent method attribution',
        source_receipts_modified=False, scientific_gates_modified=False,
        new_SHA256_checks=0, connection_values_stored=False,
        report_generation=dict(process_cpu_seconds=time.process_time()-started_cpu,
                               wall_seconds=time.perf_counter()-started_wall,
                               additive_charge=False,
                               reason='may be inside a terminal report job or external metadata allowance'))
    for filename, rows in (('COST_LEDGER.jsonl', report.costs),
                           ('TIMING_LEDGER.jsonl', report.timings),
                           ('ACTION_LEDGER.jsonl', report.actions)):
        _atomic_text(base / filename, ''.join(json.dumps(row, sort_keys=True, allow_nan=False) + '\n'
                                             for row in rows))
    _atomic_text(base / 'COST_SUMMARY.json', json.dumps(summary, sort_keys=True, indent=2, allow_nan=False) + '\n')
    return summary
