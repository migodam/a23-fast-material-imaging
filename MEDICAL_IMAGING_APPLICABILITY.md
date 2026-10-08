# 医学与工业场景：A23 最可能在哪里有用

**首选验证场景：固定阵列、已知或可重复估计的参考对象、短时间内小相对变化的 differential sensing。** 不优先承诺未知患者的高对比全头/全乳房介电常数图一次恢复。这里是研究适用性判断，不是临床建议或已验证医疗器械结论。

## 1. 物理判断来自相对反馈，不来自应用名称

有限幅度展开的控制量是
\[
\eta(h)=\|L_b^{-1}H(h)G\|.
\]
一个有强散射的已知人体参考模型，面对小温度/含水量/组织状态变化，仍可能有小h；但背景不准、天线耦合/姿势变化、near-resonance放大可使误差主导。必须把“物理背景固定”“数学参考线性化”“真实材料发生变化”分开。

这使 repeated monitoring 比一次性未知对象筛查更自然地满足摊销条件。它只是可验证机制推断，未由本轮8-cell数值构成医学证据。

## 2. 真实最近邻与我们不能宣称的东西

| 文献/场景 | 已有工作实际支持 | 对 A23 的约束 |
|---|---|---|
| 2025 differential temperature / subspace [R25] | 二维数值乳房模型；current-subspace与固定Green、Tikhonov/TwIST | “SOM式current + 重复温度监测”不是新应用，必须比较 |
| 2026 patient-specific head background [R23] | 头形及粗皮肤/脂肪知识、regularized Born/background reconstruction；anthropomorphic phantom | 未知background需要真实准备，不能把它删除后称在线实时 |
| 2025 experimental10-portbrain [R24] | 实验硬件与phantom、有限阵列几何的能力/限制 | classification/localization不等于任意3D quantitative ε map |
| 2023 breast treatment pilot [R26] | repeated treatment-monitoring应用的临床探索 | 不等于A23full-wave算法已在患者上有效 |
| MammoWave临床研究 [R27] | 临床finding/classification终点 | 不把sensitivity/specificity换算成材料NRMSE或空间分辨率 |

本轮医学论文主要为作者/出版社摘要或指定正文部分，见 `SOURCES.md`。未拿到/审核全部rawclinicaldata，不能据此做临床效能排名。

## 3. 优先级

**高优先级：同一受控phantom/工业试件的差分成像。** 可测reference，姿势/几何固定，能逐渐加大材料扰动。适合区分Born、background-dressedlinear、二阶feedback和modelbias。可重复采集不是忽略测量时间，而是把准备与在线清楚分开。

**次高：hyperthermia/thermal monitoring研究。** 小温度变化可能对应平滑介电变化；重复成像有N较大优势。但温度–介电映射依组织与频率，需外部实测/校准；本包不虚构组织系数。已有[R25]必须作为nearestbaseline，未来需要3Dvector与独立温度真值验证。

**中等：已知基线的脑/乳房监测。** 参考形状与主要背景可先估计，但头皮/颅骨、耦合介质、天线位置或姿态变化会与目标变化混淆。需要nuisance-awarelikelihood，不只做高SNR理想仿真。

**低优先级：未知患者一次性完整定量筛查。** 参考模型未知、大对比、limitedaperture、校准误差与个体差异同时存在；无条件one-shot的理论基础不足。可以另研究decoderbank/几何自适应，但应把患者specificsetup作为onlinepipeline的一部分。

## 4. 大规模真实难点

生物组织有耗、色散、异质；增加频率可改善某些分辨/归因，但也改变衰减、场分布与modelbias。不能以真空波长直接推断临床分辨率，也不能把稳定SVD方向数当成可分辨肿瘤数。

有限aperture造成方向性分辨率/不确定性；smallinclusions可能在全图NRMSE中被大背景掩盖。需同时报告背景误差、目标contrast/volume/position、falsepositive、重复测量稳定性与posterioruncertainty。

标定包括source/receivergains、phase、位置、耦合介质和antennaforwardmodel。简化点接收器DDA与真实天线S参数之间的误差不能由NN无声吸收后宣称physicsnative。

安全与功率约束影响可取得SNR、measurementduration与频点；本轮不引用未经核验的SAR限值，也不通过提高功率作为算法默认前提。未来实验须按设备、机构与适用标准执行。

## 5. 和 EIT / DOT / ultrasound / MRI 的关系

| 模态 | 可转移的数学 | 不能直接照搬的物理 |
|---|---|---|
| EIT | adjoint sensitivity、low-rank Bayesian update、nuisance profiling | 准静态conductivityPDE/边界电极模型，不是频域辐射矢量Maxwell散射 |
| DOT | Born-typeperturbation、Green/adjoint、posteriorcompression | diffusephotontransport/diffusion，不是coherentEMphaseandpolarization |
| optical inverse scattering | 多重散射、矢量/标量近似需检查、相位数据问题 | 成像NA、光学模型、weakscattering条件不同 |
| ultrasound tomography | inverseBorn、waveform、ROM、few-passcorrection | 声学/弹性，density/speed/attenuation参数与Maxwell不同 |
| MRI | Bayesian reconstruction、coil sensitivity等局部可借鉴 | 原始编码/自旋动力学模型不是本包的inverse-scatteringoperator |

“都能写成PDEinverse”不足以让同一个Schurfeedback/energy/reciprocity证明自动转移。

## 6. 怎样才算在医学 regime 击败传统算法

同一实际测量、同一geometry/calibration、同一参考信息、同一噪声、同一hardware，比较fullpipeline：
\[
T_{\rm acceptable}=T_{\rm calibration}+T_{\rm reference}
+T_{\rm physics\ setup}+T_{\rm image}+T_{\rm validation}.
\]
重复N次可摊销固定部分，但病人或姿势改变的部分不可继续摊销。

候选对照至少包含background-dressedBorn/TSVD、currentBP或SOM/CSI、经过合理regularization的DBIM/adjointreference。NN使用训练对象/标签成本另外记录，并有独立patient/phantomfamily划分。需报告真实3D体积、场/材料分辨率、source/receiver/frequency数、imagequality、功耗/内存/latency和失败率。

**本轮推荐落点。** 先做小型3Dvector差分材料phantom或工业监测，再向thermal/known-baseline组织模型过渡。若未知background估计成本或calibrationbias占主导，论文应正面报告该限制，不用“医学实时”标题遮盖。
