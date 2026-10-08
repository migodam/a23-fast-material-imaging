# A23 最终证据一致性审计

审计日期：2026-10-08。范围为既有结果与冻结协议的数值、字段和计费一致性。此文件由独立 Codex 子任务记录；父线程负责最终科学解释。没有新 Maxwell、label、测试或图表重生成；没有修改算法、原始数据、配置或 gate。

## 1. 核心结论与证据范围

当前保存的 H1、H2、H3 均为 **FAIL**，vanilla IBS2 的 H2 机制对照也为 **FAIL**；顶层决定是 **STOP_NO_EXPANSION**。依据冻结阈值独立读取现有表格、逐行重算比较关系，得到相同布尔结果。根目录和 results 中两份 gate JSON 相同。

32行 H1、48行 H2 comparison、204行 full-image/Pareto、12行 curvature 均符合冻结矩阵。204行是192个主条件方法输出加12个 calibration 输出；28个观测来自24个主观测和4个stress观测。它们不是204个独立对象；独立场景为4个历史暴露对象，其中两个Gaussian属于同一形状家族。

从28个保存的 image NPZ 重新读取全部204个重建，full χ NRMSE最大差 **8.10463e-15**；δχ/实部/虚部指标和质量范数绝对误差也只存在浮点舍入差。所有 physical_violation 与材料接受/拒绝状态一致。这里只复核已保存数组，没有重新求解或增加label。唯一成功 full-data residual 由原已付费预测保存的行和动作 receipt 支持，未在本审计中重新求解。

## 2. 输出和 full-validation 数量

| 方法 | 全部输出 | OK（仅材料可行） | REJECTED_PHYSICAL |
|---|---:|---:|---:|
| homogeneous_born | 24 | 8 | 16 |
| born_BP | 24 | 18 | 6 |
| dressed_linear_chi | 28 | 6 | 22 |
| linear_a_exact_conversion | 24 | 7 | 17 |
| vanilla_IBS2 | 28 | 6 | 22 |
| A23_compressed_feedback | 28 | 7 | 21 |
| generic_randomized_linear | 24 | 9 | 15 |
| current_BP_ratio | 24 | 18 | 6 |
| 合计 | 204 | 79 | 125 |

“OK”表示材料可行性通过，不等于成像质量或full-forward validation通过。全表full-validation是 **RUN 1 / REJECTED 19 / NOT_RUN 184**。预注册12个keyprediction中1个运行、11个材料拒绝；可选8个calibration baseline/A23 check均在材料处拒绝。另4个calibration IBS2行没有分配full检查，保持NOT_RUN。19个validation拒绝已经包含在125个原始image拒绝中，不能再当19个独立失败图像相加。

125个被拒绝输出保留全部raw材料误差；沒有clip或隐藏projection。fallback_count全部0。未full运行的datafullresidual均为空值，未填0或用surrogateresidual代替。所有204行 full_dimension=3456。

pilot终止receipt计 **4 reference + 12 clean-label + 1合法prediction =17个full-forward states**。分phase计数为clean12/12、primary1/12、calibration0/8。材料检查拒绝没有占用full-state调用，但其检查时间保留。H1与micro的reference另见各自作业receipt；不能把12个keychecks或8个stresschecks写成实际运行的20个full solves。

## 3. H1：完整准备成本已计入 direct 构造

H1完整cold成本逐行等于：共同reference/geometry + 所需共享receiver geometry归因 + cold encoder/export增量 + direct独立构造（仅direct）。32行对该加法恒等式的差为0。共同offline decoder/probe评价费用与encoder准备分开，不能把含评价的旧cold wall列直接拿来比较，也不能把direct的约0.16–0.19秒cachecopy当完整准备。direct cold独立构造包含128个adjoint-solve RHS和768个B-adjoint RHS，已加入一次。

| scene | original transfer error | original完整cold秒 | cached完整cold秒 | cached降幅 | direct独立构造秒 | direct完整cold秒 |
|---|---:|---:|---:|---:|---:|---:|
| 2001 | 5.462455% | 12.331332 | 12.225682 | 0.856762% | 4.846861 | 12.832250 |
| 2003 | 6.151660% | 16.428792 | 16.361738 | 0.408154% | 4.792140 | 16.817762 |
| 2014 | 4.864280% | 14.995364 | 14.942954 | 0.349506% | 4.907134 | 15.526394 |
| 2009 | 4.938148% | 14.684433 | 14.593750 | 0.617546% | 4.740996 | 15.023747 |

5%fidelity门槛下，没有臂达到20%完整准备降幅；独立同预算decoder-weighted比较也没有通过。各臂均保留cold1/warm5，不取最快一次替代预定汇总。direct是精确transfer控制，但其实际rank在H1 receipt里未记录，保持未知；不得从别处填一个current rank。

OPM/cached实际complex-current rank32；source-anchored OPM/OM与MP为24；M-only为16。randomized rank32属于real-data range。上述rank领域不同，不能当同一横轴复杂度。L/F/G/S、forward/adjoint solve、B、QR、factorization与I/O是不同动作类别；其RHS数不能相加后冒充相等wall cost。

## 4. H2：最强原始与可行线性对照分别保留

当前线性对照集合包含homogeneous Born、Born BP、dressed χ、linear a+exact conversion和generic randomized linear。原始最小NRMSE没有因材料拒绝而删除；可行最强对照另列。a坐标对照先用背景实Jacobian的共同物理prior局部pushforward，再精确inverseconvert。它只保证参考点局部匹配，不声称强幅度下全局概率密度等价。

| scene | noise | 最强raw linear / χNRMSE / 状态 | 最强可行linear / χNRMSE | A23 χNRMSE / 状态 | A23相对raw改善 |
|---|---|---|---|---|---:|
| 2001 | zero | linear_a_exact_conversion / 0.413600823 / REJECTED_PHYSICAL | born_BP / 0.555779510 | 0.423982254 / REJECTED_PHYSICAL | -2.510012% |
| 2001 | nominal 20dB | linear_a_exact_conversion / 0.418163875 / REJECTED_PHYSICAL | born_BP / 0.556033130 | 0.427522424 / REJECTED_PHYSICAL | -2.238010% |
| 2003 | zero | dressed_linear_chi / 0.546923211 / REJECTED_PHYSICAL | 无 | 0.504133181 / REJECTED_PHYSICAL | 7.823773% |
| 2003 | nominal 20dB | generic_randomized_linear / 0.555365000 / REJECTED_PHYSICAL | 无 | 0.523061923 / REJECTED_PHYSICAL | 5.816549% |
| 2014 | zero | linear_a_exact_conversion / 0.811317960 / OK | linear_a_exact_conversion / 0.811317960 | 0.812062962 / OK | -0.091826% |
| 2014 | nominal 20dB | linear_a_exact_conversion / 0.811657333 / OK | linear_a_exact_conversion / 0.811657333 | 0.812370371 / OK | -0.087850% |
| 2009 | zero | linear_a_exact_conversion / 0.711983284 / REJECTED_PHYSICAL | 无 | 0.727928227 / REJECTED_PHYSICAL | -2.239511% |
| 2009 | nominal 20dB | linear_a_exact_conversion / 0.711568932 / REJECTED_PHYSICAL | 无 | 0.727378526 / REJECTED_PHYSICAL | -2.221794% |

全部8个nominal A23条件均不qualify。最大原始改善是2003 zero的7.823773%，仍低于10%且材料拒绝；noisy为5.816549%。2014虽然材料OK，A23比linear-a精确转换稍差。没有跨两个不同形状家族的合格结果。vanilla IBS2在2003的原始误差改善超过10%，但材料拒绝，且不形成第二家族；不能将其rawheadroom写为H2 PASS。

本审计发现汇总器最初漏列Born BP；父线程随后只修正报告并重建cached表格。修正影响8个条件组的合法最佳对照：2001 t=.5和1、2003 t=.15、2009 t=.5，均涵盖zero/noisy。只有2003 t=.15/noisy的原始最佳改为Born BP（0.349559116964282），原generic（0.351634440567306）稍弱且拒绝。48行两种feedback对应16个合法最佳字段及2个raw最佳字段已重新逐行匹配。**全部nominal最强raw、A23/IBS2主比较及H1/H2/H3结果不变。** 2001 nominal存在合法Born BP，不能笼统说该场景“所有linear baselines均拒绝”。

## 5. 幅度、noise与prior信息边界

材料插值是 χ(t)=χb+t(χnom−χb)，t=.15/.5/1；保存的12个标签与这个等式完全一致。不是polarizability的线性插值。

物理复噪声σ固定为nominal t=1 clean差分field的RMS乘0.1；同scene所有t和method共用σ。每个实/虚分量的方差为σ²/2；按source分别Re/Im pack，再以已知reference field RMS进行统一白化。背景RMS与σ定义由保存的clean/curvature/measurement数组复核，最大相对差低于2e−16。该“20dB”是nominal差分定义，低幅度的有效SNR降低；不能写成各幅度同有效20dB。

| scene | known-reference RMS | 物理复噪声σ |
|---|---:|---:|
| 2001 | 0.00717530085182 | 0.000563221085541 |
| 2003 | 0.00717396168411 | 0.00237819878107 |
| 2014 | 0.00717561151649 | 0.000197749756882 |
| 2009 | 0.00717729391953 | 0.000724470293747 |

28个保存观测的packing相对差最大1.28931e-16。zero archives的noise为0；四个calibration archives复用各自nominal noisy archive的**完全相同noise realization**。source stress按源采样5%标准差Gaussian amplitude gain；receiver stress按64个receiver采样3%标准差gain并在其两观测分量共享。它们不是每个参数固定恰好偏移5%/3%。

noise σ的nominal差分定义属于OFFLINE合成观测生成。online decoder/γ/rank不读取truth；whitening只使用已知reference。完整材料coordinate/prior规则固定，没有truth选rank/γ。相同λ适用于Tikhonov decoders及feedback；Born BP采用预注册spectral normalization，current ratio采用解析BP/材料比值，其候选公式不使用λ，不能仅因CSV存在common_lambda就声称λ作用于全部方法。

主指标 fullχNRMSE分母包含背景χ，δχNRMSE另列。弱幅度时低fullχNRMSE不能自动解释为高质量contrast恢复。truth方向curvature和old32 chart均为offline解释量，没有回送参数选择。

## 6. H3与完整 Pareto 对

当前204行Pareto表逐行保留status/full_validation，且完整时间只给statusOK、full_validation RUN的行。**complete measured pairs=1；rejected/failed=125；其余missing/unvalidated=78；eligible_quality=0。**

唯一完整行是scene2014 / t=1 / nominal noisy / A23：

| 项目 | 保存值 |
|---|---:|
| fullχNRMSE | 0.812370370991204 |
| full difference-data residual | 0.109363685552860 |
| 独立setup秒 | 40.08604560001 |
| cold decode秒 | 0.39450860000 |
| paid full validation秒 | 4.05794090003 |
| 完整归因coldtime秒 | 44.56988080003 |

该行residual低于0.20，但χ误差大于0.60，故不是quality-eligible或可认证winner。H3失败，不能用完整信息缺失的baseline制造time gain；各行未运行的fullvalidation保持NULL。

所有setup与总时间已独立复核保存的component加法：reference准备、reference transfer/decoder、historical cache完整比较、A23的quadratic训练/holdout与导出等按method独立归因；实际共享支出在ledger中只支付一次。H1与pilot处于不同阶段的reference准备时间可以不同，不能混取较小值。N10/N100是FORMULA_ONLY_NOT_MEASURED；warm5只覆盖encode/decode，本实验未跑warm full pipeline。单次cold IBS2/A23 decode差不能取代完整同质量time-to-image比较。

## 7. 曲率领域与数值核对

保存的12组Q满足向量恒等式 total=local+feedback；其各幅度t²缩放相对差最大2.47357e-15。各scalar norm/余项由保存向量复核的绝对差最多1.43e−14。不能把local和feedback的范数相加冒充fullQ，因为向量可以抵消。

| scene，t=1 | fullQ | feedbackQ | local a″ | finite−linear | finite−linear−Q | stable rank |
|---|---:|---:|---:|---:|---:|---:|
| 2001 | 2.026341349 | 2.182335262 | 2.511881623 | 1.832247852 | 0.213501456 | 48 |
| 2003 | 33.771938276 | 39.789213982 | 34.482667805 | 28.909268918 | 6.879002192 | 46 |
| 2014 | 4.846032052 | 1.176156444 | 5.390277508 | 3.073938128 | 1.791813054 | 48 |
| 2009 | 10.950576754 | 7.747759355 | 16.202405851 | 7.655224121 | 3.328535250 | 48 |

full reference tangent的数值rank在所有场景为1536，等于real data维数；这是数据空间满行秩，不代表3456维材料唯一或稳定可逆。full-tangent complement的最大**绝对**norm为total 6.3959e-11、feedback 8.05601e-11、local 7.06408e-11；对应最大相对norm为2.04893e-12，符合舍入精度附近的近零。不要把绝对6e−11写成绝对1e−12。

stable tangent按singular value≥√λ定义，rank为2001/2014/2009的48与2003的46；old32 evaluator材料chart映射到数据的rank为32。A23 quadratic-output rank32与old32材料chart是不同空间；full、stable、oldchart和nuisance之外的分量不能混称新物理信息。

保存的nuisance rank133来自6source+128 observed-component gain的较大空间；实际stress是6source+64receiver gain，两分量共享。这一旧字段须按较大per-componentgain离线诊断解释。它不影响成像gate，且不等于精确stress tangent。

Q-sketch固定32 Gaussian training probes+8holdouts，保留mean，无full p² tensor。保存holdout投影误差范围0.471524–0.755651；它们是empirical估计，不能写成rigorous bound。全局rigorous_feedback_norm_bound维持NOT_COMPUTED，12行scope均为OFFLINE_TRUTH_DIRECTION_MECHANISM_ONLY。

## 8. 最终报告需要保留的限定

- 漏列 Born BP 的报告缺口已由父线程修正，当前48行H2对照已逐行复核；原始204行和冻结门槛未改变。
- 保存的 calibration_nuisance 字段对应6个源增益和128个观测分量独立增益，秩133；实际stress使用64个receiver增益，各receiver的两分量共享。它是较大空间的离线诊断，不能称为该stress的精确切空间。
- common_lambda在所有方法行上作为共同配置记录；BP/ratio本身不使用Tikhonov λ。共享λ的字面主张仅适用于相应正则化decoder及feedback分支。
- COST_SUMMARY在report内生成时可以包含该report尚未终止的作业；最终完整成本状态需以父线程在全部终止receipt之后的刷新为准。此审计不重写总账。

没有发现将当前FAIL转换为PASS的严重数值或gate运算错误。已发现的Born-BP集合遗漏已修正；上述scope问题通过明确文字解释即可保留原结果。小cohort、同模型full validation、已暴露场景以及未运行扩展不被升级为blind、clinical或独立model证据。此次一致性检查支持表格数值和现有冻结gate的机械一致性，不代替父线程的科学判断。

## 9. 输入与审计成本

主要输入：CODEX_A23_EXECUTION_SPEC.md、FROZEN_CONFIG.json；H1_SUMMARY.csv、H2_COMPARISON.csv、FULL_IMAGE_METRICS.csv、PARETO_TABLE.csv、CURVATURE_DECOMPOSITION.csv；PIPELINE_PREPARATION_RAW.json、QUADRATIC_SKETCH_AUDIT.json、A23_GATE_DECISION.json及pilot终止receipt；28个保存images、12个clean labels/curvature数组和online geometry；report/h1_report/pilot/physics/encoder源代码只读。没有调用这些生产函数。

独立审计收据：results/a23/theory_verification/FINAL_EVIDENCE_AUDIT_RUN_0001.json。GPU=0、physical calls=0、new labels=0、tests rerun=0、plots regenerated=0。计时scope是成功记录的Python读取/数组核对CPU区间和本次最终表格/文档写入进程；源文件shell阅读及代理控制时间不伪装为精确进程CPU。
