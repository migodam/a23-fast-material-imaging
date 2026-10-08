# Cached offline diagnostics delivery

已完成一次 `a23.cached_diagnostics.summarize_cached(root)`：仅读取已保存数组与原始 metric/status，未运行物理算子、GPU、decoder，未产生新 labels 或修改参数、原始结果。

- `CHART_DIAGNOSTICS.csv`：204 行，精确使用 `a23.offline.old_chart_basis(points, volume)`；所有 finite estimates 的 chart orthogonality/energy decomposition assertions 通过 1e-9。In/out NRMSE 分母是各自 truth-background mass norm，零分母返回空值。
- `FEASIBILITY_DIAGNOSTICS.csv`：204 行，保留 raw rejected outputs；所有已保存 bounds/physical-violation 与 published status/value 相符。未 clipping，未重跑 pole validation。
- `QUADRATIC_CORRECTION_DIAGNOSTICS.csv`：28 行，涵盖 24 amplitude/noise 与 4 calibration conditions；比较的是 material-mass corrections，不解释成 data-space Q capture。
- `SKETCH_MEAN_DIAGNOSTICS.csv`：4 行，训练 mean 的 relative retention error 为 1.15–1.58e-15；heldout error 原样引用 saved audit，没有重新生成 probes。
- Standalone receipt：`results/a23/theory_verification/CACHED_DIAGNOSTICS_RECEIPT.json`，wall 0.253156 s，process CPU 0.159637 s；没有 metadata concerns 或缺少的已发布重建。

以下均为 t=1、20dB nominal-difference 的 saved-array 数值，IBS/A23 rejected 输出没有移除：

| Scene | Truth energy outside old32 | Dressed out-chart delta NRMSE | IBS out-chart delta NRMSE | A23 out-chart delta NRMSE | Correction relative deviation | Correction cosine | IBS bad Re/Im cells | A23 bad Re/Im cells |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2001 | 0.535090 | 0.804835 | 0.792264 | 0.806754 | 1.110206 | 0.366953 | 0 / 91 | 0 / 89 |
| 2003 | 0.510198 | 0.823294 | 0.617516 | 0.763265 | 0.813039 | 0.615156 | 0 / 597 | 9 / 577 |
| 2014 | 0.942347 | 0.977387 | 0.977102 | 0.977383 | 0.966432 | 0.581286 | 0 / 1 | 0 / 0 |
| 2009 | 0.866272 | 0.858109 | 0.848264 | 0.856838 | 0.947704 | 0.575708 | 0 / 270 | 0 / 269 |

函数返回 table dicts 与 paths；已实际运行一次。现有四个 derived CSV 或 receipt 存在时，再次调用会拒绝覆盖。Main 直接使用这些已完成文件，并负责科学叙述与 gates。
