"""Bounded A23 transport; credentials remain in an external/ignored config.

The trusted existing helper is supplied by --transport-helper or
A23_TRANSPORT_HELPER. It is not vendored here. Deploy online source/runtime
inputs and evaluator-only labels in separate invocations. No SHA256 is used.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import tempfile
import textwrap
import time
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "D:/AI/A23_FAST_MATERIAL_IMAGING"
SHARED = "D:/AI/A20_OPM_IMAGING"
SHARED_LOCK = SHARED + "/runs/gpu.lock"
PYTHON = "D:/python/python.exe"
STAGES = ("micro", "phase0", "h1", "pilot", "report")
GPU_CAP = 7200.0
STOP_RESERVE = 30.0
MAX_ZIP_BYTES = 2 * 1024**3
JOB_PATTERN = r"a23-[A-Za-z0-9_-]{1,112}"


class TransportError(RuntimeError):
    """Fixed diagnostic code only; never private connection values."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _job(value):
    if not isinstance(value, str) or not re.fullmatch(JOB_PATTERN, value):
        raise TransportError("INVALID_A23_JOB_ID")
    return value


def _safe_name(name):
    if (not isinstance(name, str) or not name or name.startswith("/")
            or "\\" in name or ":" in name or any(ord(c) < 32 for c in name)
            or "//" in name or name.endswith("/")):
        return False
    parts = name.split('/')
    return bool(parts) and all(p not in (".", "..", "") for p in parts)


def _safe_destination(root, name):
    if not _safe_name(name):
        raise TransportError("UNSAFE_ARCHIVE_PATH")
    path = root.joinpath(*PurePosixPath(name).parts)
    current = path
    while current != root:
        if current.is_symlink():
            raise TransportError("SYMLINK_DESTINATION_REFUSED")
        current = current.parent
    if root.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise TransportError("DESTINATION_OUTSIDE_A23_ROOT")
    return path


def _load_helper(root, helper_path):
    selected = helper_path or os.environ.get("A23_TRANSPORT_HELPER")
    if not selected:
        raise TransportError("A23_TRANSPORT_HELPER_REQUIRED")
    path = Path(selected).expanduser().resolve()
    if not path.is_file() or path.suffix != ".py":
        raise TransportError("A23_TRANSPORT_HELPER_UNAVAILABLE")
    try:
        spec = importlib.util.spec_from_file_location("a23_existing_private_transport", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except BaseException:
        raise TransportError("A23_TRANSPORT_HELPER_IMPORT_FAILED") from None
    if any(not callable(getattr(module, name, None))
           for name in ("connection", "_python", "_windows_cpu_source")):
        raise TransportError("A23_TRANSPORT_HELPER_API_MISMATCH")
    module.ROOT, module.REMOTE, module.SHARED = root, REMOTE, SHARED
    module.SHARED_LOCK, module.PYTHON = SHARED_LOCK, PYTHON
    return module


def _connection(helper, private_config, root):
    path = Path(private_config).expanduser().resolve()
    if not path.is_file():
        raise TransportError("PRIVATE_CONNECTION_CONFIG_UNAVAILABLE")
    if path.is_relative_to(root) and "private" not in path.relative_to(root).parts:
        raise TransportError("PRIVATE_CONFIG_MUST_BE_EXTERNAL_OR_IGNORED_PRIVATE")
    if path.is_relative_to(root):
        ignored = subprocess.run(['git', 'check-ignore', '--quiet', '--',
                                  path.relative_to(root).as_posix()], cwd=root,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=8)
        if ignored.returncode:
            raise TransportError("IN_ROOT_PRIVATE_CONFIG_MUST_BE_GIT_IGNORED")
    try:
        connection = helper.connection(path, root=root)
        original_checked = connection._checked
        def bounded_checked(argv, *, category, timeout=None):
            return original_checked(argv, category=category,
                                    timeout=120 if timeout is None else timeout)
        connection._checked = bounded_checked
        return connection
    except BaseException:
        raise TransportError("PRIVATE_CONNECTION_CONFIG_INVALID") from None


def deployment_members(root, scope):
    """Narrow code/runtime or evaluator-only whitelist; never old results."""
    if scope not in ("online", "offline-evaluation"):
        raise TransportError("INVALID_DEPLOY_SCOPE")
    paths = set()
    if scope == "online":
        for folder in ("src/a20", "src/a23", "vendor", "tests"):
            directory = root / folder
            paths.update(p for p in directory.rglob("*.py") if "__pycache__" not in p.parts)
        paths.add(root / "FROZEN_CONFIG.json")
        provenance = root / "vendor/a17/UPSTREAM_PROVENANCE.json"
        if provenance.is_file():
            paths.add(provenance)
        paths.update((root / "data/online").glob("*.npz"))
        for name in ("validate_theory.py", "validate_extra.py"):
            path = root / "validation" / name
            if path.is_file():
                paths.add(path)
        required = (root / "src/a23/__init__.py", root / "FROZEN_CONFIG.json")
        if any(not p.is_file() for p in required):
            raise TransportError("A23_ONLINE_DEPLOY_INPUTS_INCOMPLETE")
    else:
        paths.update((root / "data/offline_eval").glob("*.npz"))
        if not paths:
            raise TransportError("A23_OFFLINE_EVALUATOR_INPUTS_MISSING")
    names = []
    total = 0
    for path in sorted(paths):
        name = path.relative_to(root).as_posix()
        if not _safe_name(name) or path.is_symlink() or not path.is_file():
            raise TransportError("INVALID_DEPLOY_MEMBER")
        _safe_destination(root, name)
        if any(part in ("private", ".git", "__pycache__") for part in path.relative_to(root).parts):
            raise TransportError("PRIVATE_OR_INHERITED_MEMBER_REFUSED")
        total += path.stat().st_size
        names.append(name)
    if not names or total > 128 * 1024**2:
        raise TransportError("DEPLOY_WHITELIST_EMPTY_OR_TOO_LARGE")
    return names


def _prelude(helper, options):
    return (
        "import datetime,json,math,os,pathlib,re,stat,subprocess,sys,tempfile,time,zipfile\n"
        + "OPTS=" + repr(options) + "\n"
        + "REMOTE=" + repr(REMOTE) + "\nSHARED=" + repr(SHARED)
        + "\nLOCK=" + repr(SHARED_LOCK) + "\nPYTHON=" + repr(PYTHON) + "\n"
        + "GPU_CAP=7200.0\nSTOP_RESERVE=30.0\nMAX_ZIP_BYTES=" + repr(MAX_ZIP_BYTES) + "\n"
        + "JOB_PATTERN=" + repr(JOB_PATTERN) + "\n"
        + helper._windows_cpu_source() + "\n"
        + textwrap.dedent(r'''
            origin=globals().get('_a22_remote_process_origin',time.perf_counter())
            root=pathlib.Path(REMOTE)
            query_cpu=0.0
            class Refusal(RuntimeError):
                def __init__(self,code): self.code=code;super().__init__(code)
            def refuse(code): raise Refusal(code)
            def number(value):
                if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
                    refuse('INVALID_BUDGET_VALUE')
                return float(value)
            def safe_name(name):
                return (isinstance(name,str) and bool(name) and not name.startswith('/')
                    and '\\' not in name and ':' not in name and '//' not in name and not name.endswith('/')
                    and not any(ord(c)<32 for c in name)
                    and all(p not in ('','.', '..') for p in name.split('/')))
            def destination(name):
                if not safe_name(name): refuse('UNSAFE_ARCHIVE_PATH')
                p=root.joinpath(*pathlib.PurePosixPath(name).parts)
                cursor=p
                while cursor!=root:
                    if cursor.is_symlink(): refuse('SYMLINK_DESTINATION_REFUSED')
                    cursor=cursor.parent
                if root.is_symlink() or not p.resolve().is_relative_to(root.resolve()): refuse('DESTINATION_OUTSIDE_A23_ROOT')
                return p
            def write_json(path,value):
                path.parent.mkdir(parents=True,exist_ok=True)
                with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,delete=False) as f:
                    temporary=pathlib.Path(f.name);json.dump(value,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
                try: os.replace(temporary,path)
                finally: temporary.unlink(missing_ok=True)
            def query(arguments):
                global query_cpu
                process=subprocess.Popen(arguments,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                try: output,error=process.communicate(timeout=8)
                except subprocess.TimeoutExpired:
                    process.kill();output,error=process.communicate(timeout=3)
                finally: query_cpu+=measured_cpu(process)
                return process.returncode,output
            def queue_clear():
                code,out=query(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'])
                if code or out.strip(): refuse('GPU_QUEUE_NOT_CLEAR')
            def error_fields(error):
                row={'error_type':type(error).__name__}
                if isinstance(error,Refusal): row['error_code']=error.code
                return row
            def record(row):
                if row.get('physics_job_launched') and row.get('device')=='cuda':
                    row['controller_gpu_elapsed_seconds']=time.perf_counter()-origin
                    row['gpu_tail_seconds']=max(0.0,row['controller_gpu_elapsed_seconds']-row.get('job_gpu_seconds_already_paid',0.0))
                row.update(transport_attempt=OPTS['attempt'],action=OPTS['action'],
                    utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    remote_controller_cpu_seconds=time.process_time(),queue_query_cpu_seconds=query_cpu,
                    remote_process_cpu_seconds=time.process_time()+query_cpu,
                    remote_wall_seconds=time.perf_counter()-origin,
                    child_CPU_measurement_available=child_cpu_measurement_available,
                    connection_values_stored=False)
                directory=root/'results/a23/transport'
                path=directory/('remote-'+OPTS['attempt']+'.json')
                if path.exists(): refuse('TRANSPORT_RECEIPT_ALREADY_EXISTS')
                write_json(path,row)
                with (directory/'REMOTE_TRANSPORT_LEDGER.jsonl').open('a',encoding='utf-8') as f:
                    f.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n')
                print(json.dumps(row,sort_keys=True,allow_nan=False))
            ''')
    )


PREFLIGHT_BODY = r'''
row={'status':'COMPLETE','gpu_tail_seconds':0.0,'physics_job_launched':False}
try:
    import platform,importlib.metadata
    row['python']=platform.python_version();row['runtime_versions']={}
    for name in ('numpy','scipy','torch'):
        try: row['runtime_versions'][name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: row['runtime_versions'][name]='UNAVAILABLE'
    row['shared_lock_exists']=pathlib.Path(LOCK).exists()
    code,out=query(['nvidia-smi','--query-gpu=name,memory.total,memory.used,utilization.gpu','--format=csv,noheader'])
    row['GPU_query_success']=code==0
    row['GPU_summary']=out.decode('utf-8',errors='replace').strip()[:180] if code==0 else 'UNAVAILABLE'
    code,out=query(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'])
    row['queue_query_success']=code==0;row['queue_busy']=bool(out.strip()) if code==0 else None
    row['remote_root_exists']=root.is_dir()
except BaseException as error:
    row.update(status='FAILED',**error_fields(error))
record(row)
'''


DEPLOY_BODY = r'''
row={'status':'FAILED','scope':OPTS['scope'],'gpu_tail_seconds':0.0,'physics_job_launched':False}
try:
    if pathlib.Path(LOCK).exists(): refuse('SHARED_LOCK_EXISTS')
    queue_clear()
    archive=destination(OPTS['archive'])
    expected=set(OPTS['members'])
    seen=set();plan=[];total=0
    with zipfile.ZipFile(archive) as z:
        for member in z.infolist():
            name=member.filename
            if name not in expected or not safe_name(name) or name.casefold() in seen:
                refuse('INVALID_DEPLOY_ARCHIVE_MEMBER')
            seen.add(name.casefold())
            if stat.S_ISLNK(member.external_attr>>16): refuse('ZIP_SYMLINK_REFUSED')
            if OPTS['scope']=='offline-evaluation' and not (name.startswith('data/offline_eval/') and name.endswith('.npz')):
                refuse('OFFLINE_DEPLOY_BOUNDARY_FAILED')
            if OPTS['scope']=='online' and (name.startswith('data/offline_eval/') or 'private' in pathlib.PurePosixPath(name).parts):
                refuse('ONLINE_DEPLOY_BOUNDARY_FAILED')
            total+=member.file_size
            if total>128*1024**2: refuse('DEPLOY_ARCHIVE_TOO_LARGE')
            target=destination(name);payload=z.read(member)
            immutable=name=='FROZEN_CONFIG.json' or name.startswith('data/')
            if target.exists() and immutable and target.read_bytes()!=payload:
                refuse('IMMUTABLE_CONFIG_OR_DATA_CONFLICT')
            plan.append((target,payload))
        if len(seen)!=len(expected): refuse('DEPLOY_MEMBER_SET_MISMATCH')
    if pathlib.Path(LOCK).exists(): refuse('SHARED_LOCK_EXISTS')
    queue_clear()
    for target,payload in plan:
        if target.exists() and target.read_bytes()==payload: continue
        target.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile('wb',dir=target.parent,delete=False) as f:
            temporary=pathlib.Path(f.name);f.write(payload)
        try: os.replace(temporary,target)
        finally: temporary.unlink(missing_ok=True)
    archive.unlink()
    row.update(status='COMPLETE',member_count=len(plan),uncompressed_bytes=total,
        offline_evaluator_only=OPTS['scope']=='offline-evaluation',private_files_transferred=False)
except BaseException as error:
    row.update(**error_fields(error))
record(row)
'''


RUN_BODY = r'''
row={'status':'FAILED','job_id':OPTS['job'],'stage':OPTS['stage'],'device':OPTS['device'],
    'gpu_tail_seconds':0.0,'physics_job_launched':False,'foreground':True}
child=None;child_cpu=0.0;owned_lock=None;receipt=None
job=OPTS['job'];device=OPTS['device'];receipt_path=root/'results/a23/jobs'/job/'job_receipt.json'
def observe_lock():
    global owned_lock
    try:
        payload=pathlib.Path(LOCK).read_bytes();owner=json.loads(payload)
        if (child is not None and owner.get('pid')==child.pid
                and owner.get('job_id',owner.get('job',job))==job
                and owner.get('root',REMOTE)==REMOTE):
            owned_lock=payload
    except (OSError,ValueError): pass
def stop_child():
    global child_cpu,query_cpu
    if child is None or child.poll() is not None: return
    observe_lock();child_cpu=max(child_cpu,measured_cpu(child))
    try:
        code,out=query(['taskkill.exe','/PID',str(child.pid),'/T','/F'])
        child.wait(timeout=4)
    except BaseException:
        if child.poll() is None:
            child.kill()
            try: child.wait(timeout=3)
            except subprocess.TimeoutExpired: pass
    child_cpu=max(child_cpu,measured_cpu(child))
try:
    if not re.fullmatch(JOB_PATTERN,job): refuse('INVALID_A23_JOB_ID')
    config=json.loads((root/'FROZEN_CONFIG.json').read_text(encoding='utf-8'))
    cap=min(GPU_CAP,number(config.get('gpu_occupation_cap_seconds',GPU_CAP)))
    paid=0.0
    for path in (root/'results/a23/jobs').glob('*/job_receipt.json'):
        item=json.loads(path.read_text(encoding='utf-8'))
        if 'gpu_occupation_seconds' in item: used=number(item['gpu_occupation_seconds'])
        elif item.get('device')=='cuda': used=number(item['wall_seconds'])
        elif item.get('device')=='cpu': used=0.0
        else: refuse('PREVIOUS_JOB_GPU_ACCOUNTING_INCOMPLETE')
        paid+=used
    for path in (root/'results/a23/transport').glob('remote-*.json'):
        item=json.loads(path.read_text(encoding='utf-8'))
        paid+=number(item.get('gpu_tail_seconds',0.0))
    remaining=cap-paid
    requested=number(OPTS['timeout_seconds'])
    allowance=min(requested,remaining) if device=='cuda' else min(requested,GPU_CAP)
    row.update(prior_gpu_seconds=paid,remaining_gpu_seconds=max(0.0,remaining),
        controller_allowance_seconds=max(0.0,allowance),stop_reserve_seconds=STOP_RESERVE)
    if allowance<=STOP_RESERVE+3 or time.perf_counter()-origin>=allowance-STOP_RESERVE:
        refuse('GPU_OR_CONTROLLER_BUDGET_REFUSED')
    if (root/'results/a23/jobs'/job).exists() or (root/'runs'/(job+'.stdout')).exists():
        refuse('JOB_ID_ALREADY_RESERVED')
    if pathlib.Path(LOCK).exists(): refuse('SHARED_LOCK_EXISTS')
    queue_clear()
    if pathlib.Path(LOCK).exists(): refuse('SHARED_LOCK_EXISTS')
    if time.perf_counter()-origin>=allowance-STOP_RESERVE:
        refuse('CONTROLLER_BUDGET_EXHAUSTED_BEFORE_LAUNCH')
    environment=os.environ.copy()
    environment.update(PYTHONPATH=str(root/'src'),PYTHONDONTWRITEBYTECODE='1',
        OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',
        A23_JOB_WALL_ORIGIN=str(origin),A23_CONTROLLER_BUDGET_SECONDS=str(allowance))
    (root/'runs').mkdir(parents=True,exist_ok=True)
    arguments=[PYTHON,'-B','-u','-m','a23.cli',OPTS['stage'],'--root',REMOTE,
        '--job',job,'--device',device,'--lock-root',SHARED]
    with (root/'runs'/(job+'.stdout')).open('xb') as output,(root/'runs'/(job+'.stderr')).open('xb') as errors:
        child=subprocess.Popen(arguments,cwd=root,env=environment,stdout=output,stderr=errors)
        row['physics_job_launched']=True
        deadline=origin+allowance-STOP_RESERVE
        while child.poll() is None:
            observe_lock();child_cpu=max(child_cpu,measured_cpu(child))
            if time.perf_counter()>=deadline:
                row['status']='TIMEOUT';stop_child();break
            time.sleep(.2)
        child_cpu=max(child_cpu,measured_cpu(child))
    if row['status']!='TIMEOUT': row['status']='COMPLETE' if child.returncode==0 else 'FAILED'
except BaseException as error:
    row.update(**error_fields(error));stop_child()
finally:
    ended=child is None or child.poll() is not None
    stopped_queue_clear=True
    if child is not None and device=='cuda' and row['status'] in ('TIMEOUT','FAILED','STOP_UNCONFIRMED'):
        try:
            code,out=query(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'])
            stopped_queue_clear=code==0 and not out.strip()
        except BaseException:
            stopped_queue_clear=False
        row['compute_queue_clear_after_stop']=stopped_queue_clear
        if not stopped_queue_clear: row['status']='STOP_UNCONFIRMED'
    if not ended: row['status']='STOP_UNCONFIRMED'
    row.update(child_stop_confirmed=ended,exit_status=child.returncode if child else None,
        child_process_CPU_seconds=child_cpu)
    elapsed=time.perf_counter()-origin
    if child is not None:
        if receipt_path.exists():
            try:
                receipt=json.loads(receipt_path.read_text(encoding='utf-8'))
                billed=number(receipt.get('gpu_occupation_seconds',receipt.get('wall_seconds',0.0))) if device=='cuda' else 0.0
                billed_cpu=number(receipt.get('process_cpu_seconds',0.0))
                row['job_receipt_preserved']=True
            except BaseException:
                row['job_receipt_invalid']=True;receipt=None;billed=0.0;billed_cpu=0.0
        elif ended:
            receipt={'schema':'a23.transport_synthesized_job_receipt.v1','job_id':job,
                'stage':OPTS['stage'],'device':device,'status':row['status'],
                'wall_seconds':elapsed,'gpu_occupation_seconds':elapsed if device=='cuda' else 0.0,
                'process_cpu_seconds':child_cpu,'counts':{'failed_attempts':int(row['status']!='COMPLETE')},
                'child_stop_confirmed':True,'child_CPU_measurement_available':child_cpu_measurement_available,
                'synthesized_by_transport':True,'accounting_scope':'conservative inclusive controller elapsed; all host work included'}
            write_json(receipt_path,receipt)
            billed=receipt['gpu_occupation_seconds'];billed_cpu=child_cpu
            row['job_receipt_synthesized']=True
        else:
            billed=0.0;billed_cpu=0.0
        row['gpu_tail_seconds']=max(0.0,elapsed-billed) if device=='cuda' else 0.0
        row['job_gpu_seconds_already_paid']=billed
        row['child_CPU_tail_seconds']=max(0.0,child_cpu-billed_cpu)
        row['gpu_charge_scope']='inclusive controller wall minus existing job receipt; includes host work'
    else:
        row['child_CPU_tail_seconds']=0.0
    if ended and stopped_queue_clear and owned_lock is not None:
        try:
            lock=pathlib.Path(LOCK)
            if lock.exists() and lock.read_bytes()==owned_lock:
                lock.unlink();row['owned_stale_lock_released']=True
        except OSError:
            row['owned_stale_lock_release_failed']=True
    if receipt is not None:
        row['job_receipt_summary']={key:receipt.get(key) for key in
            ('status','device','wall_seconds','gpu_occupation_seconds','process_cpu_seconds','counts')}
    record(row)
'''


PULL_BODY = r'''
row={'status':'FAILED','gpu_tail_seconds':0.0,'physics_job_launched':False}
try:
    if pathlib.Path(LOCK).exists(): refuse('PULL_REFUSED_WHILE_SHARED_LOCK_EXISTS')
    archive=destination(OPTS['archive']);total=0;count=0
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        paths=list((root/'results/a23').rglob('*'))
        paths+=list((root/'runs').glob('a23-*'))
        for p in sorted(paths):
            if not p.is_file(): continue
            name=p.relative_to(root).as_posix()
            if p.is_symlink() or not safe_name(name): refuse('UNSAFE_RESULT_PATH')
            destination(name)
            if name.startswith('runs/') and not (p.suffix in ('.stdout','.stderr') and re.fullmatch(JOB_PATTERN,p.stem)):
                continue
            if not (name.startswith('results/a23/') or name.startswith('runs/')): refuse('PULL_NAMESPACE_REFUSED')
            total+=p.stat().st_size
            if total>MAX_ZIP_BYTES: refuse('RESULT_ARCHIVE_TOO_LARGE')
            z.write(p,name);count+=1
    row.update(status='COMPLETE',archive=OPTS['archive'],member_count=count,uncompressed_bytes=total)
except BaseException as error:
    row.update(**error_fields(error))
record(row)
'''


def _remote_code(helper, action, attempt, **options):
    bodies = {"preflight": PREFLIGHT_BODY, "deploy": DEPLOY_BODY,
              "run": RUN_BODY, "pull": PULL_BODY}
    return _prelude(helper, dict(action=action, attempt=attempt, **options)) + bodies[action]


def _call(helper, connection, code, *, timeout):
    try:
        row = helper._python(connection, code, timeout=timeout)
    except BaseException as error:
        accounting = getattr(error, "accounting", None)
        failed = TransportError("REMOTE_TRANSPORT_FAILED_PRIVATE_DIAGNOSTICS_SUPPRESSED")
        failed.accounting = accounting if isinstance(accounting, dict) else None
        raise failed from None
    if not isinstance(row, dict):
        raise TransportError("REMOTE_RESPONSE_NOT_A_RECEIPT")
    return row


def deploy(helper, connection, root, scope, attempt):
    names = deployment_members(root, scope)
    archive_name = "a23-deploy-" + attempt + ".zip"
    with tempfile.TemporaryDirectory() as directory:
        archive = Path(directory) / archive_name
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
            for name in names:
                z.write(root / name, name)
        connection.shell("$ErrorActionPreference='Stop'; if(Test-Path '" + SHARED_LOCK
                         + "'){throw 'Shared lock exists'}; New-Item -ItemType Directory -Force '"
                         + REMOTE + "' | Out-Null", timeout=15)
        connection.copy_to(archive, archive_name)
        row = _call(helper, connection, _remote_code(helper, "deploy", attempt,
                    scope=scope, archive=archive_name, members=names), timeout=60)
        row['local_archive_compressed_bytes'] = archive.stat().st_size
        return row


def _same_file(left, right):
    if left.stat().st_size != right.stat().st_size:
        return False
    with left.open('rb') as a, right.open('rb') as b:
        while True:
            x, y = a.read(1024**2), b.read(1024**2)
            if x != y:
                return False
            if not x:
                return True


def _ledger_prefix(existing, incoming):
    with existing.open('rb') as old, incoming.open('rb') as new:
        while True:
            part = old.read(1024**2)
            if not part:
                return True
            if new.read(len(part)) != part:
                return False


def _install_results(root, archive):
    """Stage and validate everything before writing; old arrays are immutable."""
    with tempfile.TemporaryDirectory() as directory:
        staged_root = Path(directory)
        plan, seen, total = [], set(), 0
        with zipfile.ZipFile(archive) as z:
            for member in z.infolist():
                name = member.filename
                valid_log = (name.startswith('runs/') and len(PurePosixPath(name).parts) == 2
                             and Path(name).suffix in ('.stdout', '.stderr')
                             and re.fullmatch(JOB_PATTERN, Path(name).stem))
                if (not _safe_name(name) or name.casefold() in seen
                        or not (name.startswith('results/a23/') or valid_log)
                        or stat.S_ISLNK(member.external_attr >> 16)):
                    raise TransportError("INVALID_RESULT_ARCHIVE_MEMBER")
                seen.add(name.casefold())
                total += member.file_size
                if total > MAX_ZIP_BYTES:
                    raise TransportError("RESULT_ARCHIVE_TOO_LARGE")
                destination = _safe_destination(root, name)
                staged = _safe_destination(staged_root, name)
                staged.parent.mkdir(parents=True, exist_ok=True)
                with z.open(member) as source, staged.open('wb') as output:
                    while True:
                        chunk = source.read(1024**2)
                        if not chunk:
                            break
                        output.write(chunk)
                if not destination.exists():
                    plan.append((destination, staged, 'new'))
                elif _same_file(destination, staged):
                    continue
                elif destination.suffix == '.jsonl' and 'LEDGER' in destination.name.upper():
                    if _ledger_prefix(destination, staged):
                        plan.append((destination, staged, 'append'))
                    elif _ledger_prefix(staged, destination):
                        continue  # Incoming is an older immutable ledger prefix.
                    else:
                        raise TransportError("IMMUTABLE_LEDGER_PREFIX_CONFLICT")
                else:
                    raise TransportError("IMMUTABLE_RESULT_CONFLICT")
        changed = 0
        for destination, staged, mode in plan:
            destination.parent.mkdir(parents=True, exist_ok=True)
            if mode == 'append':
                if not _ledger_prefix(destination, staged):
                    raise TransportError("LEDGER_CHANGED_DURING_PULL")
                with staged.open('rb') as source, destination.open('ab') as output:
                    source.seek(destination.stat().st_size)
                    while True:
                        chunk = source.read(1024**2)
                        if not chunk:
                            break
                        output.write(chunk)
            else:
                if destination.exists():
                    if _same_file(destination, staged):
                        continue
                    raise TransportError("RESULT_CHANGED_DURING_PULL")
                temporary = None
                try:
                    with tempfile.NamedTemporaryFile('wb', dir=destination.parent, delete=False) as output:
                        temporary = Path(output.name)
                        with staged.open('rb') as source:
                            while True:
                                chunk = source.read(1024**2)
                                if not chunk:
                                    break
                                output.write(chunk)
                    os.link(temporary, destination)  # Atomic new file; refuses replacement.
                finally:
                    if temporary is not None:
                        temporary.unlink(missing_ok=True)
            changed += 1
    return changed


def pull(helper, connection, root, attempt):
    name = 'a23-pull-' + attempt + '.zip'
    row = _call(helper, connection, _remote_code(helper, 'pull', attempt,
                archive=name), timeout=120)
    if row.get('status') != 'COMPLETE':
        return row
    with tempfile.TemporaryDirectory() as directory:
        archive = Path(directory) / name
        connection.copy_from(name, archive)
        row['local_files_written'] = _install_results(root, archive)
    # This exact transport-owned archive is the only removed remote file.
    connection.shell("Remove-Item -LiteralPath '" + REMOTE + '/' + name + "'", timeout=15)
    return row


def _local_receipt(root, attempt, action, row, cpu, wall):
    directory = root / 'results/a23/transport'
    directory.mkdir(parents=True, exist_ok=True)
    value = dict(schema='a23.local_transport.v1', transport_attempt=attempt, action=action,
                 status=row.get('status', 'FAILED'), local_process_cpu_seconds=cpu,
                 local_wall_seconds=wall, remote=row, connection_values_stored=False,
                 physics_launch_authority='parent only; run action explicitly required')
    path = directory / ('local-' + attempt + '.json')
    with path.open('x', encoding='utf-8') as output:
        json.dump(value, output, sort_keys=True, indent=2, allow_nan=False)
        output.write('\n')
    with (directory / 'LOCAL_TRANSPORT_LEDGER.jsonl').open('a', encoding='utf-8') as output:
        output.write(json.dumps(value, sort_keys=True, allow_nan=False) + '\n')
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('preflight', 'deploy', 'run', 'pull'))
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--transport-helper', help='Trusted existing helper; also A23_TRANSPORT_HELPER')
    parser.add_argument('--private-config', required=True, help='External or ignored private/ config; never uploaded')
    parser.add_argument('--scope', choices=('online', 'offline-evaluation'), default='online')
    parser.add_argument('--stage', choices=STAGES, default='micro')
    parser.add_argument('--job', default=None)
    parser.add_argument('--device', choices=('cpu', 'cuda'), default='cuda')
    parser.add_argument('--timeout-seconds', type=float, default=GPU_CAP)
    args = parser.parse_args(argv)
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        parser.error('A23 root does not exist')
    if (not math.isfinite(args.timeout_seconds) or not 0 < args.timeout_seconds <= GPU_CAP):
        parser.error('timeout must be positive and at most 7200 seconds')
    if args.action == 'run' and args.job is None:
        parser.error('--job is required for run')
    attempt = uuid.uuid4().hex
    started_wall, started_cpu = time.perf_counter(), time.process_time()
    row = {'status': 'FAILED', 'physics_job_launched': False}
    launch_outcome_uncertain = False
    try:
        helper = _load_helper(root, args.transport_helper)
        connection = _connection(helper, args.private_config, root)
        if args.action == 'preflight':
            row = _call(helper, connection, _remote_code(helper, 'preflight', attempt), timeout=35)
        elif args.action == 'deploy':
            row = deploy(helper, connection, root, args.scope, attempt)
        elif args.action == 'run':
            _job(args.job)
            launch_outcome_uncertain = True
            row = _call(helper, connection, _remote_code(helper, 'run', attempt,
                        stage=args.stage, job=_job(args.job), device=args.device,
                        timeout_seconds=args.timeout_seconds), timeout=min(GPU_CAP, args.timeout_seconds) + 30)
        else:
            row = pull(helper, connection, root, attempt)
    except BaseException as error:
        row = dict(status='FAILED', error_type=type(error).__name__,
                   error_code=error.code if isinstance(error, TransportError) else 'PRIVATE_DIAGNOSTICS_SUPPRESSED',
                   physics_job_launched=None if launch_outcome_uncertain else False,
                   launch_outcome_uncertain=launch_outcome_uncertain)
        accounting = getattr(error, 'accounting', None)
        if isinstance(accounting, dict):
            row['remote_accounting'] = accounting
    receipt = _local_receipt(root, attempt, args.action, row,
                             time.process_time() - started_cpu, time.perf_counter() - started_wall)
    # Child logs are saved separately. Never print command/private inputs or traceback text.
    print(json.dumps(dict(status=receipt['status'], action=args.action,
                          transport_attempt=attempt, detail=row), sort_keys=True, allow_nan=False))
    return 0 if receipt['status'] == 'COMPLETE' else 1


if __name__ == '__main__':
    raise SystemExit(main())
