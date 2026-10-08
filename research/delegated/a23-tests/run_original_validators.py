"""Run byte-preserved validator copies, with receipts separate from the pilot ledger."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "results/a23/theory_verification"


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1",
                       MKL_NUM_THREADS="1", VECLIB_MAXIMUM_THREADS="1")
    statuses = []
    for name in ["validate_theory.py", "validate_extra.py"]:
        source, destination = ROOT / "validation" / name, OUTPUT / name
        original_bytes = source.read_bytes()
        shutil.copy2(source, destination)
        assert destination.read_bytes() == original_bytes
        start = time.perf_counter()
        cpu_before = os.times()
        run = subprocess.run([sys.executable, str(destination)], cwd=OUTPUT, env=environment,
                             text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        cpu_after = os.times()
        (OUTPUT / (destination.stem+".run.log")).write_text(run.stdout, encoding="utf-8")
        row = {
            "scope": "independent algebra-only eight-cell validation; NOT production imaging",
            "script": name, "device": "cpu", "python": sys.executable,
            "return_code": run.returncode, "wall_seconds": time.perf_counter()-start,
            "child_cpu_seconds": (cpu_after.children_user+cpu_after.children_system -
                                  cpu_before.children_user-cpu_before.children_system),
            "source_byte_preserved": source.read_bytes() == original_bytes,
            "copy_byte_identical": destination.read_bytes() == original_bytes,
            "source_bytes": len(original_bytes), "sha256_check": "NOT_RUN_user_instruction",
        }
        with (OUTPUT / "ORIGINAL_VALIDATORS_LEDGER.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, allow_nan=False)+"\n")
        statuses.append(row)
        print(f"{name}: {'PASS' if run.returncode == 0 else 'FAIL'}, byte-preserved={row['source_byte_preserved']}")
    return int(any(row["return_code"] or not row["source_byte_preserved"] for row in statuses))


if __name__ == "__main__":
    raise SystemExit(main())
