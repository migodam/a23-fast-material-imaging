"""Evaluator-only material labels and prior chart diagnosis, never encoder imports."""
from pathlib import Path
import numpy as np

def load_truth(root,sid):
    with np.load(Path(root)/f'data/offline_eval/scene_{sid}.npz',allow_pickle=False) as f:
        if set(f.files)!={'truth'}:raise ValueError('UNREGISTERED_OFFLINE_LABEL')
        return f['truth'].copy()

def old_chart_basis(points,volume):
    from .geometry import fixed_patch_chart
    chart,provenance=fixed_patch_chart(points,volume)
    Q=np.sqrt(volume)*chart.Q
    return np.block([[Q,np.zeros_like(Q)],[np.zeros_like(Q),Q]])
