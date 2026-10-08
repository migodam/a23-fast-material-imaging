"""Frozen analytic material decoders. No neural or truth-state inputs."""
from __future__ import annotations
import time
import numpy as np
from scipy import linalg as la

class TikhonovDecoder:
    def __init__(self,A,relative=.001,*,device='cpu',book=None,lam=None):
        self.A=np.asarray(A,float);self.device=device;self.book=book
        if self.A.ndim!=2 or not self.A.size or not np.all(np.isfinite(self.A)):
            raise ValueError('INVALID_TRANSFER')
        if relative<=0: raise ValueError('TIKHONOV_POSITIVE_REGULARIZATION_REQUIRED')
        started=time.perf_counter()
        if device=='cuda':
            import torch
            At=torch.as_tensor(self.A,device='cuda',dtype=torch.float64)
            U,sv,Vh=torch.linalg.svd(At,full_matrices=False)
            top=float((sv[0]**2).cpu());self.lam=float(lam) if lam is not None else relative*top
            if top<=0 or self.lam<=0: raise ValueError('ZERO_TRANSFER')
            D=(Vh.T*(sv/(sv**2+self.lam))[None,:])@U.T
            torch.cuda.synchronize();self.D=D.cpu().numpy()
            self.data_U=U.cpu().numpy();self.singular_values=sv.cpu().numpy()
        else:
            U,sv,Vh=la.svd(self.A,full_matrices=False,check_finite=False)
            top=float(sv[0]**2);self.lam=float(lam) if lam is not None else relative*top
            if top<=0 or self.lam<=0: raise ValueError('ZERO_TRANSFER')
            self.D=(Vh.T*(sv/(sv**2+self.lam))[None,:])@U.T
            self.data_U=U;self.singular_values=sv
        self.prepare_seconds=time.perf_counter()-started
        if book:
            book.counts['decoder_prepare_compact_SVD']+=1
            book.counts['decoder_matrix_bytes']+=self.D.nbytes
    def decode(self,data):
        d=np.asarray(data)
        if np.iscomplexobj(d) or d.shape[0]!=self.A.shape[0]: raise ValueError('REAL_PACKED_DATA_REQUIRED')
        return self.D@d

class PhysicsEncoder:
    def __init__(self,reference,decoder,*,quadratic_basis=None,gamma=1.,outer='adjoint'):
        self.reference=reference;self.decoder=decoder;self.quadratic_basis=quadratic_basis
        self.gamma=gamma;self.outer=outer
    def encode(self,measured_data_real):return np.asarray(measured_data_real)-self.reference.data0
    def decode_linear(self,code):return self.decoder.decode(code)
    def decode_feedback(self,code):
        x1=self.decode_linear(code)
        q=self.reference.quadratic(x1,outer=self.outer)
        if self.quadratic_basis is not None:q=self.quadratic_basis@(self.quadratic_basis.T@q)
        return x1-self.gamma*self.decoder.decode(q)

def quadratic_sketch(reference,config):
    rng=np.random.default_rng(np.random.SeedSequence([config['master_seed'],reference.adapter.problem.parent_id,803]))
    # Fixed physical prior-scale Gaussian probes, not truth/local support.
    size=config['quadratic_training_probes'];q=[]
    amplitude=.15*np.sqrt(reference.v)
    for _ in range(size):
        x=rng.normal(size=reference.p)*amplitude
        q.append(reference.quadratic(x))
    outputs=np.column_stack(q);mean=outputs.mean(axis=1)
    centered=outputs-mean[:,None]
    # Mean is explicitly included, no Rademacher diagonal collapse.
    U,s,_=la.svd(np.column_stack((mean,centered)),full_matrices=False)
    rank=min(config['quadratic_data_rank'],np.count_nonzero(s>1e-10*s[0]))
    Uy=U[:,:rank]
    errors=[]
    for _ in range(config['quadratic_holdout_probes']):
        x=rng.normal(size=reference.p)*amplitude;q=reference.quadratic(x)
        errors.append(float(la.norm(q-Uy@(Uy.T@q))/la.norm(q)))
    return Uy,{'rank':rank,'requested_rank':config['quadratic_data_rank'],'mean_retained':True,
               'training_probes':size,'holdout_probes':len(errors),'independent_probe_errors':errors,
               'empirical_only':True,'tensor_constructed':False},outputs
