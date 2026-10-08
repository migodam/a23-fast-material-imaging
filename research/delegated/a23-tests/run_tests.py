"""Stdlib unittest runner with small-CPU receipts, separate from production budgets."""
from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "results/a23/theory_verification"


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    os.environ["A23_TEST_ACTION_LEDGER"] = str(OUTPUT / "ADAPTER_ACTION_LEDGER.jsonl")
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "src"))
    start, cpu = time.perf_counter(), time.process_time()
    run_id = len(list(OUTPUT.glob("ADAPTER_TEST_RUN_*.json")))+1
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_a23_*.py",
                                                top_level_dir=str(ROOT))
    logpath = OUTPUT / f"ADAPTER_TEST_RUN_{run_id:04d}.log"
    with logpath.open("w", encoding="utf-8") as handle:
        result = unittest.TextTestRunner(stream=handle, verbosity=2).run(suite)
    from tests.a23_test_support import AUDIT_BOOKS, AUDIT_MEASUREMENTS
    import numpy as np
    import scipy
    receipts = []
    for book in AUDIT_BOOKS:
        receipt = book.receipt()
        receipt.update(book.metadata)
        receipts.append(receipt)
    report = {
        "scope": "same-backend eight-cell implementation checks; NOT production imaging evidence",
        "run_id": run_id, "tests_run": result.testsRun, "success": result.wasSuccessful(),
        "failures": [{"test": str(test), "traceback": trace} for test, trace in result.failures],
        "errors": [{"test": str(test), "traceback": trace} for test, trace in result.errors],
        "skips": [{"test": str(test), "reason": reason} for test, reason in result.skipped],
        "wall_seconds": time.perf_counter()-start, "process_cpu_seconds": time.process_time()-cpu,
        "device": "cpu", "gpu_occupation_seconds": 0., "largest_N_cells": 8,
        "python_version": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
        "separate_from_primary_forward_caps": True, "book_receipts": receipts,
        "tiny_numerical_diagnostics": AUDIT_MEASUREMENTS,
        "scientific_gate_status": {"H1": "NOT_EVALUATED_BY_THESE_TESTS",
                                   "H2": "NOT_EVALUATED_BY_THESE_TESTS", "H3": "NOT_EVALUATED_BY_THESE_TESTS"},
        "sha256_check": "NOT_RUN_user_instruction",
    }
    path = OUTPUT / f"ADAPTER_TEST_RUN_{run_id:04d}.json"
    path.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(f"{'PASS' if result.wasSuccessful() else 'FAIL'}: {result.testsRun} tests; "
          f"{len(result.failures)} failures; {len(result.errors)} errors; receipt {path.relative_to(ROOT)}")
    if not result.wasSuccessful():
        for test, trace in [*result.failures, *result.errors]:
            print(f"{test}\n{trace}")
    return int(not result.wasSuccessful())


if __name__ == "__main__":
    raise SystemExit(main())
