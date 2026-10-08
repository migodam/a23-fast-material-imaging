"""Small geometry passed to the preserved A20/A17 backend, never a new solver."""
from __future__ import annotations

import itertools
import json
import os
from pathlib import Path

import numpy as np

from a20.backend import MaterialChart, Problem
from a20.costs import CostBook

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "FROZEN_CONFIG.json").read_text(encoding="utf-8"))
AUDIT_BOOKS: list[CostBook] = []
AUDIT_MEASUREMENTS: dict = {}


def record_measurement(name: str, value) -> None:
    """Only tiny test diagnostics; these are never inserted into pilot gate rows."""
    AUDIT_MEASUREMENTS[name] = value


def audit_book(**kwargs) -> CostBook:
    if "path" not in kwargs and os.environ.get("A23_TEST_ACTION_LEDGER"):
        kwargs["path"] = os.environ["A23_TEST_ACTION_LEDGER"]
    kwargs["metadata"] = {"test_scope": "tiny_adapter_only", "test_book": len(AUDIT_BOOKS)+1,
                          **kwargs.get("metadata", {})}
    book = CostBook(device="cpu", **kwargs)
    AUDIT_BOOKS.append(book)
    return book


def tiny_problem(*, heterogeneous: bool = False) -> Problem:
    points = np.array(list(itertools.product([-.16, .16], repeat=3)), dtype=float)
    volume = .22 ** 3
    directions = np.array([
        [1., 0., 0.], [-1., 0., 0.], [0., 1., 0.],
        [0., -1., 0.], [0., 0., 1.], [0., 0., -1.],
    ])
    polarizations = np.array([
        [0., 1., 0.], [0., 0., 1.], [0., 0., 1.],
        [1., 0., 0.], [1., 0., 0.], [0., 1., 0.],
    ], dtype=complex)
    count = 12
    z = 1 - 2 * (np.arange(count) + .5) / count
    phi = np.arange(count) * np.pi * (3 - np.sqrt(5))
    unit = np.column_stack([
        np.sqrt(1-z*z)*np.cos(phi), np.sqrt(1-z*z)*np.sin(phi), z,
    ])
    theta = np.column_stack([z*np.cos(phi), z*np.sin(phi), -np.sqrt(1-z*z)])
    azimuth = np.column_stack([-np.sin(phi), np.cos(phi), np.zeros(count)])
    obs_basis = np.stack([theta, azimuth], axis=1).astype(complex)
    init = np.full(len(points), .1 + .04j)
    if heterogeneous:
        init += .035 * np.arange(len(points))
    return Problem(
        -23, points, volume, np.zeros((len(directions), 2*count), complex),
        1., init, MaterialChart(volume, len(points), None, "full-cell"),
        directions, polarizations, 1.4*unit, obs_basis, 2.,
    )


def relative_error(left, right) -> float:
    return float(np.linalg.norm(np.asarray(left)-np.asarray(right)) /
                 max(np.linalg.norm(right), 1e-30))
