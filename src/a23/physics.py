"""Full-cell real material response, reusing the frozen A17 vector Maxwell.

The only reference state is the declared known background.  This module never
loads evaluator labels. Currents are c=p/sqrt(v); material x=sqrt(v)*delta chi.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
import numpy as np
from scipy import linalg as la
from a20.backend import Adapter, Problem, MaterialChart, pack, unpack, kernel, ForbiddenAccess
from a20.costs import CostBook

FORBIDDEN = {'truth','teacher','full_H','truth_state','reference_step','labels','old_GN_step'}

def load_online(path):
    """Whitelist existing geometry, discard the old chart and old-grid data."""
    allowed={'parent_id','points','volume','data0','scale','init','Q','kind','dirs',
             'pols','receivers','obs_basis','k','historical_exposed','scene_id','family'}
    with np.load(path,allow_pickle=False) as f:
        if set(f.files)-allowed:
            raise ForbiddenAccess('UNREGISTERED_RUNTIME_INPUT:'+','.join(sorted(set(f.files)-allowed)))
        d={k:f[k].copy() for k in f.files}
    n=len(d['points']);v=float(d['volume'])
    sid=int(d.get('parent_id',d.get('scene_id')))
    chart=MaterialChart(v,n,None,'full_cell')
    return Problem(sid,d['points'],v,np.zeros_like(d['data0']),1.,
                   np.full(n,.1+.04j),chart,d['dirs'],d['pols'],d['receivers'],d['obs_basis'],float(d['k']))

def alpha_second(chi,volume,k):
    kappa=1-1j*k**3*volume/(2*np.pi)
    return -18*volume*kappa/(3+kappa*np.asarray(chi))**3

class ReferencePhysics:
    def __init__(self, problem, *, book=None, device='cpu', config=None):
        self.config=config or {}
        self.book=book or CostBook(device=device,enforce=False)
        self.adapter=Adapter(problem,device=device,book=self.book,whitening=1.)
        self.device=device
        self.chi0=np.asarray(problem.init,complex).copy()
        if problem.chart.Q is not None:
            raise ValueError('A23_PRIMARY_REQUIRES_FULL_CELL_CHART')
        self.validate_material(self.chi0)
        self.state=self.adapter.full_state(self.chi0)
        # Physical reference RMS only; no truth or measured-noise norm.
        self.scale=float(np.sqrt(np.mean(np.abs(self.state.field)**2)))
        if not np.isfinite(self.scale) or self.scale<=0:
            raise ValueError('ZERO_REFERENCE_SIGNAL')
        self.adapter.whitening=1/self.scale
        self.data0=self.adapter.whiten(pack(self.state.field))
        self.p=problem.chart.d;self.N=problem.chart.n;self.P=self.adapter.P
        self.v=problem.volume;self.k=problem.frequency
        self._Z=None;self._matrix=None
        self.cache_key=(problem.parent_id,self.v,self.k,tuple(self.chi0),
                        tuple(problem.points.ravel()),tuple(problem.receivers.ravel()),
                        tuple(problem.dirs.ravel()),tuple(problem.pols.ravel()),
                        tuple(problem.obs_basis.ravel()),self.scale,self.device,'complex128')

    def __getattr__(self,name):
        if name in FORBIDDEN: raise ForbiddenAccess('OFFLINE_FIELD_IN_REFERENCE:'+name)
        raise AttributeError(name)

    def validate_material(self,chi):
        chi=np.asarray(chi,complex)
        bad_shape=(chi.shape!=self.chi0.shape) if hasattr(self,'chi0') else chi.ndim!=1
        if bad_shape:
            raise ValueError('MATERIAL_SHAPE')
        if not np.all(np.isfinite(chi)): raise ValueError('NONFINITE_MATERIAL')
        lowr=self.config.get('physical_real_lower',-.5)
        lowi=self.config.get('physical_imag_lower',0.)
        violation=max(0.,lowr-float(np.min(chi.real)),lowi-float(np.min(chi.imag)))
        if violation>1e-10: raise ValueError('PHYSICAL_MATERIAL_VIOLATION')
        v=self.adapter.problem.volume;k=self.adapter.problem.frequency
        den=3+(1-1j*k**3*v/(2*np.pi))*chi
        if np.min(abs(den)/np.maximum(3.,abs(chi)))<=self.config.get('pole_relative_floor',1e-10):
            raise ValueError('CONSTITUTIVE_POLE')
        return {'violation':violation,'pole_margin':float(np.min(abs(den)))}

    def solve_reference(self,rhs,*,adjoint=False):
        rhs=np.asarray(rhs,complex)
        columns=1 if rhs.ndim==1 else rhs.shape[1]
        counter='solve_adjoint_rhs' if adjoint else 'solve_forward_rhs'
        with self.book.span('reference_adjoint_solve' if adjoint else 'reference_solve',**{counter:columns}):
            return self.adapter.model.solver.solve(self.state._L_factor,rhs,
                  trans=2 if adjoint else 0,label='full_adjoint' if adjoint else 'full_tangent')

    def apply_L(self,current): return self.adapter.apply_L(self.chi0,current)
    def apply_L_adjoint(self,current): return self.adapter.apply_L_adjoint(self.chi0,current)
    def apply_G(self,current):
        c=np.asarray(current);cols=1 if c.ndim==1 else c.shape[1]
        with self.book.span('G',G_rhs=cols): return self.adapter.model.goff_apply(c)
    def apply_S(self,current): return self.adapter.apply_S(current)
    def apply_S_adjoint(self,data): return self.adapter.apply_S_adjoint(data)
    def apply_B(self,d): return self.adapter.apply_B(self.chi0,self.state,d)
    def apply_B_adjoint(self,c): return self.adapter.apply_B_adjoint(self.chi0,self.state,c)

    def prepare_adjoint(self,*,force=False):
        if self._Z is not None and not force: return self._Z
        with self.book.span('direct_receiver_adjoint_prepare',S_adjoint_rhs=self.adapter.m):
            rhs=self.adapter.model.GS.conj().T.copy()
            self._Z=self.solve_reference(rhs,adjoint=True)
            residual=la.norm(self.state.L.conj().T@self._Z-rhs)/la.norm(rhs)
            self.book.counts['L_adjoint_residual_audit_rhs']+=rhs.shape[1]
            if residual>1e-9: raise ValueError('REFERENCE_ADJOINT_BACKWARD_RESIDUAL')
        return self._Z

    def matrix(self,*,force=False):
        """Stream contractions per source, no n_current by p Jacobian."""
        if self._matrix is not None and not force: return self._matrix
        Z=self.prepare_adjoint(force=force)
        n=self.N;m=self.adapter.m
        # 1536 x 3456 = 40.5 MiB for this pilot, explicitly preflighted.
        if 2*self.P*m*self.p*8>256*1024**2: raise MemoryError('TRANSFER_MEMORY_PREFLIGHT')
        A=np.empty((2*self.P*m,self.p),float)
        with self.book.span('direct_streamed_transfer',B_adjoint_rhs=self.P*m):
            zh=Z.conj().T.reshape(m,n,3)
            for s in range(self.P):
                exciting=self.state.exciting[s].reshape(n,3)
                C=np.einsum('qic,ic->qi',zh,exciting)*self.state.da[None,:]/self.v
                raw=np.concatenate((C,1j*C),axis=1)
                A[s*2*m:(s+1)*2*m]=np.concatenate((raw.real,raw.imag),axis=0)/self.scale
        self._matrix=A
        return A

    def linear(self,d):
        d=np.asarray(d)
        if np.iscomplexobj(d) or d.shape[0]!=self.p: raise ValueError('REAL_FULL_MATERIAL_REQUIRED')
        if self._matrix is not None: return self._matrix@d
        one=d.ndim==1
        b=self.apply_B(d);b=b[:,:,None] if one else b
        c=self.solve_reference(b.transpose(1,0,2).reshape(self.adapter.n,-1))
        out=self.apply_S(c).reshape(self.adapter.m,self.P,-1).transpose(1,0,2)
        packed=self.adapter.whiten(pack(out))
        return packed[:,0] if one else packed

    def linear_adjoint(self,w):
        w=np.asarray(w)
        if np.iscomplexobj(w): raise ValueError('REAL_DATA_REQUIRED')
        if self._matrix is not None: return self._matrix.T@w
        return self.adapter.full_adjoint_action(self.chi0,self.state,w)

    def prior_coordinate_to_alpha(self,x):
        return self.state.a+self.state.da*self.adapter.chart.expand(np.asarray(x))

    def polarization_to_chi(self,a):
        a=np.asarray(a,complex)
        kappa=1-1j*self.k**3*self.v/(2*np.pi)
        den=3*self.v-kappa*a
        if not np.all(np.isfinite(a)) or np.min(abs(den)/np.maximum(3*self.v,abs(kappa*a)))<=self.config.get('pole_relative_floor',1e-10):
            raise ValueError('INVERSE_POLARIZABILITY_POLE')
        chi=3*a/den
        # Conversion and physical feasibility are distinct receipts.
        return chi

    def quadratic(self,left_real,right_real=None,*,components=False,outer='adjoint'):
        u=np.asarray(left_real);vv=u if right_real is None else np.asarray(right_real)
        if u.ndim!=1 or vv.ndim!=1 or np.iscomplexobj(u) or np.iscomplexobj(vv):
            raise ValueError('QUADRATIC_REAL_DIRECTION_REQUIRED')
        du=self.adapter.chart.expand(u);dv=self.adapter.chart.expand(vv)
        hu=self.state.da*du;hv=self.state.da*dv
        Eu=self.state.exciting.T
        bu=np.repeat(hu,3)[:,None]*Eu/np.sqrt(self.v)
        Xu=self.solve_reference(bu)
        Xv=Xu if right_real is None or np.array_equal(u,vv) else self.solve_reference(np.repeat(hv,3)[:,None]*Eu/np.sqrt(self.v))
        GXu=self.apply_G(Xu);GXv=GXu if Xv is Xu else self.apply_G(Xv)
        fb=.5*(np.repeat(hu,3)[:,None]*GXv+np.repeat(hv,3)[:,None]*GXu)
        local=.5*np.repeat(alpha_second(self.chi0,self.v,self.k)*du*dv,3)[:,None]*Eu/np.sqrt(self.v)
        def output(rhs):
            if outer=='adjoint':
                Z=self.prepare_adjoint()
                with self.book.span('quadratic_receiver_contraction',S_rhs=self.P): y=(Z.conj().T@rhs).T
            elif outer=='primal': y=self.apply_S(self.solve_reference(rhs)).T
            else: raise ValueError('UNREGISTERED_QUADRATIC_OUTER')
            return self.adapter.whiten(pack(y))
        if not components: return output(fb+local)
        yf=output(fb);yl=output(local)
        return {'total':yf+yl,'feedback':yf,'local':yl}

    def predict(self,chi):
        self.validate_material(chi)
        limits={'OFFLINE_CLEAN_LABEL_GENERATION':('clean_label_full_state_calls','clean_full_forward_cap'),
                'ONLINE_FULL_PREDICTION_VALIDATION':('primary_prediction_full_state_calls','primary_prediction_full_forward_cap'),
                'ONLINE_CALIBRATION_PREDICTION_VALIDATION':('calibration_prediction_full_state_calls','calibration_prediction_full_forward_cap')}
        counter=None
        if self.book.phase in limits:
            counter,key=limits[self.book.phase]
            past=self.config.get('_prior_counts',{}).get(counter,0)
            if past+self.book.counts[counter]>=self.config.get(key,0):
                from a20.costs import BudgetExceeded
                raise BudgetExceeded('PHYSICAL_CALL_CAP:'+key)
        if counter:
            self.book.counts[counter]+=1
            self.book.append({'event':'PHYSICAL_CALL_RESERVED','phase':self.book.phase,'counters':{counter:1},'status':'RESERVED',**self.book.metadata})
        with self.book.span('registered_full_prediction'):
            state=self.adapter.full_state(np.asarray(chi,complex))
        return self.adapter.whiten(pack(state.field)),state

MaterialResponse=ReferencePhysics

def gaussian_noise(rng,shape,sigma):
    if not np.isfinite(sigma) or sigma<0: raise ValueError('INVALID_NOISE_SIGMA')
    return sigma/np.sqrt(2)*(rng.normal(size=shape)+1j*rng.normal(size=shape))
