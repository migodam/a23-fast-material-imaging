"""Bounded phase entrypoints with one shared queue and paid failure receipts."""
from __future__ import annotations
import argparse,json,os,platform,subprocess,time,traceback,sys
from pathlib import Path
from a20.costs import CostBook,write_json,job_lock,BudgetExceeded,plain

def prior_cost(root):
    rows=[]
    for p in (root/'results/a23/jobs').glob('*/job_receipt.json'):
        rows.append(json.loads(p.read_text()))
    for folder in (root/'results/a23/jobs').glob('*'):
        if (folder/'job_manifest.json').exists() and not (folder/'job_receipt.json').exists():
            raise BudgetExceeded('ORPHAN_JOB_COST_UNRESOLVED_STOP_BEFORE_NEW_PHYSICS')
    return sum(r.get('process_cpu_seconds',0.) for r in rows),sum(r.get('gpu_occupation_seconds',0.) for r in rows)

def prior_counts(root):
    from collections import Counter
    total=Counter()
    for folder in (root/'results/a23/jobs').glob('*'):
        receipt=folder/'job_receipt.json';paid=Counter();logged=Counter()
        if receipt.exists(): paid.update(json.loads(receipt.read_text()).get('counts',{}))
        if (folder/'ACTION_LEDGER.jsonl').exists():
            for line in (folder/'ACTION_LEDGER.jsonl').read_text().splitlines():
                if line.strip():logged.update(json.loads(line).get('counters',{}))
        total.update({key:max(paid[key],logged[key]) for key in paid.keys()|logged.keys()})
    return dict(total)

def run_unit(root,book):
    import unittest
    with book.span('mathematical_and_actual_tiny_backend_unit_tests'):
        suite=unittest.defaultTestLoader.discover(str(root/'tests'),pattern='test_a23*.py')
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        row={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
             'skips':len(result.skipped),'status':'PASS' if result.wasSuccessful() else 'FAIL',
             'scope':'unit+tiny real frozen backend, not full-image evidence'}
        write_json(root/'results/a23/PHASE0_TESTS.json',row)
        if not result.wasSuccessful():raise ValueError('PHASE0_IMPLEMENTATION_TEST_FAILED')
    return row

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('stage',choices=('micro','phase0','h1','pilot','report'))
    p.add_argument('--root',default=str(Path(__file__).resolve().parents[2]))
    p.add_argument('--job',required=True);p.add_argument('--device',default='cpu',choices=('cpu','cuda'))
    p.add_argument('--lock-root');a=p.parse_args(argv)
    root=Path(a.root).resolve();sys.path.insert(0,str(root));dest=root/'results/a23';dest.mkdir(parents=True,exist_ok=True)
    if not a.job.replace('-','').replace('_','').isalnum():raise ValueError('INVALID_JOB_ID')
    jobdir=dest/'jobs'/a.job
    if jobdir.exists():raise ValueError('JOB_ALREADY_EXISTS_NEVER_REPLACE')
    config=json.loads((root/'FROZEN_CONFIG.json').read_text())
    cpu,gpu=prior_cost(root)
    config['_prior_counts']=prior_counts(root)
    jobdir.mkdir(parents=True)
    book=CostBook(jobdir/'ACTION_LEDGER.jsonl',device=a.device,prior_cpu=cpu,prior_gpu=gpu,
       cpu_limit=config['cpu_wall_soft_target_seconds'],gpu_limit=config['gpu_occupation_cap_seconds'],
       cpu_reserve=60.,gpu_reserve=60.,metadata={'job':a.job,'stage':a.stage},enforce=True)
    write_json(jobdir/'job_manifest.json',{'stage':a.stage,'job':a.job,'device':a.device,
       'precision':'complex128/float64','platform':platform.platform(),'python':platform.python_version(),
       'frozen_config':config,'source_snapshot':json.loads((root/'RUN_SOURCE_SNAPSHOT.json').read_text()) if (root/'RUN_SOURCE_SNAPSHOT.json').exists() else {'status':'EARLY_SOURCE_SNAPSHOT_RECORDED_IN_LOCAL_DEPLOY_AUDIT'},'prior_cost':{'cpu':cpu,'gpu':gpu},'new_SHA256_checks':0})
    outcome='FAILED';error=None
    try:
        # Actual queue is checked by controller; lock protects race between jobs.
        with job_lock(Path(a.lock_root) if a.lock_root else root):
            if a.stage=='phase0':run_unit(root,book)
            elif a.stage=='micro':
                from .pilot import make_ref,reference_checks
                start=time.perf_counter();ref=make_ref(root,config['scenes'][0],book,a.device,config)
                reference_seconds=time.perf_counter()-start
                from .encoder import TikhonovDecoder
                start=time.perf_counter();A=ref.matrix();matrix_seconds=time.perf_counter()-start
                start=time.perf_counter();d=TikhonovDecoder(A,device=a.device,book=book,relative=config['tikhonov_relative'])
                decoder_seconds=time.perf_counter()-start
                checks=reference_checks(ref,config)
                # Conservative frozen entire matrix forecast, no outcome-based selection.
                estimated_remaining=4*(6*matrix_seconds+20*decoder_seconds+5*reference_seconds+120.)
                row={'status':'PASS','reference_seconds':reference_seconds,'matrix_seconds':matrix_seconds,
                     'decoder_seconds':decoder_seconds,'estimated_remaining_gpu_seconds':estimated_remaining,
                     'forecast':'conservative workload forecast, not measured experiment total','checks':checks}
                if gpu+book.receipt()['gpu_occupation_seconds']+estimated_remaining>config['gpu_occupation_cap_seconds']-60:
                    row['status']='BUDGET_BLOCKED'
                write_json(dest/'MICROBENCHMARK.json',row)
                if row['status']!='PASS':raise BudgetExceeded('MICROBENCHMARK_REMAINING_MATRIX_BUDGET_BLOCKED')
            elif a.stage=='h1':
                if json.loads((dest/'PHASE0_TESTS.json').read_text())['status']!='PASS':raise ValueError('PHASE0_GATE_CLOSED')
                if json.loads((dest/'MICROBENCHMARK.json').read_text())['status']!='PASS':raise ValueError('MICRO_BUDGET_GATE_CLOSED')
                from .pilot import h1_stage
                h1_stage(root,book,a.device,config)
            elif a.stage=='pilot':
                import csv
                if not (dest/'H1_ENCODER_METRICS.csv').exists():raise ValueError('H1_NOT_COMPLETED')
                rows=list(csv.DictReader((dest/'H1_ENCODER_METRICS.csv').open()))
                if set(int(r['scene']) for r in rows)!=set(config['scenes']):raise ValueError('H1_INCOMPLETE_NO_EXPANSION')
                if (dest/'FULL_IMAGE_METRICS.csv').exists():raise ValueError('EXISTING_PILOT_RESULTS_RETAINED_NO_AUTOMATIC_OVERWRITE_OR_EXPANSION')
                from .pilot import pilot_stage
                pilot_stage(root,book,a.device,config)
            else:
                from .report import report
                report(root)
            outcome='COMPLETE'
    except BaseException as e:
        error={'type':type(e).__name__,'reason':str(e)}
        with (dest/'FAILURE_LEDGER.jsonl').open('a',encoding='utf-8') as f:
            f.write(json.dumps(dict(job=a.job,stage=a.stage,error=error,charged=True))+'\n')
        traceback.print_exc()
    finally:
        receipt=book.receipt();receipt.update(status=outcome,job=a.job,stage=a.stage,error=error)
        write_json(jobdir/'job_receipt.json',receipt)
        write_json(dest/'LATEST_JOB.json',{'job':a.job,'status':outcome,'stage':a.stage})
        print(json.dumps({'job':a.job,'status':outcome,'gpu_seconds':receipt['gpu_occupation_seconds'],
                         'cpu_seconds':receipt['process_cpu_seconds'],'error':error}),flush=True)
    return 0 if outcome=='COMPLETE' else 1

if __name__=='__main__':raise SystemExit(main())
