"""Unmodified A22 known-geometry utilities; no material labels."""
import numpy as np
from a20.backend import MaterialChart
COARSE_INDICES=tuple(list(range(8))+list(range(16,24)))
def _readonly(value,dtype=None):
 a=np.array(value,dtype=dtype,copy=True);a.setflags(write=False);return a

def fixed_patch_chart(points, volume):
    """Eight octants plus eight centered x-sign details, independent of data.

    H is Euclidean-orthonormal; Q=H/sqrt(v), so v Q.T Q=I.  Real material
    coordinates are [16 real coefficients, 16 imaginary coefficients].
    """
    points = np.asarray(points, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 3 or not np.all(np.isfinite(points)):
        raise ValueError("FINITE_3D_MESH_REQUIRED")
    volume = float(volume)
    if not np.isfinite(volume) or volume <= 0:
        raise ValueError("POSITIVE_CELL_VOLUME_REQUIRED")
    center = .5 * (points.min(axis=0) + points.max(axis=0))
    bits = points >= center
    octants = 4 * bits[:, 0].astype(int) + 2 * bits[:, 1].astype(int) + bits[:, 2].astype(int)
    H = np.zeros((len(points), 16), dtype=np.float64)
    counts = []
    for octant in range(8):
        index = np.flatnonzero(octants == octant)
        if len(index) < 2:
            raise ValueError("PATCH_DETAIL_REQUIRES_TWO_CELLS_IN_EVERY_OCTANT")
        H[index, octant] = 1. / np.sqrt(len(index))
        xs = points[index, 0]
        split = .5 * (float(xs.min()) + float(xs.max()))
        detail = np.where(xs >= split, 1., -1.)
        detail -= detail.mean()
        length = float(np.linalg.norm(detail))
        if length == 0:
            raise ValueError("PATCH_X_DETAIL_IS_RANK_DEFICIENT")
        H[index, 8 + octant] = detail / length
        counts.append(len(index))
    metric_error = float(np.linalg.norm(H.T @ H - np.eye(16)))
    if metric_error > 1e-10:
        raise ValueError("FIXED_PATCH_MATERIAL_METRIC_MISMATCH")
    Q = _readonly(H / np.sqrt(volume))
    chart = MaterialChart(volume, len(points), Q, "a22_fixed_patch32")
    return chart, {"basis_source": "known_mesh_only", "spatial_columns": 16,
        "real_dimension": 32, "order": "octants0:8,x_details8:16; real_then_imag",
        "octant_cell_counts": counts, "physical_metric": "volume * Q.T @ Q = I",
        "physical_metric_error": metric_error, "coarse_indices": list(COARSE_INDICES),
        "truth_fitting": False, "data_fitting": False}

def acquisition_geometry(geometry):
    """Exact A17 scenes.acquisition / A10 balanced geometry, without imports."""
    count = int(geometry.get("receiver_count", 64))
    angle = float(geometry["rotation"])
    z = 1. - 2. * (np.arange(count) + .5) / count
    phase = np.arange(count) * np.pi * (3. - np.sqrt(5.))
    rr = np.column_stack((np.sqrt(1. - z*z) * np.cos(phase),
                          np.sqrt(1. - z*z) * np.sin(phase), z))
    co, si = np.cos(angle), np.sin(angle)
    rotation = np.array([[co, -si, 0.], [si, co, 0.], [0., 0., 1.]])
    # A9 acquisition rotates receiver rows by R; A16 scenes rotates source
    # rows by R.T.  Preserve this distinction and original six-source order.
    rr = rr @ rotation
    b1 = np.cross(rr, [0., 0., 1.])
    b1 /= np.linalg.norm(b1, axis=1)[:, None]
    obs = np.stack((b1, np.cross(rr, b1)), axis=1)
    dirs, pols = [], []
    for i in range(3):
        for j in range(3):
            if i != j:
                dirs.append(np.eye(3)[i])
                pols.append(np.eye(3)[j])
    receivers = 5. * rr
    if bool(geometry.get("partial", False)):
        keep = receivers[:, 0] >= 0
        receivers, obs = receivers[keep], obs[keep]
    return (np.asarray(dirs) @ rotation.T, np.asarray(pols) @ rotation.T,
            receivers, obs)
