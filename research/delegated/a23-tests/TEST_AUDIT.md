# A23 同后端 tiny 测试与协议审计

本审计验证坐标、算子及错误路径是否按冻结合同实现。最终 **32 项测试通过**，两个原始独立 tiny 验证脚本也通过。所有计算使用 CPU，实际物理模型最多 8 个 cell；没有运行 1728-cell 对象、H1/H2/H3 成像实验或 GPU 任务。本文件的 PASS 只表示 tiny 实现检查通过。

## 范围与复用关系

读取了 `CODEX_A23_EXECUTION_SPEC.md`、`FROZEN_CONFIG.json`、`validation/validate_theory.py`、`validation/validate_extra.py`、实际 A20 adapter/chart/accounting 及 A17 DenseDDA 接口；随后检查新 `a23/physics.py` 和 `a23/encoder.py`。

实际 adapter 测试直接实例化复制保留的 A20 `Adapter`，使用它内部的 A17 `DenseDDA`，不重新实现 Green 核或 Maxwell solver。几何为 8 个三维 vector dipole、24 个复 current 坐标、16 个全 cell 实质量归一材料坐标、6 个 source、12 个 receiver、每 receiver 两个读出分量，总计 288 个实数据坐标。参考材料为声明的 `.1+.04i`。白化使用已知参考场 RMS，测试在线 loader 确实丢弃旧数据、旧 scale 和旧受限 chart。

原始独立 tiny 脚本按字节复制到 `results/a23/theory_verification/` 后运行；原始脚本及旧 JSON/log 没有被覆盖。复制前后用字节相等比较确认源文件未变，不检查 SHA256。原始脚本使用自己的独立八-cell kernel，因此其结果与本文件的实际 adapter 结果分开。

## 最终结果与证据

| 检查 | 最终 tiny 数值或结果 | 支持的结论 |
|---|---|---|
| per-source Re/Im packing、batched roundtrip、实内积 | 通过 | 数据顺序与实余切一致 |
| full-cell chart 展开/投影/质量内积、拒绝 complex 材料自由坐标 | 通过 | 使用完整 2N 实质量坐标 |
| 非对称白化矩阵的真实伴随 | 相对内积误差 9.351e-16 | 白化先 pack，再按 W / Wᵀ 配对 |
| streamed matrix 对 native JVP | 3.859e-16 | contraction 与实际 backend tangent 一致 |
| 未缓存 vector/batched tangent、实伴随 | 最大误差 4.868e-16 | 缓存前后两条路径一致 |
| a′、a″ finite-difference plateau | 最小相对误差 4.189e-12 / 4.664e-11 | CMRR 的一、二阶导数正确到该 tiny 数值精度 |
| Q 双线性、对称、半 Hessian、local/feedback 分解 | 通过；local 对解析项误差 3.187e-16 | 包含局部 a″ 项及 Hessian 的 1/2 |
| χ→a 一阶 pullback 与反馈项一致 | 3.385e-16 | 两坐标的二阶 scattering 项一致 |
| Q 的 primal / adjoint outer 路径 | 最大相对误差 5.409e-16 | receiver-adjoint contraction 与 outer full solve 一致 |
| finite-alpha exact field identity | 最大相对误差 1.659e-13；所有 remainder≤norm bound | tiny finite-amplitude 代数恒等式和范数界有效 |
| χ full-forward linear / quadratic remainder 阶数 | 2.000458 / 3.001057 | 此 probe 的绝对误差呈二阶 / 三阶 |
| full-rank tiny inverse linear / minus-feedback 阶数 | 2.001270 / 3.002673 | 此 tiny Moore-Penrose control 的负号校正呈三阶 |
| 实际 encoder 的 measured−reference 与 x₁−DQ | 通过 | 测量残差和校正符号正确 |
| 冻结 Tikhonov 对 regularized normal equation | 3.147e-14 | 测试 decoder 与同 λ 的明确方程一致 |
| exact a→χ inverse、inverse pole、constitutive pole、非有限/不合法材料、受限 chart、零参考信号 | 通过 | 错误路径显式拒绝，未静默 clip |
| Gaussian 复噪声及 pack 方差 | E|noise|² / σ² = 1.001141；实分量期望方差 0.06845 | σ 是复 RMS，每个 Re/Im 分量方差 σ²/2 |
| 冻结 cohort/ranks/probes/gates/caps | 通过 | 文件合同未被移动；并不代表 gate 达成 |
| runtime NPZ whitelist、Problem/BasisView truth/J/H 拒绝 | 通过 | 已测 Python API 阻止离线字段进入运行接口 |
| failed-span 收费、CPU shutdown reserve、nested exclusive wall | 通过 | 失败 RHS 不删除，CPU receipt 不假称 GPU 工作 |

完整原始数值见 `ADAPTER_TEST_RUN_0005.json` 的 `tiny_numerical_diagnostics`。所有测试日志保留。

## 中间失败与修复

`ADAPTER_TEST_RUN_0003.json/.log` 原样保留了 1 项测试失败。共享 RNG 因新增测试移动了 probe，中心二阶差分在 ε=.005 的相对误差为 3.3078e−6，高于测试的 2e−6 容差。这个误差随着 ε 减半约下降四倍，与中心差分的二阶截断误差一致。

测试现在采用每个方法独立的固定 seed，同时把**原来失败的同一个 probe**加入回归测试：ε=.0025 的误差为 8.2699e−7，ε=.000625 为 5.3625e−8；原容差没有放宽。所有 intermediate receipts 保留，任何物理实现文件都未因这个失败被本 worker 修改。这里说明数值差分步长不足，不能把它记作生产成像失败，也不能删除它。

## 账本与预算

最终 run 的累计 wall 为 0.141694 秒，process CPU 为 0.133430 秒；五次 adapter 测试 run 合计 wall 0.777783 秒、process CPU 0.686366 秒，包含中间失败。原始独立验证的成本另记 `ORIGINAL_VALIDATORS_LEDGER.jsonl`。

最终 run 在 tiny geometry 调用了 37 次 full state（222 个 source RHS），参考 solve_forward_rhs=321，solve_adjoint_rhs=48，G_rhs=282。这些是单元/理论验证调用，全部只作用于 8-cell 几何，记录在独立 `ADAPTER_ACTION_LEDGER.jsonl`，没有消费或混入 12 次生产 clean forward / 12 次 primary prediction / 8 次 calibration prediction 配额。

## 原始独立验证的边界

两个保留脚本的 `assertions=ALL PASSED`。它们检查 cached Schur 恒等式、source anchor、双侧残差、独立 tiny Maxwell 的阶数、Gaussian quadratic mean/covariance、reciprocal transition 与 gauge 等代数内容。其中 arbitrary-RA 和 nilpotent-nonnormal counterexample 是脚本中记录的示例字段，不能把这些常数字段误称为本 worker 的实际 adapter 实验。passivity projection 只在独立原始代数脚本中出现，未加入 A23 production arm。

## 尚未由本审计验证的事项

- H1 encoder 成本、H2 完整材料成像改善、H3 同质量 total time-to-image 全部 **NOT_EVALUATED_BY_THESE_TESTS**。
- 生产 driver 的逐对象 forward-call cap、GPU occupation 停止与每个 method 的 complete error/time 向量需要由其运行证据验证；本协议测试只冻结现有字段并测试共享 CostBook 的 CPU/失败机制。
- Gaussian 方差测试使用固定 seed 的 20000 samples/实坐标，验证生成器的声明方差；没有评价生产 20dB 重建效果或 calibration robustness。
- inverse 三阶检查使用 tiny 满列 rank Moore-Penrose decoder，仅为数学控制。生产 Tikhonov 有正则偏差，不能据此声称生产 inverse 也具有无条件三阶材料误差。
- 一种 finite eight-cell geometry 和有限 probes 不证明连续 Maxwell 精度、临床应用、总体显著性、盲测、独立离散化性能或新颖性。最终理论与科学结论由 parent Codex 判断。

## 交付与复现

- `tests/test_a23_physics.py`：实际后端、坐标/导数/二阶/噪声/错误路径；
- `tests/test_a23_protocol.py`：冻结字段、在线 schema/capability 与账本；
- `tests/a23_test_support.py`：8-cell 几何和独立 test receipt；
- `research/delegated/a23-tests/run_tests.py`：stdlib unittest 与 numerical diagnostics；
- `research/delegated/a23-tests/run_original_validators.py`：原始脚本的字节保留复制与执行；
- `research/delegated/a23-tests/TEST_STATUS.json`：简短机器可读状态；
- `results/a23/theory_verification/`：全部 copied validators、JSON、logs 与独立 ledgers。

使用现有 `.venv_nn` Python；不安装 pytest 或新环境。复现命令：

```sh
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 "<RESEARCH_ROOT>/Gaussian/.venv_nn/bin/python" research/delegated/a23-tests/run_tests.py
```
