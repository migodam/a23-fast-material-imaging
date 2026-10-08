#!/usr/bin/env python3
"""Small, CPU-only A23 algebra checks; NOT an imaging performance study.

Independent implementation of the public A9 dyadic kernel and CM+radiation
reaction formula, with eight 3D vector dipoles. No A20/A22 data are loaded.
Run: OPENBLAS_NUM_THREADS=1 python validation/validate_theory.py
"""
from __future__ import annotations
import itertools
import json
import platform
import time
from pathlib import Path
import numpy as np
from numpy.linalg import norm, solve, svd

SEED = 20261008
rng = np.random.default_rng(SEED)

def orth(a: np.ndarray, tol: float = 1e-11) -> np.ndarray:
    u, ss, _ = svd(a, full_matrices=False)
    return u[:, ss > tol * (ss[0] if len(ss) else 1.)]

def rel(a: np.ndarray, b: np.ndarray) -> float:
    return float(norm(a-b) / max(norm(b), 1e-30))

def dyad(d: np.ndarray, k: float) -> np.ndarray:
    r = norm(d)
    if r == 0:
        raise ValueError('Self interaction must be represented by polarizability')
    nn = np.outer(d/r, d/r)
    return np.exp(1j*k*r)/(4*np.pi*r) * (k*k*(np.eye(3)-nn)
             +(1j*k/r-1/r**2)*(np.eye(3)-3*nn))

def alpha(chi: np.ndarray, v: float, k: float) -> np.ndarray:
    return 3*v*chi/(chi+3-1j*k**3*v*chi/(2*np.pi))

def realpack(y: np.ndarray) -> np.ndarray:
    # Per-source Re,Im ordering, y=(n_receiver_components,n_sources).
    return np.concatenate((y.T.real, y.T.imag), axis=1).reshape(-1)

def slope(ts, errs) -> float:
    return float(np.polyfit(np.log(ts), np.log(errs), 1)[0])

def algebra() -> dict:
    n, u, s = 18, 4, 3
    f = .035*(rng.normal(size=(n,n))+1j*rng.normal(size=(n,n)))
    l = np.eye(n)-f
    U = orth(rng.normal(size=(n,u))+1j*rng.normal(size=(n,u)))
    P = np.eye(n)-U@U.conj().T
    A = U.conj().T@l@U
    R = U@solve(A,U.conj().T)
    C, CH = l@U,l.conj().T@U
    K = P@(np.eye(n)-l@R)
    T = (np.eye(n)-R@l)@P
    Kc = P@(np.eye(n)-C@solve(A,U.conj().T))
    Tc = P-U@solve(A,CH.conj().T@P)
    KHc = P-U@solve(A.conj().T,C.conj().T@P)
    THc = P@(np.eye(n)-CH@solve(A.conj().T,U.conj().T))
    errs = {'K':rel(Kc,K),'T':rel(Tc,T),
            'K_adjoint':rel(KHc,K.conj().T),'T_adjoint':rel(THc,T.conj().T)}
    assert max(errs.values()) < 1e-12
    b = rng.normal(size=(n,s))+1j*rng.normal(size=(n,s))
    j = solve(l,b)
    Us = orth(j)
    Rs = Us@solve(Us.conj().T@l@Us,Us.conj().T)
    Ks = (np.eye(n)-Us@Us.conj().T)@(np.eye(n)-l@Rs)
    pzero = float(norm(Ks@b)/norm(b))
    assert pzero < 1e-12
    S = rng.normal(size=(7,n))+1j*rng.normal(size=(7,n))
    B = rng.normal(size=(n,5))+1j*rng.normal(size=(n,5))
    Xh = solve(l,B)+.02*(rng.normal(size=B.shape)+1j*rng.normal(size=B.shape))
    Zh = solve(l.conj().T,S.conj().T)+.02*(rng.normal(size=(n,7))+1j*rng.normal(size=(n,7)))
    corrected = S@Xh+Zh.conj().T@(B-l@Xh)
    exact = S@solve(l,B)
    rhs = (S-Zh.conj().T@l)@solve(l,B-l@Xh)
    dual_error = rel(exact-corrected,rhs)
    assert dual_error < 1e-10
    # Arbitrary approximate inverse is NOT a Galerkin generalized inverse.
    return {'cached_schur_relative_errors':errs,
        'source_anchored_P_relative_norm':pzero,
        'two_sided_residual_identity_relative_error':dual_error,
        'arbitrary_RA_counterexample':{'L':1,'RA':.5,'true_defect':.5,'double_defect':.25},
        'nonnormal_counterexample':{'F':[[0,100],[0,0]],'spectral_radius':0,
                                  'zeroth_order_inverse_error':100}}

def maxwell() -> dict:
    # Eight dipoles, 24 complex current coordinates, 16 real material coordinates.
    pts = np.array(list(itertools.product([-.16,.16], repeat=3)))
    N = len(pts); n=3*N; s=6; k=2.; v=.22**3
    chi0 = .7+.035*np.arange(N)+.12j
    a0 = alpha(chi0,v,k)
    G = np.zeros((n,n),complex)
    for i in range(N):
        for j in range(N):
            if i != j:
                G[3*i:3*i+3,3*j:3*j+3] = dyad(pts[i]-pts[j],k)
    dirs = np.array([[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1.]])
    pols = np.array([[0,1,0],[0,0,1],[0,0,1],[1,0,0],[1,0,0],[0,1,0.]])
    Einc = np.column_stack([(np.exp(1j*k*(pts@d))[:,None]*p).reshape(-1)
                            for d,p in zip(dirs,pols)])
    # Fibonacci sphere receivers, recording all three electric components.
    q=18
    rz=1-2*(np.arange(q)+.5)/q
    phi=np.arange(q)*np.pi*(3-np.sqrt(5))
    rec=1.4*np.column_stack([np.sqrt(1-rz**2)*np.cos(phi),
                            np.sqrt(1-rz**2)*np.sin(phi),rz])
    S=np.block([[dyad(r-x,k) for x in pts] for r in rec])
    L=np.eye(n)-np.repeat(a0,3)[:,None]*G
    b0=np.repeat(a0,3)[:,None]*Einc
    J0=solve(L,b0)
    E0=Einc+G@J0
    y0=S@J0
    Z=solve(L.conj().T,S.conj().T)
    # Real x with alpha-alpha0 = v*(x_Re+i*x_Im).
    p=2*N
    def hx(x):
        return v*(x[:N]+1j*x[N:])
    def X(x):
        return solve(L,np.repeat(hx(x),3)[:,None]*E0)
    def ordered_q(x,z):
        return realpack(Z.conj().T@(np.repeat(hx(x),3)[:,None]*(G@X(z))))
    def quad(x,z):
        return .5*(ordered_q(x,z)+ordered_q(z,x))
    def forward(x):
        a=a0+hx(x)
        ll=np.eye(n)-np.repeat(a,3)[:,None]*G
        return S@solve(ll,np.repeat(a,3)[:,None]*Einc)
    eye=np.eye(p)
    A=np.column_stack([realpack(S@X(eye[:,i])) for i in range(p)])
    Aadj=np.column_stack([realpack(Z.conj().T@(np.repeat(hx(eye[:,i]),3)[:,None]*E0))
                           for i in range(p)])
    adjerr=rel(Aadj,A)
    assert adjerr < 1e-12
    D=np.linalg.pinv(A,rcond=1e-13)
    assert norm(D@A-np.eye(p)) < 1e-9
    direction=rng.normal(size=p); direction/=norm(direction)
    ts=np.array([.2,.1,.05,.025,.0125])
    table=[]
    Ulin=orth(A)
    QQ=np.empty((A.shape[0],p,p))
    for i in range(p):
        for j in range(i,p):
            QQ[:,i,j]=QQ[:,j,i]=quad(eye[:,i],eye[:,j])
    Qflat=np.column_stack([QQ[:,i,j] for i in range(p) for j in range(i,p)])
    Ujet=orth(np.column_stack((A,Qflat)),tol=1e-10)
    for t in ts:
        x=t*direction; y=realpack(forward(x)-y0)
        lin=A@x; qq=quad(x,x)
        x1=D@y
        x2=x1-D@quad(x1,x1)
        H=np.repeat(hx(x),3)[:,None]
        TT=solve(L,H*G)
        XX=X(x)
        exact_dj=solve(np.eye(n)-TT,XX)
        exact_identity=rel(S@exact_dj,forward(x)-y0)
        eta=float(norm(TT,2))
        bound=float(norm(S,2)*eta**2/(1-eta)*norm(XX)) if eta<1 else None
        table.append({'t':float(t),'eta':eta,
            'linear_forward_error':float(norm(y-lin)),
            'quadratic_forward_error':float(norm(y-lin-qq)),
            'first_inverse_absolute_error':float(norm(x1-x)),
            'second_inverse_absolute_error':float(norm(x2-x)),
            'linear_statistic_discarded_mean':float(norm(y-Ulin@(Ulin.T@y))),
            'jet_statistic_discarded_mean':float(norm(y-Ujet@(Ujet.T@y))),
            'exact_finite_amplitude_identity_relative_error':exact_identity,
            'quadratic_remainder_norm_bound':bound})
        assert exact_identity < 1e-10
        assert bound is None or norm(y-lin-qq) <= bound*(1+1e-8)
    sl={key:slope(ts,[row[key] for row in table]) for key in
        ['linear_forward_error','quadratic_forward_error','first_inverse_absolute_error',
         'second_inverse_absolute_error','linear_statistic_discarded_mean','jet_statistic_discarded_mean']}
    assert 1.9<sl['first_inverse_absolute_error']<2.1
    assert 2.8<sl['second_inverse_absolute_error']<3.2
    assert 1.9<sl['linear_statistic_discarded_mean']<2.1
    assert 2.8<sl['jet_statistic_discarded_mean']<3.2
    # Uncentered Gaussian quadratic-response Gram factor, not unweighted pairs.
    Gquad=np.column_stack((np.sqrt(2)*QQ.reshape(A.shape[0],-1),np.einsum('aii->a',QQ)))
    Cperp=Gquad-Ulin@(Ulin.T@Gquad)
    sv=svd(Cperp,compute_uv=False)
    ranks={str(frac):int(np.searchsorted(np.cumsum(sv**2)/sum(sv**2),frac)+1)
           for frac in [.9,.99,.999]}
    # Exact M/P relation before any rank cap: B h_star = j0.
    ck=k**3/(6*np.pi)
    den=chi0+3-1j*3*ck*v*chi0
    da=9*v/den**2
    dda=-18*v*(1-1j*3*ck*v)/den**3
    uchi=rng.normal(size=N)+1j*rng.normal(size=N)
    uchi/=norm(uchi)
    toreal=lambda z:np.r_[z.real,z.imag]
    xdir=toreal(da*uchi/v)
    local=A@toreal(.5*dda*uchi**2/v)
    fb=quad(xdir,xdir)
    nrm=lambda z:z-Ulin@(Ulin.T@z)
    coord_normal_error=rel(nrm(fb+local),nrm(fb))
    chart=orth((A@xdir)[:,None])
    chart_local_fraction=float(norm(local-chart@(chart.T@local))/norm(local))
    assert coord_normal_error<1e-10
    hstar=a0/da
    Bh=np.repeat(da*hstar,3)[:,None]*E0
    F=np.eye(n)-L
    pm=rel(b0,Bh-F@Bh)
    assert pm<1e-12
    # Electromagnetic reciprocal transition operator vs nonsymmetric raw L.
    T=solve(np.diag(1/np.repeat(a0,3))-G,np.eye(n))
    return {'scope':'Independent eight-cell, three-dimensional vector DDA; no reconstruction benchmark',
        'n_current_complex':n,'p_material_real':p,'sources':s,
        'receiver_positions':q,'receiver_components':3*q,'data_real':A.shape[0],
        'background_L_condition':float(np.linalg.cond(L)),
        'linear_A_condition':float(np.linalg.cond(A)),
        'adjoint_transfer_relative_error':adjerr,'PM_degree_shift_relative_error':pm,
        'reciprocal_transition_transpose_error':rel(T.T,T),
        'raw_L_transpose_error':rel(L.T,L),
        'linear_statistic_rank':Ulin.shape[1],'full_jet_statistic_rank':Ujet.shape[1],
        'gaussian_quadratic_innovation_energy_ranks':ranks,
        'constitutive_normal_curvature_identity_relative_error':coord_normal_error,
        'one_direction_chart_local_constitutive_artifact_fraction':chart_local_fraction,
        'amplitude_table':table,'log_log_absolute_error_slopes':sl}

def probability_and_fiber() -> dict:
    d,m=4,7
    Q=rng.normal(size=(m,d,d)); Q=.5*(Q+Q.transpose(0,2,1))
    nodes=np.array([-np.sqrt(3),0,np.sqrt(3)])
    weights=np.array([1/6,2/3,1/6])
    gs=[];ws=[]
    for idx in itertools.product(range(3),repeat=d):
        gs.append(nodes[list(idx)]);ws.append(float(np.prod(weights[list(idx)])))
    gs=np.array(gs);ws=np.array(ws)
    vals=np.einsum('ni,aij,nj->na',gs,Q,gs)
    mu=ws@vals
    cov=(vals-mu).T@(ws[:,None]*(vals-mu))
    expected_mu=np.einsum('aii->a',Q)
    expected_cov=2*np.einsum('aij,bij->ab',Q,Q)
    cerr=rel(cov,expected_cov)
    assert rel(mu,expected_mu)<1e-13 and cerr<1e-13
    ts=np.array([.2,.1,.05,.025,.0125])
    out=[]
    for t in ts:
        target=.8*t; b=.6*t; aa=target
        qq=.7*aa*b+.4*b*b
        a2=target-qq
        f=lambda a:a+.7*a*b+.4*b*b+.2*b**3
        out.append({'t':float(t),'hard_split_data_error':abs(f(aa)-target),
                    'curved_fiber_data_error':abs(f(a2)-target),
                    'omitted_quadratic_channel_KL':.5*b**4})
    slopes={name:slope(ts,[r[name] for r in out]) for name in
            ['hard_split_data_error','curved_fiber_data_error','omitted_quadratic_channel_KL']}
    assert 1.9<slopes['hard_split_data_error']<2.1
    assert 2.99<slopes['curved_fiber_data_error']<3.01
    assert 3.99<slopes['omitted_quadratic_channel_KL']<4.01
    rho=.8; noisevar=.25
    prior=np.array([[1,rho],[rho,1.]])
    gain=prior[:,0]/(1+noisevar)
    post_cov=prior-np.outer(prior[:,0],prior[0,:])/(1+noisevar)
    return {'Gaussian_quadratic_covariance_relative_error':cerr,
        'Rademacher_counterexample':'Q(g,g)=(g1^2,g2^2) is always (1,1) for Rademacher; rank 1, true quadratic range rank 2',
        'fiber_amplitude_table':out,'log_log_absolute_error_slopes':slopes,
        'correlated_prior_example':{'rho':rho,'noise_variance':noisevar,
            'posterior_mean_for_y_1':gain.tolist(),'posterior_covariance':post_cov.tolist()},
        'unnormalized_factor_warning':'Integrating delta(L(x)j-b(x)) dj contributes 1/abs(det L(x)); multiply abs(det L) to normalize.'}

def main() -> None:
    start=time.perf_counter()
    report={'seed':SEED,'dtype':'complex128/float64','device':'CPU',
        'python':platform.python_version(),'numpy':np.__version__,
        'scope':'Theorem/counterexample validation only; NOT A22 replay, GPU experiment, blinded imaging study, or speed benchmark.',
        'algebra':algebra(),'tiny_vector_maxwell':maxwell(),
        'probability_and_fiber':probability_and_fiber()}
    report['wall_seconds']=time.perf_counter()-start
    report['assertions']='ALL PASSED'
    path=Path(__file__).with_name('THEORY_VALIDATION.json')
    path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    main()
