# 最小决定性实验：先验证三个假设，不先训练网络

本文件给下一轮执行；本轮未运行以下真实 A23 成像实验。已有本轮结果仅为 `validation/` 的 tiny CPU 数学检查。所有新阈值是 **A23 预注册建议**，不是修改 A20–A22 已冻结的 gate。

## 1. 总体设计

三个问题足以决定是否扩大：
- H1：删除冗余/替代 OPM 后，同质量 physics encoder 是否真正更便宜？
- H2：真实有限幅度 feedback 是否在完整材料图像上提供独立于局部极化率、chart 和 nuisance 的收益？
- H3：这种收益是否在 noise/calibration 条件下转化为总 time-to-acceptable-image 优势？

用户原 Experiment1 对应 H1；Experiment2 与4对应 H2；Experiment3对应 H3；Experiment5/6在前三项出现 headroom 后才进入，不自动开 NN/Flow。

## 2. Phase 0：无 GPU 的数学与实现门

运行本包 tiny checks，另在将采用的实际 adapter 上检查：
1. 原与 cached K/T/adjoint 的 block equality；
2. source-anchored P 为零，approx-reference 的 P norm 随 residual 缩放；
3. real material adjoint、whitening/packing、a'/a'' 与有限差分；
4. Q symmetric bilinearity，Qχ 的 local constitutive 项；
5. U_y 固定、full material chart 外方向可作用；
6. basis gauge invariance 和非正规/pole反例；
7. no-truth runtime whitelist。

合格参考：complex128，identity relativeerror目标1e−10，有限差分需显示步长平台，而不是单个h通过。这些是实现容差，不是成像质量门槛。失败先修实现，不靠增大rank或training掩盖。

## 3. H1：计算最小性，不把 rank 当时间

在相同几何、已知参考 χb=.1+.04i（沿用 A22 reference 仅用于本次可比性）上，验证实际输入/单位兼容。参考 full state 合法且统一计费。

Arms：
- 原 U8/O4/P4/M4 degree1 OPM；
- 仅 cached-Schur 改写的同一 OPM；
- source-anchored OPM；
- source-anchored OM；
- MP、M-only；
- direct background adjoint/pullback；
- randomized material-to-data transfer。

P/M/O 原始 RHS、截断前后 rank、principal angles、joint rank、incremental residual全部记录。删除 P 不能靠任意padding补同rank；报告实际rank与actions两条曲线。

**评价。** 使用独立于 basis construction 的8个全材料 probe（含宽尺度、局部边缘和Gaussian随机方向），测 transfer output error、decoder-weighted error及一组对偶response。gold reference只是已知背景，不用unknown truth-state或late-GNoracle。

**计费。** full L/F/G/S actions、LU factorization、triangular RHS 是不同类别。只有相同物理操作的 vector RHS 能直接匹配；混合算法用数据无关 microbenchmark 的实际成本校准并另报walltime，不把“一次L action”等同“一次full solve”。QR/SVD与数据传输单列。

**正面信号建议。** 同一transfererror≤5%的候选中，至少出现20%实际encoder总准备成本下降；或在同预算下decoder-weightederror明显下降。只减少currentrank不算。

若只有cache改写赢，这是有用工程结果，但不单独支持新成像机制论文。若directadjoint/randomized赢，Primary采用它，放弃OPM标签。

## 4. H2：非线性 headroom 和伪曲率排除

### 最小对象与材料表示

先用 A22-R1 的4个历史暴露对象2001、2003、2014、2009；它们是feasibility，不是盲测。换成统一 **full-cell实材料坐标**，或预先固定的full-p prior-preconditioned表示。原32Dchart只作diagnostic，不作唯一输出space。

构造
\[
\chi(t)=\chi_b+t(\chi_{\rm nominal}-\chi_b),\quad
t\in\{0.15,0.5,1\}.
\]
只在原nominal材料与reference均满足声明物理范围时使用；不为通过实验事后扩大材料约束。最多12组clean多源full-wave data（每组含s个RHS）；可复用完全相同模型/几何/hash下已有clean标签，但注明历史成本和复用范围。

噪声两档：zero；以每个对象t=1的差分clean signal定义20dB noise scale，**同对象各t保持同一绝对σ**，防止每个小扰动都获得人为提高的SNR。所有方法收到相同σ和同一noise realization。总计24组观测条件，不是24个独立对象。

### 预先固定的核心 arms

A：homogeneous Born/BP，作为简单基线。
B：known-background linear-in-χ TSVD/Wiener。
C：linear-in-a + exact a→χ。
D：vanilla inverseBorn2，使用与候选相同的A/Q/D。
E：A23 compressed feedback inverse（同decoder规则）。
F：source/current BP analytic material ratio，合理实现。

generic ROM/SVD在H1筛选后保留最快合格实现；其regularization/prior/noise保持相同。不得专门弱化对照的regularization。

### 必须拆出的量

真finite response减去linear项；完整Qχ；local \(\tfrac12J_a(a''uu)\)；feedbackQ；相对于full tangent、stable tangent、32D tangent及nuisance tangent的残差分别列出。投影空间不同不能共用“information”名称。

full J若满行rank，报告normalinnovation=0，不判理论失败，也不为了制造innovation先删掉singularvectors。此时只检验in-space inverse correction是否有收益。

### 输出质量

主指标为full χ的物理L2 NRMSE，real/imag分开；另报support/edge误差及目标小区域误差。旧chart内NRMSE与chart外误差仅辅助。必须保留所有对象/幅度/噪声行，不选最好图片。

最小正面信号建议：至少两个不同形状对象出现可重复的有限幅度收益（相对最强matched-prior linear baseline，fullNRMSE改善≥10%），且不能仅由a坐标转换解释。少量对象只用于选择regime，不给总体显著性或临床保证。negative/partial也允许形成明确适用边界。

## 5. H3：真实 pipeline 与有限 paid forward validation

所有24条件可算fullmaterialerror而无需额外fullforward。完整非线性data验证先限定于 **三个预注册关键arms**：background-dressedlinear、vanillaIBS2、A23compressed；各四对象t=1/20dB，共12次预测材料的full-state验证。不要事后只验证最好看的结果。

校准压力：在同四个nominal/noisy数据上施加冻结seed的source5% amplitude与receiver3% gain扰动，增加4组观测条件，不需新cleanforward。至少baseline与A23评估完整误差；有剩余budget再做8次fullpredictionvalidation。geometryshift是独立可选扩展，需要额外full标签，预算不足记NOT_RUN。

所有未做fullvalidation的条件标NOT_RUN，不能据surrogateresidual宣称完整物理一致。使用同一后端fullforward只是full-surrogate对照，**不是独立模型验证**；额外网格/天线模型/独立discretization验证为下一阶段，不虚构已经完成。

计时含reference、encoder、decode、prior、a→χ、feasibility、fullverification、I/O。冷启动至少一次，warm重复次数在数据前固定（建议5），同步GPU，不按最快一次报性能。不同候选共享准备仅实际收费一次，另报告各自独立部署应归因成本，避免双计或漏计。

N=1/10/100分别列实际setup+公式外推，明确后两者是否实际跑过。单次decoderkernel10ms不当作time-to-image。

**正面信号建议。** 在预先声明的可接受fullimage/physicalresidual区域内，总时间下降≥20%；或同总时间图像明显改善形成非支配Pareto点。若额外fullverification抹掉所有节省，结论为当前实现无部署收益。

## 6. 预算与停止

建议未来pilot上限：GPU占用不超过2小时；CPU准备/验证独立计时，预设2小时CPU wall软目标。执行前用实际硬件microbenchmark评估余下队列；若不可完成最小关键矩阵，在开始昂贵任务前缩为预注册更小独立pilot或报告BUDGET_BLOCKED，不能运行一半后挑有利结果。

优先顺序：Phase0 → H1 → H2小幅度/nominal → H3关键12验证。NN/Flow/GMM训练、大型多频sweep、geometry全组合都不在此budget内。oldprojectgate不被本任务覆盖，所有A23输出新目录。

## 7. 何时进入先验比较

只有残余在model/calibration检查后仍是可解释材料结构，才比较：Wiener、GMM、wavelet/group、计费TV、一个小deterministicdecoder。生成模型需额外证明多模态/uncertainty calibration收益。输入允许full图，data protection用完整Q或有界近似；不得把chart外误差全部叫“prior自由度”。

## 8. 交付与研究决策

必须给完整case table、actions/timing、memory、实际rank、未运行/失败、noise/calibrationseeds、full-image/rawmaterial输出和三假设的PASS/PARTIAL/FAIL/NOT_RUN。PASS仅表示本pilot条件达到建议，不表示strongTAP/临床/泛化已建立。

最重要的是允许三种合法终局：A23few-pass有Pareto信号；只有普通adjoint/SVD值得保留；或所有low-cost近似在目标regime都不够。不得用增加网络或扩大rank把每个负结果自动变成下一轮训练计划。

## 9. 参数化公平性补充

linear-a 基线使用参考点的实极化率 Jacobian 变换同一物理材料 prior/质量度量；不能把 χ 与 a 各自使用 λI 当成公平正则化。强幅度下局部 prior 匹配不是全局 pushforward equivalence，需要单列这项差异。此项与 local a'' 消融共同防止“坐标变化看起来像 feedback 增益”。
