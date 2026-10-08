# A23 公开证据索引

路径均相对仓库。`A23_RUN_MANIFEST.json`登记范围、环境、阶段、来源和预算；`FROZEN_CONFIG.json`、`configs/SCIENTIFIC_AGGREGATION_FREEZE.json`在质量输出前冻结；`RUN_SOURCE_SNAPSHOT.json`记录实际pilot源码commit。`SOURCE_MANIFEST.json`、`docs/BACKEND_MAP.md`、`PROTOCOL_CONFLICTS.md`解释坐标、输入、缓存和显式冲突处理。

## 物理与重建

| 文件/目录 | 证据 |
|---|---|
| `results/a23/H1_ENCODER_METRICS.csv`、`H1_SUMMARY.csv` | 八方法×四场景；cold1/warm5、实际rank、动作与完整准备成本 |
| `results/a23/SEED_REDUNDANCY.csv`、`h1/scene_*/` | deflation、source-P结构零、固定probes/randomizedtraining |
| `results/a23/OFFLINE_CLEAN_LABEL_*.npz` | 12个新n12多源cleanlabel，OFFLINE生成/评价 |
| `results/a23/images/*.npz` | 24主观测及4标定；全部raw图像，拒绝图像不删除 |
| `results/a23/FULL_IMAGE_METRICS.csv` | 204行全材料、实/虚、edge/support、可行性、数据与计时 |
| `results/a23/H2_COMPARISON.csv` | 最强原始/合法匹配线性对照和逐条件改善 |
| `results/a23/CURVATURE_DECOMPOSITION.csv`、`CURVATURE_*.npz` | OFFLINE Q/反馈/locala″/有限幅度、四类不同complements |
| `results/a23/QUADRATIC_SKETCH_AUDIT.json`、`QUADRATIC_SKETCH_*.npz` | 固定rank32、Gaussian训练均值和独立holdout |
| `results/a23/CHART_DIAGNOSTICS.csv`、`FEASIBILITY_DIAGNOSTICS.csv` | 204行chart内外能量/误差和raw材料逐cell违规 |
| `results/a23/QUADRATIC_CORRECTION_DIAGNOSTICS.csv`、`SKETCH_MEAN_DIAGNOSTICS.csv` | cached-only decodedcorrection差异和实际均值保留 |

## 成本、失败与图

`results/a23/jobs/*/`保存实际manifest、终止receipt和ACTION日志；`COST_LEDGER.jsonl`、`ACTION_LEDGER.jsonl`、`TIMING_LEDGER.jsonl`、`COST_SUMMARY.json`是机械去重snapshot，原收费不覆盖。transport记录进程尾部和控制器费用，不含连接凭证。`FAILURE_LEDGER.jsonl`、`runs/*.stderr`保留candidate/validation拒绝和代码失败，scope不同不冒充独立样本。

`PIPELINE_PREPARATION_RAW.json`、`DECODE_TIMING_RAW.json`、`PARETO_TABLE.csv`区分真实shared费用与每方法独立setup归因、null/full验证和公式摊销。`theory_verification/`保留tiny、adapter、guards及审计CPUreceipt；小模型actions不混入production。

`figures/a23/PLOT_MANIFEST.json`列26图PNG/SVG、rawCSV、缺失/拒绝处理。图展示证据，科学判断由冻结gates和报告给出。

`data/online`是白名单runtime输入；`data/offline_eval`仅label/evaluation。约3.15GB derived workspace未公开，公开input/probes和代码可重建；详见REPRODUCE。未保存的fullresidual保持null，不由surrogate代填。
