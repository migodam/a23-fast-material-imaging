"""Reproduce the preregistered pilot summaries from saved evidence only.

No Maxwell, labels, rank selection, optimization or training runs here.
Scientific thresholds live in the pre-output frozen configuration.
"""
from __future__ import annotations
import ast,csv,json,math
from pathlib import Path
from statistics import mean,median
from .pilot import save_csv
from a20.costs import write_json

LINEAR=('homogeneous_born','born_BP','dressed_linear_chi','linear_a_exact_conversion','generic_randomized_linear')
FEEDBACK=('vanilla_IBS2','A23_compressed_feedback')
PRIMARY=('dressed_linear_chi',)+FEEDBACK
FAMILIES={2001:'gaussian',2003:'gaussian',2014:'asymmetric',2009:'shell'}

def number(value):
    try:v=float(value)
    except (TypeError,ValueError):return None
    return v if math.isfinite(v) else None

def structure(value,default=None):
    if isinstance(value,(dict,list)):return value
    if not value:return default
    try:return json.loads(value)
    except (ValueError,TypeError):
        try:return ast.literal_eval(value)
        except (ValueError,SyntaxError):return default

def rows(path):
    if not path.exists():return []
    with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))

def med(values):
    good=[v for v in values if v is not None]
    return median(good) if good else None

def h1_decision(summary,config):
    by={(int(r['scene']),r['method']):r for r in summary};decisions=[]
    for sid in config['scenes']:
        baseline=by.get((sid,'original_opm'))
        for method in dict.fromkeys(r['method'] for r in summary):
            r=by.get((sid,method))
            if not r or not baseline:continue
            cold=number(r.get('full_cold_encoder_seconds'))
            base=number(baseline.get('full_cold_encoder_seconds'))
            error=number(r.get('transfer_error'));derr=number(r.get('decoder_weighted_error'))
            bderr=number(baseline.get('decoder_weighted_error'))
            reduction=1-cold/base if cold is not None and base else None
            quality=(error is not None and error<=config['gates']['H1_transfer_error_max'])
            cost=quality and reduction is not None and reduction>=config['gates']['H1_encoder_time_reduction_min']
            # The alternative is a strict same-budget comparison, excluding only
            # floating point identity noise, not a new scientific effect threshold.
            alternative=(cold is not None and base is not None and cold<=base and
                         derr is not None and bderr is not None and bderr-derr>1e-9)
            decisions.append(dict(scene=sid,method=method,transfer_error=error,
                decoder_weighted_error=derr,complete_cold_encoder_seconds=cold,
                reduction_vs_original=reduction,quality_5pct=quality,
                time_gate=bool(cost),same_budget_decoder_improvement=bool(alternative)))
    complete=len(summary)==8*len(config['scenes'])
    passed=any(r['time_gate'] or r['same_budget_decoder_improvement'] for r in decisions)
    return {'status':'PASS' if passed else 'FAIL' if complete else 'HOLD',
            'scope':'four historical feasibility scenes; exact cache identities separate from cost gate',
            'complete':complete,'rows':decisions}

def h2_comparison(image_rows,config):
    comparisons=[];outcomes={}
    for sid in config['scenes']:
        for t in config['amplitudes']:
            for noise in config['noise']:
                selected={r['method']:r for r in image_rows if int(r['scene'])==sid and
                          number(r['t'])==t and r['noise']==noise}
                raw=[r for m,r in selected.items() if m in LINEAR and number(r.get('full_chi_NRMSE')) is not None]
                legal=[r for r in raw if r.get('status')=='OK']
                # Preserve the strongest raw baseline even when it is rejected;
                # removing a low-error invalid baseline must not manufacture gain.
                best=min(raw,key=lambda r:(float(r['full_chi_NRMSE']),r['method'])) if raw else None
                bestlegal=min(legal,key=lambda r:(float(r['full_chi_NRMSE']),r['method'])) if legal else None
                for method in FEEDBACK:
                    candidate=selected.get(method);value=number(candidate.get('full_chi_NRMSE')) if candidate else None
                    base=number(best.get('full_chi_NRMSE')) if best else None
                    improvement=1-value/base if value is not None and base else None
                    comparisons.append(dict(scene=sid,family=FAMILIES[sid],t=t,noise=noise,
                        method=method,status=candidate.get('status') if candidate else 'NOT_RUN',
                        full_chi_NRMSE=value,best_matched_linear=best['method'] if best else None,
                        best_linear_NRMSE=base,best_linear_status=best.get('status') if best else None,
                        best_legal_linear=bestlegal['method'] if bestlegal else None,
                        improvement_vs_strongest_raw_linear=improvement,
                        primary=(t==1.),
                        qualifies=(t==1. and candidate is not None and candidate.get('status')=='OK' and
                                   improvement is not None and improvement>=config['gates']['H2_full_material_improvement_min'])))
    for method in FEEDBACK:
        primary=[r for r in comparisons if r['method']==method and r['primary']]
        successful=[]
        for sid in config['scenes']:
            case=[r for r in primary if r['scene']==sid]
            if len(case)==2 and all(r['qualifies'] for r in case):successful.append(sid)
        families=sorted(set(FAMILIES[s] for s in successful))
        complete=len(primary)==8 and all(r['status']!='NOT_RUN' for r in primary)
        outcomes[method]=dict(status='PASS' if len(families)>=config['gates']['H2_distinct_shapes_min'] else 'FAIL' if complete else 'HOLD',
                             qualifying_scenes=successful,qualifying_families=families,
                             primary_rows=primary,complete=complete)
    return comparisons,outcomes

def prepare_pareto(image_rows,preparation,h1summary,config):
    prep={int(r['scene']):r for r in preparation};h1={(int(r['scene']),r['method']):r for r in h1summary};out=[]
    for r in image_rows:
        sid=int(r['scene']);p=prep.get(sid,{});method=r['method'];common=number(p.get('common_reference_geometry_seconds'))
        setup=None
        if common is not None:
            audit=number(p.get('historical_transfer_cache_audit_seconds')) or 0.
            if method in ('homogeneous_born','born_BP'):
                extra=number(p.get('born_transfer_and_decoder_seconds'))
            elif method=='generic_randomized_linear':
                h=h1.get((sid,'randomized_transfer'),{})
                extra=number(h.get('cold_encoder_with_independent_construction_seconds'))
                if extra is not None:extra+=(number(p.get('random_decoder_seconds')) or 0.)+audit
            elif method=='current_BP_ratio':extra=0.
            else:
                extra=number(p.get('direct_transfer_and_decoder_seconds'))
                if extra is not None:extra+=audit
            if extra is not None:setup=common+extra
            if method=='A23_compressed_feedback' and setup is not None:
                setup+=(number(p.get('quadratic_compression_including_holdout_audit_seconds')) or 0.)
                setup+=(number(p.get('quadratic_cache_export_seconds')) or 0.)
        decode=number(r.get('cold_decode_seconds'));validation=number(r.get('full_validation_seconds'))
        encode=number(r.get('online_pack_encode_seconds')) or 0.
        imageio=number(r.get('shared_observation_image_export_seconds')) or 0.
        nonvalidation=setup+decode+encode+imageio if setup is not None and decode is not None else None
        complete=r.get('status')=='OK' and r.get('full_validation')=='RUN'
        total=nonvalidation+validation if complete and nonvalidation is not None and validation is not None else None
        err=number(r.get('full_chi_NRMSE'));res=number(r.get('datafullresidual'))
        quality=(complete and err is not None and res is not None and
                 err<=config['gates']['H3_full_material_NRMSE_max'] and
                 res<=config['gates']['H3_difference_data_residual_max'])
        out.append(dict(scene=sid,shape=r.get('shape',FAMILIES[sid]),method=method,t=number(r['t']),noise=r['noise'],
            status=r.get('status'),full_validation=r.get('full_validation'),full_chi_NRMSE=err,datafullresidual=res,
            setup_seconds=setup,cold_decode_seconds=decode,warm_decode_median_seconds=number(r.get('warm_decode_seconds')),
            pack_encode_seconds=encode,conservative_image_export_seconds=imageio,
            full_validation_seconds=validation,eligible_quality=bool(quality),
            total_time_to_image_seconds=total,cached_pipeline_without_fullvalidation_seconds=nonvalidation,
            total_time_N10_extrapolated=setup+10*(decode+encode+imageio+validation) if total is not None else None,
            total_time_N100_extrapolated=setup+100*(decode+encode+imageio+validation) if total is not None else None,
            timing_scope='measured individual components plus independent setup attribution; one full validation',
            warm_full_pipeline='NOT_RUN; warm5 encode/decode only, single full validation',
            N10_N100='FORMULA_ONLY_NOT_MEASURED',metadata_and_publication_cost='budget ledger only',
            attribution='each method pays its independent setup; actual shared budget is charged once'))
    return out

def h3_decision(pareto,config):
    primary=[r for r in pareto if r['method'] in PRIMARY and r['t']==1 and r['noise']==config['noise'][1]]
    table=[]
    for sid in config['scenes']:
        d={r['method']:r for r in primary if r['scene']==sid}
        baseline=d.get('dressed_linear_chi');candidate=d.get('A23_compressed_feedback')
        if not candidate or not baseline:
            table.append(dict(scene=sid,status='NOT_RUN',qualifies=False));continue
        ct=candidate['total_time_to_image_seconds'];bt=baseline['total_time_to_image_seconds']
        reduction=1-ct/bt if ct is not None and bt else None
        same_quality=(candidate['eligible_quality'] and baseline['eligible_quality'])
        same_budget=(same_quality and ct is not None and bt is not None and ct<=bt and
                     candidate['full_chi_NRMSE']<baseline['full_chi_NRMSE'] and
                     candidate['datafullresidual']<=baseline['datafullresidual'])
        improvement=(same_quality and reduction is not None and reduction>=config['gates']['H3_time_reduction_min'])
        table.append(dict(scene=sid,status='EVALUATED',candidate_eligible=candidate['eligible_quality'],
            baseline_eligible=baseline['eligible_quality'],candidate_complete_seconds=ct,baseline_complete_seconds=bt,
            time_reduction=reduction,non_dominated_same_budget=bool(same_budget),qualifies=bool(improvement or same_budget)))
    complete=len(primary)==12 and all(r['status']!='NOT_RUN' for r in table)
    return dict(status='PASS' if table and all(r['qualifies'] for r in table) else 'FAIL' if complete else 'HOLD',
                primary='all four fixed noisy nominal cases, matched quality and complete measured components',
                rows=table,complete=complete,formal_generalization='NOT_ESTABLISHED')

def report(root):
    root=Path(root);dest=root/'results/a23'
    config=json.loads((root/'FROZEN_CONFIG.json').read_text())
    from .h1_report import summarize_h1
    h1summary=summarize_h1(root)['summary_rows']
    image=rows(dest/'FULL_IMAGE_METRICS.csv')
    prep=json.loads((dest/'PIPELINE_PREPARATION_RAW.json').read_text()) if (dest/'PIPELINE_PREPARATION_RAW.json').exists() else []
    comparisons,h2=h2_comparison(image,config)
    save_csv(dest/'H2_COMPARISON.csv',comparisons)
    pareto=prepare_pareto(image,prep,h1summary,config);save_csv(dest/'PARETO_TABLE.csv',pareto)
    methodrows=[]
    for method in dict.fromkeys(r['method'] for r in image):
        for t in config['amplitudes']:
            for noise in config['noise']:
                rr=[r for r in image if r['method']==method and number(r['t'])==t and r['noise']==noise]
                methodrows.append(dict(method=method,t=t,noise=noise,count=len(rr),physically_legal=sum(r.get('status')=='OK' for r in rr),
                    median_full_chi_NRMSE=med([number(r.get('full_chi_NRMSE')) for r in rr]),
                    median_delta_chi_NRMSE=med([number(r.get('delta_chi_NRMSE')) for r in rr]),
                    median_surrogate_residual=med([number(r.get('surrogateresidual')) for r in rr]),
                    count_semantics='all attempted methods, rejected raw errors included; not an eligible-only average'))
    save_csv(dest/'METHOD_SUMMARY.csv',methodrows)
    gate=dict(study='A23_PILOT_1',frozen_config='FROZEN_CONFIG.json',
        H1=h1_decision(h1summary,config),H2=h2['A23_compressed_feedback'],
        vanilla_IBS2_mechanism_control=h2['vanilla_IBS2'],H3=h3_decision(pareto,config),
        dataset={'scenes':config['scenes'],'historically_exposed':True,'independent_scenes':4,
                 'new_labels_cap':12,'observations_primary':24,'observations_calibration':4},
        NN='NOT_RUN_FORBIDDEN',degree_expansion='NOT_RUN_FORBIDDEN',new_scene_campaign='NOT_RUN',
        nonlinear_reconstruction='NOT_RUN',medical_claims='NOT_ESTABLISHED',
        same_model_full_validation='does not establish independent model validation',
        chart='full3456 real mass coordinates, old32 evaluator diagnostic only',
        priors='same physical local pullback; nonlinear alpha global prior not claimed equivalent',
        raw_rejected_outputs='published, ineligible for quality/time gates',new_SHA256_checks=0)
    gate['decision']='STOP_NO_EXPANSION' if gate['H2']['status']!='PASS' or gate['H3']['status']!='PASS' else 'PILOT_HEADROOM_ONLY_NO_AUTOMATIC_EXPANSION'
    write_json(root/'A23_GATE_DECISION.json',gate);write_json(dest/'A23_GATE_DECISION.json',gate)
    from .accounting_report import summarize_cost
    costs=summarize_cost(root)
    from .plots import make_plots
    figures=make_plots(root)
    return {'gate':gate,'cost':costs,'figures':figures,'image_rows':len(image)}
