# CODEX A23 执行规范（独立阅读版）

## 0. 任务

实现并执行一个有硬预算的 **fast material imaging 最小pilot**。不要开展currentselection/exchange/ranking，不优化相同fullGNsolver，不训练NN/Flow，不启动大型GPUcampaign。

本文件是未来执行合同；本研究包尚未实现 `a23` 生产模块。下面的module/API/commands均为**建议新增接口**，不得声称原repo已提供它们。

目标：
H1：能否删除冗余构造，得到更便宜的physicsencoder？
H2：二阶relativefeedback能否改善完整材料成像，而非只改善32Dchart？
H3：同质量total time-to-image是否优于简单baselines？

## 1. 先读哪些已有文件

上游repo：`migodam/a20-opm-imaging`。
固定commit：`b85a29a51f4ea7b4d93617e827d88e23933b89df`。
A22原handoff额外pin：`4dd4a9fa69d4272f35a6b93d8455f77cb139187b`。

按顺序读：
- `src/a20/opm.py`：SchurFeedback、build_seeds、Hierarchy；
- `src/a20/backend.py`：realmaterial、packing、forcing、B/B*、fullstate、compressedB；
- `vendor/a17/a9_engine.py`：真实dyadicGreen、CMRR极化率；
- `A22_R1_GPT_HANDOFF.md`、`CHART_EXTERIOR_AUDIT.md`、`CACHED_ONE_SHOT_RUNTIME.md`；
- `docs/PUBLIC_PACKAGE_INDEX.md`、旧gate/results只读；
- 本包 `ONE_SHOT_INVERSE_THEORY.md`、`CHEAP_FEEDBACK_OPERATORS.md`、`MINIMAL_DECISIVE_EXPERIMENTS.md`、`THEOREM_AND_COUNTEREXAMPLE_LEDGER.md`。

A20没有证明closed-loopimaging；A21是oracle；A22-R1的32Dchart不含全部复杂材料。不得把旧叙事当新实验结果。

## 2. 工作区与预算

新建独立 `a23/` 或独立branch；旧results不覆盖。可复用源码，但所有实验receipt写 `results/a23/`，记录upstreamcommit、当前commit、configsha256、environment、device、dtype、inputhash。

未来建议GPU占用上限2小时。先CPU/tiny与microbenchmark；没有明确可用GPU或预计预算不足，停止昂贵任务，交付实现/预算估计与NOT_RUN，不自动申请云GPU。不能把失败重跑从累计计费中删除。禁止安装大型新依赖环境或复制第三方论文全文到仓库。

Plan mode：**开启一次**，仅用于检查输入可用性、落实接口、冻结case/budget/metrics与阶段顺序；计划通过后执行，不反复回到开放式路线探索。

## 3. 数学与坐标合同

原物理：
\[
j_s=a(\chi)(e_s^{inc}+Gj_s),\quad L=I-aG.
\]
原代码current为 \(c=j/\sqrt v\)，B/S成套变换。材料用fullcell的 \(2N\) 个实质量归一坐标；禁止把realmaterial直接当complexlinear自由变量。白化在原per-sourceRe/Impack之后；所有伴随通过实innerproduct检验。

原极化率：
\[
a=\frac{3v\chi}{3+\kappa\chi},\quad \kappa=1-i3c_kv,\quad c_k=k^3/(6\pi),
\]
\[
a'=\frac{9v}{(3+\kappa\chi)^2},\quad
a''=-\frac{18v\kappa}{(3+\kappa\chi)^3}.
\]
不得改为bareχ，以免破坏真实backend。inverseconversion为
\[
\chi=\frac{3a}{3v-\kappa a}.
\]
极点/物理材料范围需显式检查，不静默clip不合法值。若做passivityprojection，计为独立arm/共同步骤并重新校核数据。

参考χb=.1+.04i仅作为兼容A22的本pilot默认，必须核对实际geometry/unit/physicalbackground。未知truthstate不作为参考。

## 4. Runtime 与 offline 隔离

线上允许：geometry、sources/receivers、frequencies、declaredreference、noise/calibrationmodel、measuredy、reference-onlycachedfields/A/Q/decoder。允许在**预测材料**做付费fullforwardvalidation，这不是oracle，但要计time。

线上禁止：truthmaterial、truthcurrent、truthstateJ/H、oldfullGNsteps、late-stateoracle、依据truth选rank/decoder/γ。offline评价器可读truth以计算误差；不得把其选择传回runtime。

Known-referencefullJ/adjoint可做离线goldcontrol，不是truthJ。旧GaussianQ可能含support信息；新primary必须fullcell或truth-independentfullpprior。旧32D仅diagnostic。

Noise生成使用cleanlabel属于offline合法步骤；runtime只获得相同y/σ，不获得cleantruth。

## 5. 必须实现的算子

### 5.1 Cached Schur

令Π=I−UU*，AU=U*LU，C=LU，CH=L*U：
\[
Kv=\Pi(v-CA_U^{-1}U^*v),\quad
Tv=\Pi v-UA_U^{-1}C_H^*\Pi v,
\]
\[
T^*v=\Pi(v-C_HA_U^{-*}U^*v),\quad
K^*v=\Pi v-UA_U^{-*}C^*\Pi v.
\]
用已有FU/F*U缓存算C/CH，不新增fullaction。retaincore原guard保留；unsafe则报告失败或预先声明fallback，不加jitter救结果。

### 5.2 Source anchor

参考fullcurrent的span加入U；若j_b,s∈U且AU安全，Kb_s应为零。U的实际rank、剩余observation预算、allsourcecapture记录。和原U8比较时不伪造同rank或漏计reference准备。

### 5.3 Projection-first transfer

缓存Z=Lb^{-*}S*，或primal/materialsketch中更便宜的实现；J_s=Z*B_s。fullp流式contraction，禁止n×pcurrentJacobian与s×r×p巨型denseB未经memorypreflight直接分配。

### 5.4 二阶 response

在极化率增量h中：
\[
X_s(h)=L_b^{-1}H(h)e_{b,s},
\quad Q_a(u,v)=\tfrac12 S L_b^{-1}[H(u)GX(v)+H(v)GX(u)].
\]
已有Z时Q(h,h)=Z*H(h)GX(h)，避免outerfullsolve。
χ版本必须
\[
Q_\chi(u,v)=Q_a(a'u,a'v)+\tfrac12J_a(a''uv).
\]
Q包含Hessian的1/2。只缓存linearoutputZ时不能发现其range外的quadraticinnovation。

### 5.5 Decoders

x1=Dz；x2=x1−γD Qhat(x1,x1)，z=y−yb，不能用相反residual符号。
D采用共同prior/noise与冻结TSVD/Tikhonov/Wiener规则。γ先固定1，另允许一套数据前冻结的analyticgate，禁止truth选γ。
full-image output以χ计误差；a坐标须inverseconvert并检查pole。

## 6. 建议新增接口

使用typed dataclass/Protocol，数组shape注明；以下不是已有函数。

```python
class ReferencePhysics:
    def apply_L(self, current): ...
    def apply_L_adjoint(self, current): ...
    def solve_reference(self, rhs, *, adjoint=False): ...
    def apply_G(self, current): ...
    def apply_S(self, current): ...
    def apply_S_adjoint(self, data): ...
    def apply_B(self, material_real): ...
    def apply_B_adjoint(self, current_by_source): ...

class MaterialResponse:
    def linear(self, material_real): ...
    def linear_adjoint(self, data_real): ...
    def quadratic(self, left_real, right_real): ...
    def local_constitutive_quadratic(self, left_real, right_real): ...

class PhysicsEncoder:
    def encode(self, measured_data_real): ...
    def decode_linear(self, code): ...
    def decode_feedback(self, code): ...
```

所有physicsfunctions接受/拥有共同CostLedger，记录每列RHS。禁止globalcache跨material/frequency/geometry误复用。cachekey至少含geometry/antenna/frequency/reference/noisemetric/materialmetric/probeconfig/dtype。data-dependentOseed不能放入声称可跨测量复用的offlinecache。

## 7. 数学单元测试

先复制/运行本包独立tiny验证，再对实际adapter实现：
- cachedSchur与原式≤1e−10；
- sourceP消失与approxreference残差关系；
- realadjointdotproduct≤1e−10；
- a'/a''finite-differenceplateau；
- Qbilinear/symmetric，χ与a坐标二阶response一致；
- field/fullforwardremainder和inversecorrection阶数；
- arbitraryRA .5counterexample不得被误识为Galerkin；
- Fnilpotentnonnormalcounterexample；
- rawL非对称而物理transitionreciprocal；
- randomunitarybasisgauge；
- quadraticsketch保留mean，Rademacherdiagonalfailure；
- runtime禁止truth字段；
- core/pole/invalidmaterial/zero-signalnoise/emptybasis错误路径。

生产容差与tiny阶数不是成像gate。单元通过后才允许H1。

## 8. 数据矩阵与方法

历史feasibility对象：2001,2003,2014,2009。先检查这些A22输入实际存在；原A20的2010不是自动替换2009。缺失则报告具体路径/对象，禁止静默换易对象。

材料幅度t=.15,.5,1；fullχ interpolation；最多12cleanfullstatecalls。noisezero与nominalt1-difference的20dB固定σ，各t同σ，共24条件。所有方法同noise realization、samefullpprior、samegeometry和reference。

H1：originalOPM、cachedOPM、sourceanchoredOPM/OM、MP/M-only、directadjoint、randomizedtransfer。actualrank/actions双轴；8个independentfullmaterialprobes。

H2核心：homogeneousBorn/BP、dressedlinearχ、linear-a+exactconversion、vanillaIBS2、A23compressedfeedback、currentBP/materialratio。H1获胜的genericROM/SVD保留strongcontrol。合理CSI/DBIM只在明确额外预算内做nominalreference，未跑不能声称被击败。

H3关键付费fullvalidation：dressedlinear、vanillaIBS2、A23，各四个nominalt1/noisy对象，共12次fullpredictionstates。calibrationstress另4观测：source5%amplitude、receiver3%gain，固定seed；有预算再对baseline/A23做8次fullpredictionstates。geometryshift/multifrequency/independentdiscretization是可选扩展，不伪造已运行。

## 9. 二阶压缩审计

分别报告fullQ、locala''、feedbackQ；对fulltangent/stabletangent/32Dchart/nuisance用不同字段。fullJ满行rank时normalcurvature应为零；允许in-spaceQ有用。不能先截断J再声称其complement就是新物理信息。

Gaussianquadraticprobes的中心化均值不可丢：
CovQ(g,g)=2ΣqijqijT，mean=Σqii。streamingsketch冻结seed并用独立probes评估。不要构建fullp²tensor作为large-scale默认。

rank预算建议k=16/32/64，只作事先声明曲线；每次额外rank/probe/QR计费。不为达到gate自动增degree/扩大rank。输出proofbound与empiricalestimate不同字段。

## 10. 计费和质量

Actions最少字段：
`L_rhs, L_adjoint_rhs, F_rhs, F_adjoint_rhs, G_rhs, S_rhs, S_adjoint_rhs,
reference_factorizations, solve_forward_rhs, solve_adjoint_rhs,
B_rhs, B_adjoint_rhs, qr_columns, svd_shapes, cache_read_bytes,
cache_write_bytes, transfer_bytes, failed_attempts`。

Times：geometry、reference、seed、Schur、basis、transfer、decoderprepare、onlineencode、onlinedecode、prior、physicalvalidation、I/O、totalwall、exclusiveGPUspan。GPU同步后计时；实际共享支出与各候选独立部署归因分开，不能相加双计。

Quality主字段：
fullχNRMSE（massnorm）、real/imagNRMSE、edge/support、小目标区域、datafullresidual、surrogateresidual、physicalviolations、rejection/fallback。
旧chart内error/exteriorerror单列；fullprediction没有运行则datafullresidual=NULL并标NOT_RUN，不填0。

Cold一次；warm预先固定5次（预算不许则在开始前冻结更少并披露），不只取最快。N=1/10/100setupamortization列明extrapolated。每method完整error/time向量公开，失败不删。

## 11. 建议 gate 与停止规则

H1：同transfererror≤5%下encoder总准备成本至少降低20%，或同预算decoder-weightederror明确改善。仅cache工程收益不是newimaging机制。

H2：至少两个不同shape显示fullmaterialerror相对最强公平linearbaseline改善≥10%，且非仅a坐标转换/真值chartartifact。小cohort只定regime，不给总体显著性。

H3：在共同可接受image/residual区域内总时间下降≥20%，或相同总时间形成更优quality的非支配Pareto点。全部fullverification/failedfallback计入。

这些是新pilot建议，冻结时记录，不修改oldgates。PARTIAL可导出条件性下一步；未跑/预算不足不记FAIL。禁止把未过gate改为“扩大NN训练”。

## 12. 本次不做的事

不新增NN训练、不跑diffusion、不寻找更快fullGNsolver、不使用oraclecurrents、不建立医学临床性能主张、不把SVD输出相同包装为OPM独立信息、不复制用户本机/账号/密钥信息。

若linearadjoint/SVD已更好，交付其winner结果并停止OPM专属模块。这是合法科研成功，不要求保住旧名称。

## 13. 必交文件

`A23_RUN_MANIFEST.json`、`FROZEN_CONFIG.json`、`ACTION_LEDGER.jsonl`、
`TIMING_LEDGER.jsonl`、`FAILURE_LEDGER.jsonl`、
`SEED_REDUNDANCY.csv`、`CURVATURE_DECOMPOSITION.csv`、
`FULL_IMAGE_METRICS.csv`、`PARETO_TABLE.csv`、
`A23_GATE_DECISION.json`、`A23_RESEARCH_REPORT_ZH.md`。

保存完整重建数组、运行code/tests、rawrows和模型cacheprovenance；大cache另目录且可再生成。报告明确：
what was read / derived / implemented / run / not run；
Primary现在是否仍值得做；
三假设各自判断；
最强baseline；
全部预算与失败。

## 14. χ/a 对照的 prior 变换

linear-in-a 与 linear-in-χ 必须共享物理材料 prior/质量度量，而不是各自随意用同一个 λI。参考点用实 Jacobian \(T_a\) pullback/pushforward：
\(\Gamma_a=T_a\Gamma_\chi T_a^T\)。
记录所用 metric；强幅度时注明局部匹配的近似误差。概率密度在非线性 a→χ 变换下还需 Jacobian。任何因换坐标/换prior而获益的结果，不标成额外feedback信息。
