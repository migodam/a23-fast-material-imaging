# A23 foreground transport

`tools/a23_remote.py` provides `preflight`, `deploy`, `run`, and `pull` for the
new remote root `D:/AI/A23_FAST_MATERIAL_IMAGING`. It reuses the already-installed
trusted `PrivateTransport` and `_python` helper; select that helper with
`--transport-helper` or `A23_TRANSPORT_HELPER`. No SSH target, key value or local
credential path is hardcoded into this public file. `--private-config` is
required, must be external or under a Git-ignored `private/` directory, and is
never uploaded or printed.

The shared owner root remains `D:/AI/A20_OPM_IMAGING`; its lock is
`D:/AI/A20_OPM_IMAGING/runs/gpu.lock`. Before a run the controller checks the
compute queue and shared lock immediately, and the A23 CLI must atomically
acquire that same lock. It never removes a foreign lock. After a timed-out or
failed child, it confirms child exit and queries the compute queue; an observed
child-owned lock can be removed only when its exact saved ownership payload is
unchanged and the queue is clear. Unconfirmed stops remain explicit.

Deployment is deliberately separated:

- `deploy --scope online` uploads only copied `src/a20`, `src/a23`, vendor
  Python/provenance, Python tests, `FROZEN_CONFIG.json`, runtime-only
  `data/online/*.npz`, and the two tiny validation scripts.
- `deploy --scope offline-evaluation` uploads only
  `data/offline_eval/*.npz`, under an explicit evaluator/generator-only role.
  It never places those labels in the online archive.

Archive paths, duplicate/case-alias names, symlinks and namespace escapes are
rejected. Existing frozen config and input data are immutable. Inherited
results, private files, old labels outside the explicit evaluator namespace,
PDFs and credentials are not deployment members. Code repairs may update
A23-owned source files while the shared queue/lock are clear.

The five run stages are `micro`, `phase0`, `h1`, `pilot`, and `report`; the default
device is CUDA and `--device cpu` is also accepted. A fresh explicit job ID
matching `a23-*` is required. The command is:

```text
D:/python/python.exe -B -u -m a23.cli <stage> --root D:/AI/A23_FAST_MATERIAL_IMAGING --job <new-a23-job> --device cuda --lock-root D:/AI/A20_OPM_IMAGING
```

All previous `results/a23/jobs/*/job_receipt.json` charges, including failed
jobs, and previous controller GPU tails reduce the 7200-second GPU allowance.
The frozen cap may reduce that ceiling further. `--timeout-seconds` can impose
a smaller allowance; it cannot expand the budget. A 30-second stop reserve is
subtracted before child execution. The elapsed charge includes host work in
the foreground controller and child, rather than only CUDA kernels. The CPU
target remains soft; CPU measurement is recorded rather than silently equated
to wall time.

Windows GetProcessTimes measures child and query-process CPU. Child stdout and
stderr stay in `runs/<job>.stdout` and `.stderr`; the console receives only a
small sanitized JSON result. Job receipts are preserved; when a stopped child
failed before writing one, the controller synthesizes a conservative failed
receipt. Controller CPU, remaining child CPU and GPU tails remain separate
transport receipts so they do not double count the scientific job.

Remote transport records are under `results/a23/transport/remote-*.json` and
`REMOTE_TRANSPORT_LEDGER.jsonl`. Local costs and returned remote records are
under `local-*.json` and `LOCAL_TRANSPORT_LEDGER.jsonl`. SSH/SCP failure details
are suppressed. A lost run connection leaves its launch outcome unconfirmed;
the driver does not claim that no job ran or retry it automatically.

`pull` accepts only `results/a23/` and A23 stdout/stderr logs. It stages and
validates the archive before writing. Scientific arrays and logs remain
immutable; JSON with identical values can retain its existing local bytes.
Ledger updates require literal prefix compatibility, except the exact root
`results/a23/FAILURE_LEDGER.jsonl`: independent local and remote failures keep
both raw byte versions in `platform_variants/<attempt>/local_previous/` and
`remote_latest/`, then append only incoming JSON objects absent from the local
ledger. The local prefix is never rewritten, repeated/subset pulls add no
duplicate failures, and an exclusive file lock protects the unchanged-original
check and append. Pull receipts describe this as `independent_failure_union`.
All other ledger conflicts remain strict. No hashes are computed. New files
are installed atomically without replacing old results. A pull is refused
while the shared lock remains present.

The CLI receives `A23_JOB_WALL_ORIGIN` and `A23_CONTROLLER_BUDGET_SECONDS`. It
may use the first value to meter its own inclusive wall span; otherwise the
controller records the measured excess as a separate tail. CPU thread counts
are fixed to one in the child environment. The existing helper may create a
transport-owned temporary controller script in the new remote root when the
encoded command exceeds its inline length limit.

Validation performed for this delivery: Python source compilation and
compilation of all four generated remote controller variants. No A23
preflight, deployment, physics job or pull was launched by this implementation
subtask. This check does not prove Windows execution, lock interoperability,
scientific budget correctness or any Maxwell/image gate; those require the
parent's authorized first execution and review.
