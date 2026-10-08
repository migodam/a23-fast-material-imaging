#!/usr/bin/env python3
"""Additional algebra-only A23 checks; no imaging, GPU, or project data."""
import json
from pathlib import Path
import numpy as np
from numpy.linalg import norm, solve

rng = np.random.default_rng(20261009)
v, k = .22**3, 2.
c = k**3/(6*np.pi)
kappa = 1-1j*3*c*v
chi = rng.uniform(0,8,1000)+1j*rng.uniform(0,2,1000)
a = 3*v*chi/(3+kappa*chi)
margin = a.imag-c*abs(a)**2
assert margin.min() > -1e-12
raw = rng.normal(size=1000)+1j*rng.normal(size=1000)
center, radius = 1j/(2*c), 1/(2*c)
z = raw-center
proj = center+z*np.minimum(1., radius/np.maximum(abs(z),1e-300))
assert np.min(proj.imag-c*abs(proj)**2) > -1e-12
chi_rec = 3*a/(3*v-kappa*a)
assert norm(chi_rec-chi)/norm(chi) < 1e-12
# Fixed linear projection loses precisely the omitted likelihood mean energy.
# A scalar conditional Gaussian KL example only.
# The posterior chain-rule bound is proved analytically, not tested here.
mu0, mu1 = 0., .7
conditional_kl = .5*(mu1-mu0)**2
# Gauge-invariant transfer moments for a complex reduced core.
r, p, m = 5, 3, 4
F = .03*(rng.normal(size=(r,r))+1j*rng.normal(size=(r,r)))
M = rng.normal(size=(r,p))+1j*rng.normal(size=(r,p))
O = rng.normal(size=(m,r))+1j*rng.normal(size=(m,r))
V, _ = np.linalg.qr(rng.normal(size=(r,r))+1j*rng.normal(size=(r,r)))
H = O@solve(np.eye(r)-F,M)
Hg = (O@V)@solve(np.eye(r)-V.conj().T@F@V,V.conj().T@M)
err = norm(H-Hg)/norm(H)
assert err < 1e-12
out = dict(scope='Algebra only; not an imaging or posterior-calibration study',
           passive_polarizability_min_margin=float(margin.min()),
           projected_polarizability_min_margin=float(np.min(proj.imag-c*abs(proj)**2)),
           polarizability_inverse_relative_error=float(norm(chi_rec-chi)/norm(chi)),
           unitary_gauge_transfer_relative_error=float(err),
           conditional_Gaussian_KL_example=conditional_kl,
           assertions='ALL PASSED')
path=Path(__file__).resolve().parent/'EXTRA_VALIDATION.json'
path.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
