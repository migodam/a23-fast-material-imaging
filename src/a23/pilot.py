"""Small fixed experimental matrix. Offline labels never choose a method."""
from __future__ import annotations
import csv,json,time
from pathlib import Path
import numpy as np
from scipy import linalg as la
from a20.backend import pack,kernel
from a20.costs import write_json,plain
from .physics import ReferencePhysics,load_online,gaussian_noise
from .encoder import TikhonovDecoder,quadratic_sketch

def save_csv(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(plain(rows))

def append_failure(root,event,**kw):
    path=Path(root)/'results/a23/FAILURE_LEDGER.jsonl'
    with path.open('a',encoding='utf-8') as f:f.write(json.dumps(plain(dict(event=event,**kw)),allow_nan=False)+'\n')

def make_ref(root,sid,book,device,config):
    return ReferencePhysics(load_online(Path(root)/f'data/online/scene_{sid}.npz'),book=book,device=device,config=config)

def reference_checks(ref,config):
    rng=np.random.default_rng(np.random.SeedSequence([config['master_seed'],ref.adapter.problem.parent_id,33]))
    d=rng.normal(size=(ref.p,2));d/=la.norm(d,axis=0)
    w=rng.normal(size=(len(ref.data0),2))
    A=ref.matrix()
    direct=ref.adapter.full_tangent_action(ref.chi0,ref.state,d)
    terr=la.norm(A@d-direct)/max(la.norm(direct),1e-30)
    pull=ref.adapter.full_adjoint_action(ref.chi0,ref.state,w)
    adj=abs(float(np.sum((A@d)*w)-np.sum(d*pull)))/max(abs(float(np.sum((A@d)*w))),1e-30)
    q=ref.quadratic(d[:,0],d[:,1],components=True)
    swapped=ref.quadratic(d[:,1],d[:,0])
    sym=la.norm(q['total']-swapped)/max(la.norm(q['total']),1e-30)
    row={'source_residual':ref.state.source_residual(),'streamed_vs_paid_tangent':float(terr),
         'real_adjoint_dot_error':float(adj),'quadratic_symmetry_error':float(sym),
         'source_count':ref.P,'material_dimension':ref.p,'real_data_dimension':len(ref.data0)}
    if max(terr,adj,sym)>config['identity_rtol']:raise ValueError('REAL_BACKEND_IDENTITY_FAILURE')
    return row

def h1_stage(root,book,device,config):
    from .h1 import build_h1
    dest=Path(root)/'results/a23';rows=[]
    for sid in config['scenes']:
        started=time.perf_counter();ref=make_ref(root,sid,book,device,config)
        common=time.perf_counter()-started
        direct_times=[];direct_costs=[]
        for repeat in range(1+config['warm_repeats']):
            before=book.snapshot();t=time.perf_counter();ref.matrix(force=True);book.synchronize()
            direct_times.append(time.perf_counter()-t);direct_costs.append(book.delta(before))
        decoder=TikhonovDecoder(ref.matrix(),relative=config['tikhonov_relative'],device=device,book=book)
        ref.evaluation_decoder=decoder
        checks=reference_checks(ref,config)
        write_json(dest/f'BACKEND_IDENTITY_{sid}.json',checks)
        direct={'cold_seconds':direct_times[0],'warm_seconds':direct_times[1:],
                'cold_counts':direct_costs[0]['counts'],'warm_counts':[d['counts'] for d in direct_costs[1:]],
                'common_reference_geometry_seconds':common,'decoder_prepare_seconds':decoder.prepare_seconds}
        arms,matrices=build_h1(ref,config,dest/f'h1/scene_{sid}',direct_preparation=direct)
        cache=dest/f'cache/scene_{sid}';cache.mkdir(parents=True,exist_ok=True)
        # Reference-only transfer, not truth J. Shared reusable frozen assets.
        np.savez_compressed(cache/'transfer.npz',A=ref.matrix(),D=decoder.D,
            lam=decoder.lam,U=decoder.data_U,s=decoder.singular_values,Z=ref.prepare_adjoint(),
            **{k+'_A':v for k,v in matrices.items()})
        for r in arms:r.update(scene=sid,common_reference_geometry_seconds=common,
                               decoder_prepare_seconds=decoder.prepare_seconds)
        rows.extend(arms);save_csv(dest/'H1_ENCODER_METRICS.csv',rows)
        print(json.dumps({'stage':'h1','scene':sid,'complete_arms':len(arms)}),flush=True)
    return rows

def local_born_matrix(ref):
    n=ref.N;m=ref.adapter.m
    GS=ref.adapter.model.GS.reshape(m,n,3)
    a0,da0=kernel.polarizability(np.zeros(n,complex),ref.v,ref.k)
    out=[]
    for s in range(ref.P):
        C=np.einsum('qic,ic->qi',GS,ref.adapter.model.incident[s].reshape(n,3))*da0[None,:]/ref.v
        raw=np.concatenate((C,1j*C),axis=1)
        out.append(np.concatenate((raw.real,raw.imag),axis=0)/ref.scale)
    return np.concatenate(out,axis=0)

def current_ratio(ref,z):
    """Source-wise measured-current BP plus analytic material ratio."""
    from a20.backend import unpack
    diff=unpack(z*ref.scale,ref.P,ref.adapter.m)
    current=[]
    for s in range(ref.P):
        bp=ref.apply_S_adjoint(diff[s]);re=ref.apply_S(bp)
        denom=float(np.vdot(re,re).real)
        factor=float(np.vdot(bp,bp).real)/denom if denom>0 else 0.
        current.append(ref.state.current[s]+factor*bp)
    current=np.asarray(current)
    exciting=ref.adapter.model.incident+np.sqrt(ref.v)*ref.apply_G(current.T).T
    fields=exciting.reshape(ref.P,ref.N,3);p=np.sqrt(ref.v)*current.reshape(ref.P,ref.N,3)
    num=np.einsum('sic,sic->i',fields.conj(),p);den=np.sum(abs(fields)**2,axis=(0,2))
    if np.any(den<=1e-20):raise ValueError('ZERO_MATERIAL_RATIO_EXCITATION')
    return ref.polarization_to_chi(num/den)

def candidate_from_measurement(ref,decoder,bornA,bornD,randomD,Uy,z,method,config):
    if method=='homogeneous_born':x=bornD.decode(z)
    elif method=='born_BP':x=bornA.T@z/(bornD.singular_values[0]**2)
    elif method=='dressed_linear_chi':x=decoder.decode(z)
    elif method=='linear_a_exact_conversion':return ref.polarization_to_chi(ref.prior_coordinate_to_alpha(decoder.decode(z)))
    elif method in ('vanilla_IBS2','A23_compressed_feedback'):
        first=decoder.decode(z)
        q=ref.quadratic(first,outer='primal' if method=='vanilla_IBS2' else 'adjoint')
        if method=='A23_compressed_feedback':q=Uy@(Uy.T@q)
        x=first-config['feedback_gamma']*decoder.decode(q)
    elif method=='generic_randomized_linear':x=randomD.decode(z)
    elif method=='current_BP_ratio':return current_ratio(ref,z)
    else:raise ValueError('UNREGISTERED_IMAGING_METHOD')
    return ref.chi0+ref.adapter.chart.expand(x)

def image_metrics(ref,estimate,truth,nominal,*,method,scene,t,noise,status):
    truth=np.asarray(truth);estimate=np.asarray(estimate)
    delta=truth-ref.chi0;err=estimate-truth
    norm=lambda a:float(np.sqrt(ref.v)*la.norm(a))
    realden=norm(truth.real);imagden=norm(truth.imag)
    contrast_threshold=.2*float(np.max(abs(nominal-ref.chi0)))
    support=abs(delta)>=contrast_threshold
    predicted=abs(estimate-ref.chi0)>=contrast_threshold
    union=np.count_nonzero(support|predicted)
    point=ref.adapter.problem.points
    region=np.max(abs(point-point.mean(axis=0)),axis=1)<=.2
    edge=int(round(ref.N**(1/3)))
    order=np.lexsort((point[:,2],point[:,1],point[:,0]))
    ee=err[order].reshape((edge,)*3);tt=truth[order].reshape((edge,)*3)
    edge_error=float(np.sqrt(sum(la.norm(np.diff(ee,axis=j))**2 for j in range(3))))
    edge_truth=float(np.sqrt(sum(la.norm(np.diff(tt,axis=j))**2 for j in range(3))))
    return {'scene':scene,'shape':{2001:'gaussian_moderate',2003:'gaussian_stronger',2014:'asymmetric_piecewise',2009:'nested_shell'}[scene],
        'historically_exposed':True,'t':t,'noise':noise,'method':method,'status':status,
        'full_chi_NRMSE':norm(err)/norm(truth),'delta_chi_NRMSE':norm(err)/norm(delta),
        'real_NRMSE':norm(err.real)/realden,'imag_NRMSE':norm(err.imag)/imagden,
        'absolute_mass_error':norm(err),'edge_relative_error':edge_error/max(edge_truth,1e-30),'support_IoU':np.count_nonzero(support&predicted)/union if union else None,
        'small_geometric_region_error':norm(err[region])/max(norm(truth[region]),1e-30),
        'physical_violation':max(0.,-.5-float(estimate.real.min()),-float(estimate.imag.min())),
        'datafullresidual':None,'full_validation':'NOT_RUN','fallback_count':0}

def curvature_row(ref,x,clean,decoder,config,scene,t):
    q=ref.quadratic(x,components=True);linear=ref.matrix()@x
    finite=clean-ref.data0-linear
    sv=decoder.singular_values;U=decoder.data_U
    numerical_tol=np.finfo(float).eps*max(ref.matrix().shape)*sv[0]
    full=U[:,sv>numerical_tol];stable=U[:,sv>=np.sqrt(decoder.lam)]
    def leftover(vec,basis):return float(la.norm(vec-basis@(basis.T@vec)))
    # Fixed old32 chart is evaluator-only, not runtime feature.
    from .offline import old_chart_basis
    W=old_chart_basis(ref.adapter.problem.points,ref.v)
    chart,_=la.qr(ref.matrix()@W,mode='economic')
    # Physical source/receiver gain nuisance tangent, deterministic known ref.
    base=ref.state.field
    nuisance=[]
    for s in range(ref.P):
        tmp=np.zeros_like(base);tmp[s]=base[s];nuisance.append(ref.adapter.whiten(pack(tmp)))
    for j in range(ref.adapter.m):
        tmp=np.zeros_like(base);tmp[:,j]=base[:,j];nuisance.append(ref.adapter.whiten(pack(tmp)))
    un,sn,_=la.svd(np.column_stack(nuisance),full_matrices=False)
    un=un[:,sn>1e-10*sn[0]]
    row={'scene':scene,'t':t,'scope':'OFFLINE_TRUTH_DIRECTION_MECHANISM_ONLY',
         'linear_norm':float(la.norm(linear)),'finite_remainder_norm':float(la.norm(finite)),
         'full_Q_norm':float(la.norm(q['total'])),'feedback_Q_norm':float(la.norm(q['feedback'])),
         'local_a_second_norm':float(la.norm(q['local'])),
         'quadratic_remainder_norm':float(la.norm(finite-q['total'])),
         'full_tangent_numeric_rank':full.shape[1],'data_dimension':len(ref.data0),
         'full_tangent_threshold':float(numerical_tol),'stable_tangent_rank':stable.shape[1],
         'old_chart_rank':chart.shape[1],'nuisance_rank':un.shape[1],
         'rigorous_feedback_norm_bound':'NOT_COMPUTED','empirical_only':True}
    for name,basis in [('full_tangent',full),('stable_tangent',stable),('old32_chart',chart),('calibration_nuisance',un)]:
        for component,vec in q.items():row[component+'_outside_'+name]=leftover(vec,basis)
    return row,q

def pilot_stage(root,book,device,config):
    from .offline import load_truth
    dest=Path(root)/'results/a23';metric=[];curvature=[];timing=[];sketch=[];preparation=[]
    (dest/'images').mkdir(parents=True,exist_ok=True)
    for sid in config['scenes']:
        reference_snap=book.snapshot();reference_start=time.perf_counter()
        ref=make_ref(root,sid,book,device,config);book.synchronize()
        reference_wall=time.perf_counter()-reference_start
        prep={'scene':sid,'common_reference_geometry_seconds':reference_wall,
              'common_reference_counts':book.delta(reference_snap)['counts'],
              'scope':'independent deployment attribution; shared actual job billed once',
              'includes_truth_labels_or_curvature_diagnostics':False}
        data_path=dest/f'cache/scene_{sid}/transfer.npz'
        # H1 cache provenance was not serialized by its first source snapshot.
        # Pay a complete fresh reference transfer/decoder and compare all entries;
        # do not silently borrow a background matrix from an unknown key.
        start=time.perf_counter();transfer_snap=book.snapshot()
        with book.span('pilot_fresh_reference_transfer_and_decoder'):
            decoder=TikhonovDecoder(ref.matrix(),relative=config['tikhonov_relative'],device=device,book=book)
        book.synchronize();prep['direct_transfer_and_decoder_seconds']=time.perf_counter()-start
        prep['direct_decoder_seconds']=decoder.prepare_seconds
        prep['direct_transfer_and_decoder_counts']=book.delta(transfer_snap)['counts']
        cache_start=time.perf_counter()
        with np.load(data_path,allow_pickle=False) as f:
            priorA=f['A'].copy();randomized=f['randomized_transfer_A'].copy()
        mismatch=la.norm(priorA-ref.matrix())/la.norm(ref.matrix())
        if mismatch>1e-9:raise ValueError('H1_BACKGROUND_CACHE_FULL_TRANSFER_CONFLICT')
        key={'reference_key':plain(ref.cache_key),'probe_config':config['OPM'],
             'random_rank':config['randomized_transfer_rank'],'material':'full-cell real mass',
             'dtype':'complex128/float64','whitening':'declared reference RMS','newSHA256checks':0}
        meta_path=dest/f'cache/scene_{sid}/PROVENANCE.json'
        if meta_path.exists() and json.loads(meta_path.read_text())!=key:raise ValueError('CACHE_KEY_MISMATCH')
        write_json(meta_path,key)
        write_json(dest/f'CACHE_PROVENANCE_AUDIT_{sid}.json',{'full_transfer_relative_difference':float(mismatch),
            'status':'FRESH_PAID_REFERENCE_VERIFIED','key':key,'fresh_setup_seconds':time.perf_counter()-start,
            'first_H1_cache_key_gap':'RETAINED_AND_REPLACED_ONLY_IN_PILOT_BY_PAID_FRESH_PREPARATION',
            'old_H1_cache_overwritten':False})
        book.counts['cache_read_bytes']+=data_path.stat().st_size
        prep['historical_transfer_cache_audit_seconds']=time.perf_counter()-cache_start
        born_snap=book.snapshot();born_start=time.perf_counter()
        with book.span('born_decoder_prepare'):
            bornA=local_born_matrix(ref)
            bornD=TikhonovDecoder(bornA,device=device,book=book,lam=decoder.lam)
        book.synchronize();prep['born_transfer_and_decoder_seconds']=time.perf_counter()-born_start
        prep['born_counts']=book.delta(born_snap)['counts']
        random_snap=book.snapshot();random_start=time.perf_counter()
        with book.span('generic_randomized_decoder_prepare'):
            randomD=TikhonovDecoder(randomized,device=device,book=book,lam=decoder.lam)
        book.synchronize();prep['random_decoder_seconds']=time.perf_counter()-random_start
        prep['random_decoder_counts']=book.delta(random_snap)['counts']
        quadratic_snap=book.snapshot();quadratic_start=time.perf_counter()
        with book.span('quadratic_compression_prepare'):
            Uy,sketchrow,rawprobe=quadratic_sketch(ref,config)
        book.synchronize();prep['quadratic_compression_including_holdout_audit_seconds']=time.perf_counter()-quadratic_start
        prep['quadratic_compression_counts']=book.delta(quadratic_snap)['counts']
        # The full fixed preparation/audit cost is attributed to the candidate;
        # do not remove heldout probes from its deployment cost after seeing data.
        quadratic_io_start=time.perf_counter()
        sketchrow['scene']=sid;sketch.append(sketchrow)
        write_json(dest/'QUADRATIC_SKETCH_AUDIT.json',sketch)
        np.savez_compressed(dest/f'cache/scene_{sid}/quadratic.npz',Uy=Uy,probe_response=rawprobe)
        prep['quadratic_cache_export_seconds']=time.perf_counter()-quadratic_io_start
        preparation.append(prep);write_json(dest/'PIPELINE_PREPARATION_RAW.json',preparation)
        # Only offline generator reads nominal unknown material.
        nominal=load_truth(root,sid)
        ref.validate_material(nominal)
        labels={};prediction=[]
        for t in config['amplitudes']:
            truth=ref.chi0+t*(nominal-ref.chi0)
            labelpath=dest/f'OFFLINE_CLEAN_LABEL_{sid}_t{t}.npz'
            if labelpath.exists():
                with np.load(labelpath,allow_pickle=False) as f:
                    if not np.array_equal(f['truth_OFFLINE'],truth) or str(f['cache_key'])!=json.dumps(key,sort_keys=True):raise ValueError('CACHED_LABEL_MATERIAL_OR_KEY_CONFLICT')
                    clean=f['clean'].copy();rawfield=f['raw_field'].copy()
                book.counts['cache_read_bytes']+=labelpath.stat().st_size
            else:
                with book.scope('OFFLINE_CLEAN_LABEL_GENERATION'):
                    clean,state=ref.predict(truth)
                rawfield=state.field.copy()
                np.savez_compressed(labelpath,truth_OFFLINE=truth,clean=clean,raw_field=rawfield,
                    parent_id=sid,t=t,upstream_commit=config['upstream_commit'],cache_key=json.dumps(key,sort_keys=True))
                book.counts['cache_write_bytes']+=labelpath.stat().st_size
            labels[t]=(truth,clean,rawfield)
        sigma=.1*float(np.sqrt(np.mean(abs(labels[1.][2]-ref.state.field)**2)))
        if sigma<=0:raise ValueError('ZERO_NOMINAL_DIFFERENCE_NOISE_SCALE')
        for t in config['amplitudes']:
            truth,clean,raw=labels[t];xtrue=ref.adapter.chart.project(truth-ref.chi0)
            with book.scope('OFFLINE_CURVATURE_DIAGNOSTIC'):
                crow,qtrue=curvature_row(ref,xtrue,clean,decoder,config,sid,t)
            curvature.append(crow)
            np.savez_compressed(dest/f'CURVATURE_{sid}_{t}.npz',**qtrue,linear=ref.matrix()@xtrue,finite=clean-ref.data0)
            for noise in config['noise']:
                rng=np.random.default_rng(np.random.SeedSequence([config['master_seed'],sid,int(100*t),411]))
                epsilon=np.zeros_like(raw) if noise=='zero' else gaussian_noise(rng,raw.shape,sigma)
                encode_start=time.perf_counter()
                measured=ref.adapter.whiten(pack(raw+epsilon));z=measured-ref.data0
                encode_wall=time.perf_counter()-encode_start
                x1=decoder.decode(z)
                reconstructed={};method_costs={}
                methods=['homogeneous_born','born_BP','dressed_linear_chi','linear_a_exact_conversion',
                         'vanilla_IBS2','A23_compressed_feedback','generic_randomized_linear','current_BP_ratio']
                for method in methods:
                    attempts=[];counts=[];chi=None
                    for repeat in range(1+config['warm_repeats']):
                        snap=book.snapshot();start=time.perf_counter()
                        try:
                            candidate=candidate_from_measurement(ref,decoder,bornA,bornD,randomD,Uy,z,method,config)
                        except Exception as error:
                            from a20.costs import BudgetExceeded
                            if isinstance(error,BudgetExceeded):raise
                            book.counts['failed_attempts']+=1
                            book.synchronize();attempts.append(time.perf_counter()-start);counts.append(book.delta(snap)['counts'])
                            append_failure(root,'ALGORITHM_CANDIDATE_FAILURE',scene=sid,t=t,noise=noise,method=method,reason=str(error),charged=True)
                            chi=None;algorithm_error=str(error);break
                        with book.span('candidate_feasibility_check',candidate_feasibility_checks=1):
                            try:ref.validate_material(candidate)
                            except ValueError:pass
                        book.synchronize();attempts.append(time.perf_counter()-start);counts.append(book.delta(snap)['counts'])
                        if chi is None:chi=candidate.copy()
                    if chi is None:
                        metric.append({'scene':sid,'t':t,'noise':noise,'method':method,'status':'FAILED_ALGORITHM',
                            'reason':algorithm_error,'full_chi_NRMSE':None,'datafullresidual':None,'full_validation':'NOT_RUN',
                            'cold_decode_seconds':attempts[0] if attempts else None,'warm_decode_seconds':None,'full_dimension':ref.p})
                        timing.append({'scene':sid,'t':t,'noise':noise,'method':method,'cold':attempts[0] if attempts else None,
                            'warm_repeats':attempts[1:],'cold_actions':counts[0] if counts else {},'status':'FAILED_ALGORITHM'})
                        continue
                    status='OK'
                    try:ref.validate_material(chi)
                    except ValueError as e:
                        status='REJECTED_PHYSICAL';append_failure(root,'CANDIDATE_REJECTED',scene=sid,t=t,noise=noise,method=method,reason=str(e),charged=True)
                    row=image_metrics(ref,chi,truth,nominal,method=method,scene=sid,t=t,noise=noise,status=status)
                    pred=ref.adapter.chart.project(chi-ref.chi0)
                    row.update(surrogateresidual=float(la.norm(ref.matrix()@pred-z)/la.norm(z)),
                         cold_decode_seconds=attempts[0],warm_decode_seconds=float(np.median(attempts[1:])),
                         sigma_physical=sigma if noise!='zero' else 0.,sigma_whitened=sigma/ref.scale if noise!='zero' else 0.,
                         common_lambda=decoder.lam,full_dimension=ref.p)
                    row['online_pack_encode_seconds']=encode_wall
                    metric.append(row);reconstructed[method]=chi;method_costs[method]=counts[0]
                    timing.append({'scene':sid,'t':t,'noise':noise,'method':method,'cold':attempts[0],
                        'warm_repeats':attempts[1:],'cold_actions':counts[0],'warm_actions':counts[1:]})
                    if t==1. and noise!='zero' and method in ('dressed_linear_chi','vanilla_IBS2','A23_compressed_feedback'):
                        prediction.append((row,chi,measured,z))
                save_csv(dest/'FULL_IMAGE_METRICS.csv',metric)
                save_csv(dest/'CURVATURE_DECOMPOSITION.csv',curvature)
                write_json(dest/'DECODE_TIMING_RAW.json',timing)
                arrays={k:v for k,v in reconstructed.items()}
                image_io_start=time.perf_counter()
                np.savez_compressed(dest/f'images/scene_{sid}_t{t}_{noise}.npz',truth_OFFLINE=truth,
                    measured=measured,noise=epsilon,**arrays)
                image_io_wall=time.perf_counter()-image_io_start
                for saved_row in metric:
                    if saved_row.get('scene')==sid and saved_row.get('t')==t and saved_row.get('noise')==noise:
                        saved_row['shared_observation_image_export_seconds']=image_io_wall
                        saved_row['image_IO_attribution']='full shared export charged to each independent deployment, not summed in actual ledger'
        for row,chi,measured,z in prediction:
            start=time.perf_counter();snap=book.snapshot()
            try:
                with book.scope('ONLINE_FULL_PREDICTION_VALIDATION'):pred,state=ref.predict(chi)
                row['datafullresidual']=float(la.norm(pred-measured)/la.norm(z));row['full_validation']='RUN'
            except ValueError as e:
                row['full_validation']='REJECTED';append_failure(root,'FULL_VALIDATION_REJECTED',scene=sid,method=row['method'],reason=str(e),charged=True)
            row['full_validation_seconds']=time.perf_counter()-start
            row['validation_actions']=book.delta(snap)['counts']
        # Prespecified calibration stress: same clean nominal label and noise,
        # correlated source/receiver physical gains; no new clean solve.
        truth,clean,raw=labels[1.]
        rng=np.random.default_rng(np.random.SeedSequence([config['master_seed'],sid,509]))
        sg=1+config['calibration_source_amplitude']*rng.normal(size=ref.P)
        rg=1+config['calibration_receiver_gain']*np.repeat(rng.normal(size=ref.adapter.m//2),2)
        noise_rng=np.random.default_rng(np.random.SeedSequence([config['master_seed'],sid,100,411]))
        epsilon=gaussian_noise(noise_rng,raw.shape,sigma)
        caldata=ref.adapter.whiten(pack(raw*sg[:,None]*rg[None,:]+epsilon));cz=caldata-ref.data0
        calarrays={}
        for method in ['dressed_linear_chi','vanilla_IBS2','A23_compressed_feedback']:
            snap=book.snapshot();start=time.perf_counter()
            try:
                chi=candidate_from_measurement(ref,decoder,bornA,bornD,randomD,Uy,cz,method,config)
            except Exception as error:
                from a20.costs import BudgetExceeded
                if isinstance(error,BudgetExceeded):raise
                append_failure(root,'CALIBRATION_ALGORITHM_FAILURE',scene=sid,method=method,reason=str(error),charged=True)
                metric.append({'scene':sid,'t':1.,'noise':'20dB_calibration','method':method,'status':'FAILED_ALGORITHM',
                               'full_chi_NRMSE':None,'datafullresidual':None,'full_validation':'NOT_RUN'})
                continue
            elapsed=time.perf_counter()-start;calarrays[method]=chi
            status='OK'
            try:ref.validate_material(chi)
            except ValueError as error:
                status='REJECTED_PHYSICAL';append_failure(root,'CALIBRATION_CANDIDATE_REJECTED',scene=sid,method=method,reason=str(error),charged=True)
            row=image_metrics(ref,chi,truth,nominal,method=method,scene=sid,t=1.,noise='20dB_calibration',status=status)
            x=ref.adapter.chart.project(chi-ref.chi0)
            row.update(surrogateresidual=float(la.norm(ref.matrix()@x-cz)/la.norm(cz)),cold_decode_seconds=elapsed,
                       warm_decode_seconds=None,common_lambda=decoder.lam,full_dimension=ref.p)
            # Optional 8 full validations fixed baseline/A23, not selected by error.
            if method in ('dressed_linear_chi','A23_compressed_feedback'):
                vstart=time.perf_counter()
                try:
                    with book.scope('ONLINE_CALIBRATION_PREDICTION_VALIDATION'):pred,state=ref.predict(chi)
                    row['datafullresidual']=float(la.norm(pred-caldata)/la.norm(cz));row['full_validation']='RUN'
                except ValueError as error:
                    row['full_validation']='REJECTED';append_failure(root,'CALIBRATION_FULL_VALIDATION_REJECTED',scene=sid,method=method,reason=str(error),charged=True)
                row['full_validation_seconds']=time.perf_counter()-vstart
            metric.append(row)
        np.savez_compressed(dest/f'images/scene_{sid}_calibration.npz',truth_OFFLINE=truth,measured=caldata,
                            source_gain=sg,receiver_gain=rg,noise=epsilon,**calarrays)
        save_csv(dest/'FULL_IMAGE_METRICS.csv',metric);save_csv(dest/'CURVATURE_DECOMPOSITION.csv',curvature)
        write_json(dest/'DECODE_TIMING_RAW.json',timing)
        print(json.dumps({'stage':'pilot','scene':sid,'image_rows':len(metric),'curvature_rows':len(curvature)}),flush=True)
    return metric
