# A23 — Maxwell Physics-Native Fast Imaging Research Package

研究日期：2026-10-08。中文理论与路线决策包；无大规模GPU实验、无NN训练。

## 从这里开始

1. [A23_EXECUTIVE_DECISION.md](A23_EXECUTIVE_DECISION.md)：独立研究结论、数学发现、12个最终问题。
2. [ROUTE_COMPARISON_AND_DECISION.md](ROUTE_COMPARISON_AND_DECISION.md)：Primary / Secondary / High-risk / Kill，评分与证伪。
3. [CODEX_A23_EXECUTION_SPEC.md](CODEX_A23_EXECUTION_SPEC.md)：独立可执行任务合同；建议先开启一次Plan mode。
4. [SOURCES.md](SOURCES.md)：上游代码pin、原项目证据、教材定位、30项外部论文及全文/摘要访问边界。
5. [NOTATION_AND_ASSUMPTIONS.md](NOTATION_AND_ASSUMPTIONS.md)：统一记号、real/complex/metric与条件。

## 用户要求的16份研究文件

| 文件 | 内容 |
|---|---|
| A23_EXECUTIVE_DECISION.md | 研究结论与优先级 |
| OPM_REDUNDANCY_AND_MINIMALITY.md | 真实seed定义、P删除、P/Mdegree/coupling条件 |
| CHEAP_FEEDBACK_OPERATORS.md | cachedSchur、directadjoint、DWR、Krylov、randomizedquadratic |
| LARGE_SCALE_COMPLEXITY.md | n/p/source/frequency/memory、totalcost与摊销 |
| MEDICAL_IMAGING_APPLICABILITY.md | 差分监测优先、真实医学近邻与物理适用界 |
| COMPETITOR_THEORY_AUDIT.md | 十五类算法的真实瓶颈与公平比较 |
| FEEDBACK_NATIVE_NN_ARCHITECTURES.md | N1–N5竞争、curvedpriorrecoil、gauge与成本 |
| BAYESIAN_FEEDBACK_INVERSION.md | 最小linearstat、KLbudget、Gaussian/GMM、fibreposterior |
| PHYSICS_NATIVE_PRIORS.md | 被动圆盘、PDE/energy限制与非NNprox |
| SYMMETRY_RECIPROCITY_AND_GAUGE.md | reciprocaltranspose、SE3条件、gauge、跨频 |
| ONE_SHOT_INVERSE_THEORY.md | exactrelativefeedback、finiteamplitude/cubiccorrection、坐标曲率 |
| NOVELTY_AND_CLOSEST_PRIOR.md | inverseBorn/SOMNet/nonlinearDC等最近邻与不可声称项 |
| THEOREM_AND_COUNTEREXAMPLE_LEDGER.md | 六类理论、验证、20项反例 |
| ROUTE_COMPARISON_AND_DECISION.md | 独立路线裁决 |
| MINIMAL_DECISIVE_EXPERIMENTS.md | 三假设、最小矩阵、真实验证预算 |
| CODEX_A23_EXECUTION_SPEC.md | 独立实现/计费/隔离/交付规范 |

## 实际运行的最小验证

`validation/validate_theory.py`：独立八cell三维矢量DDA、Schur/PM/DWR/finiteamplitude、Gaussianquadratic、curvedfibre与反例。
`validation/THEORY_VALIDATION.json`：原始数值。
`validation/validate_extra.py`：被动极化率圆盘、inverseconversion与unitarygauge。
`validation/EXTRA_VALIDATION.json`：额外原始数值。

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python validation/validate_theory.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python validation/validate_extra.py
```

环境记录在JSON；仅需NumPy。脚本不读取上游teacher/数据，不启动GPU。不将运行wall_seconds当作实际time-to-image。

## 使用边界

已完成：来源核对、条件推导、反例、小数值检查和下一轮spec。
未完成：A23原尺寸fullimagereconstruction、matchedqualityspeedup、blindgeneralization、clinicalvalidation、NN或Flow训练。

参考论文/教材全文、上游私有数据/账号信息和第三方字体不包含在本包中。
