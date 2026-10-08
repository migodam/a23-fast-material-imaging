# 新颖性审计：最接近的工作、真正差异与不可宣称项

审计日期 2026-10-08。完整书目信息、链接及阅读层级见 `SOURCES.md`。这是有明确最近邻的研究审计，不是穷尽全球优先权检索。尤其 [R04] 的完整证明、[R15] 的全部构造和 quadratic-bilinear/Volterra reduction 文献需要投稿前逐页复核。

## 1. 最近邻对照

| 最近邻 | 已覆盖的概念 | A23尚可能的实质差异 | 需要证明/实测的缺口 |
|---|---|---|---|
| SOM/TSOM/FFT改进 [B01,R01] | current信息划分、传播/观察弱强、避免昂贵SVD | 实际material-feedback二阶response及few-passmaterialinverse | 不是再造currentranking；fullimage/time有优势 |
| ICLM/SOM-Net [R02–R03] | 从电磁结构设计current/material网络、显式物理一致性 | 无NN的曲率压缩；或full-image补全的解析非线性recoil | 单纯currentblock/少层NN已不新 |
| MFFSOM-Net2026 [R28] | multi-frequencycurrentlearning与EFIE融合 | 同一fullwaveposterior的预算化压缩/新算子共享 | 摘要已足以排除“首次多频SOM-NN” |
| 电磁inverseBorn收敛 [R04] | Born/inverseBorn级数与充分收敛条件 | 与真实极化率、dual-cache及data-space信息预算结合 | 二阶inverseformula本身不是新贡献 |
| second-degree方法 [R05] | 二阶predictor-corrector | 具体Maxwellfeedback可廉价实现及误差拆解 | 不宣称首次非GN二阶校正 |
| Maxwelldata-drivenROM [R06–R08] | 从数据构造ROM、内部场/成像、降低反演非线性 | 有耗频域vectorbackend、明确prior与相对feedbackdecoder | 不混淆其lossless/2Dnumerics和我们的假设 |
| goal-orientedROM/DWR [R10–R11] | primal/dualresidual乘积、projection | cachedSchur成本消除、sourceanchoredP删除、具体feedbackjet | 代数投影/DWR不作独立新理论 |
| randomizedSVD/LIS/scorecompression [R09,R12–R13] | transfer压缩、prior-relativeinformative空间、局部统计 | finite-amplitudequadraticmeanfamily与posteriorloss预算 | SVD和Gaussianlikelihood恒等式本身已知 |
| nullspace/nonlineardata-consistentNN [R14–R15] | 可靠信息保护、非线性data-consistency | Maxwell显式Q(a,b)recoil和低成本实现 | “首次curveddata-consistentNN”不成立 |
| learnedprimaldual/PnP/RED [R16,R18–R19] | 显式physics+learnedprior | 不依赖重复fullsolve的少pass机制 | 新损失/拼接feature不足 |
| diffusion/flowinverse [R20–R22] | conditionalgeneration、likelihoodguidance、posterior近似 | 实際Maxwellcompressedlikelihood和density-correctfibre | 小latent与正确posterior均需证据 |
| quadratic-bilinearMOR [R30] | 高阶输入输出/系统压缩 | constitutive-correctedfeedbackcurvature的物理分类 | 不能只把Volterra核换OPM名字 |

## 2. 四层贡献分类

### 标准线性代数 / 概率论
Schur消元、adjoint contraction、Krylov、SVD、Gaussianconditioning、KLchainrule、Isserlis四阶矩、coareaJacobian、source-subspace exactness。证明写清楚仍有价值，但不称为新的基础原理。

### 已知ROM/非线性反演
inverseBorn2、DWRcorrection、snapshot/offline-online、quadraticbilinearresponse、data-consistentpriorlearning。其Maxwell实现可有工程贡献，不能只靠命名成为strongTAP。

### A23本轮推导的Maxwell专属落实
真实CM-RR极化率的二阶响应分解；
\[
Q_\chi=Q_{\rm feedback}(a'u,a'v)+\tfrac12J_a(a''uv);
\]
在完整单频复材料重参数化下，法向曲率不含局部constitutive项；
source-anchoring使实际P forcingseed消失；
缓存接收伴随使Q外层fullsolve消失；
极化率可行圆盘与inverse-conversionpole的联合约束。

这些是本轮给出的条件推导，不意味着所有表达式都是首次出现在文献。投稿应把贡献表述为特定成像机制/构造与经验证的效果，而不是全领域优先权。

### 真正待实验确认的算法贡献
用有限的linear+quadraticdataresponsebudget，在同质量下减少总时间；或在相同时间下得到Born/SVD不能保留的有限幅度信息，并提供可校准的priorcompletion。**目前未建立。**

## 3. 最有希望的论文中心句

候选，而不是已经证明的摘要：

> A reference-dressed Maxwell encoder preserves the data response required for few-pass material reconstruction, while a curvature-aware correction allows prior completion without silently corrupting the measurement-supported component.

中文：**不是按current可见性排列模式，而是用相对参考介质的反馈，构造足以支持少次材料反演的低成本数据表示；先验补全的反馈回响被显式补偿。**

必须配合一个明确 regime：有耗三维矢量、已知/估计参考、有限材料变化、实际source/receiver/noise、完整图像而非只看32Dchart。未知全对象强散射不在未验证的标题中偷渡。

## 4. 潜在 strong-TAP 组合

Theory：精确相对反馈identity与finite-amplitudebound；constitutive/feedback/nuisance曲率分类；压缩likelihoodbudget；nonlinearprior-recoil误差。

Algorithm：source-anchored/cached-adjoint或更便宜的randomizedtransfer；一次explicitfeedbackcorrection；必要时廉价结构prior。O/P/M标签非必需。

Evidence：fullmaterialshape、source/receiver/calibration扰动、nonlinearity/noise扫描、同质量cold/warmtime、与dressedBorn/TSVD/IBS2/SOM-CSI/通用ROM竞争。至少一个 regime 出现不可由简单baseline解释的稳定Pareto优势。

这样才有强论文潜力；只有定理恒等式+8cell验证，最多是完整的下一轮研究立项包。

## 5. Killer novelty tests

- 同A/Q/D的vanillaIBS2产生同样图、更快：不能再声称新inverse算法；只能研究setupcompression是否赢。
- 同一A的SVD选出同空间：O/P/M标签不是贡献。
- Q所谓innovation被local a''或chart外部污染解释：不能称feedback信息增益。
- 完整J满行rank且压缩噪声预算不允许降维：jetencoder无压缩优势。
- 数据一致性方法已有相同阶数/相同投影机制：需要具体Maxwellcost或适用范围差异，不是新称谓。
- 无NN已满足质量/速度：停止训练，不因想要AI论文而增加复杂度。

## 6. 明确不写的句子

不写首次physics-nativeNN、首次OPM、首次feedbacknetwork、首次one-shotinverse、首次Bayesianfeedbackgraph、首次nonlineardata-consistentcompletion，也不写所有先验补全都可限制在固定线性nullspace。

不把A22经验预算coverage或cachedQP时间改写成确定性certificate或clinicalrealtime。数学constant、samplingestimate、toyvalidation、fullwaveimagingevidence各自标明。
