# A23 完整研究报告

2026-10-08 · 理论、源码与文献审计、路线裁决、Codex 执行规范

本报告合并16份指定研究文件，并包含记号与来源。所有原始小规模数值结果另见研究包 validation/。

## 目录

1. [A23_EXECUTIVE_DECISION.md](#section-1)
2. [NOTATION_AND_ASSUMPTIONS.md](#section-2)
3. [OPM_REDUNDANCY_AND_MINIMALITY.md](#section-3)
4. [CHEAP_FEEDBACK_OPERATORS.md](#section-4)
5. [LARGE_SCALE_COMPLEXITY.md](#section-5)
6. [MEDICAL_IMAGING_APPLICABILITY.md](#section-6)
7. [COMPETITOR_THEORY_AUDIT.md](#section-7)
8. [FEEDBACK_NATIVE_NN_ARCHITECTURES.md](#section-8)
9. [BAYESIAN_FEEDBACK_INVERSION.md](#section-9)
10. [PHYSICS_NATIVE_PRIORS.md](#section-10)
11. [SYMMETRY_RECIPROCITY_AND_GAUGE.md](#section-11)
12. [ONE_SHOT_INVERSE_THEORY.md](#section-12)
13. [NOVELTY_AND_CLOSEST_PRIOR.md](#section-13)
14. [THEOREM_AND_COUNTEREXAMPLE_LEDGER.md](#section-14)
15. [ROUTE_COMPARISON_AND_DECISION.md](#section-15)
16. [MINIMAL_DECISIVE_EXPERIMENTS.md](#section-16)
17. [CODEX_A23_EXECUTION_SPEC.md](#section-17)
18. [SOURCES.md](#section-18)
19. [VALIDATION_AND_READING_GUIDE.md](#section-19)


---

<a id="section-1"></a>

# A23 研究裁决：从 OPM 标签转向可计费的 Maxwell 少次材料反演

日期：2026-10-08。本文可独立阅读。对象是 full-wave 三维矢量 Maxwell inverse scattering；目标是材料成像质量与 total time-to-image，不是 current ranking、current exchange 或更准确的 frozen GN step。

## 一、最终结论

**PRIMARY：不要求保留 O/P/M 的 projection-first、curvature-budgeted、one/few-pass material inverse。**

先用已知参考介质的物理传输构建低成本线性材料 decoder；再检验一次明确的相对反馈修正是否值得支付。A23 的首轮不训练 NN，不运行 diffusion，不把32Dchart内部恢复包装成完整影像。

**SECONDARY：analytic Bayesian / Gaussian mixture / 一次结构 prior correction。** 若无 NN 已达到目标，就停在这里。

**HIGH-RISK / HIGH-REWARD：Maxwell 曲面上的 prior completion。** prior/小NN生成弱结构后，解析补偿它对可靠测量产生的二阶反馈；概率版本必须处理 posterior density，不只是投影得到一张图。

**停止：** learned current ranking/proposal、learned full resolvent、单纯OPM-token网络、用新GNfidelity实验延续旧主线、缺少多模态headroom的Flow训练。

## 二、这轮实际完成了什么

读取 A20/A22-R1 repo 的实际 Schur/seed/backend/极化率代码，固定至
`migodam/a20-opm-imaging@b85a29a51f4ea7b4d93617e827d88e23933b89df`；
A22初始handoff按用户指定commit读取。并核对A18-B/A18proposal/A19原始结论、用户教材相关章节及30项外部论文/来源。

给出六类条件理论、反例、完整复杂度/先验/架构比较和未来Codex执行规范。运行独立8cell、24complex-current、16real-material的CPU验证；没有重跑上游大实验、没有训练网络、没有做临床或盲测成像。

引用ID见 `SOURCES.md`；正文数学是本轮推导，不意味着被引论文已经证明同一组合。

## 三、先纠正现有证据的含义

A20的earlyGN较准/late较差是frozenstep证据，正式closed-loopimaging未进入。[P04] A21双侧oracle恢复optimum，并非线上少次成像。[P06]

A22-R1三个规则选出同一材料空间，没有证明O/P/M标签比同一reducedJ的SVD更有独立信息。[P08] 原复杂材料的chart内能量覆盖：Gaussian约46–49%，asymmetric约5.8%，shell约13.4%。剩余chart外材料仍会影响真实测量。[P09]

原OPM构造约1.5–1.8秒，cachedQP/读入kernel毫秒级，另外还有geometry/reference等；完整同质量time-to-image尚未建立。[P10] 因此现在不能以“现成OPM已经很快”作为起点。

A18-B的analyticpolynomial与完整certificate/fallback费用、A19的实际cost结果，都是不能简单再上NN的正当理由。[P11–P13]

## 四、最重要的五个数学/计算发现

### 1. P 在正确 reference anchor 下可以精确消失

实际P不是泛指“传播”，而是 \(Kb_s\)。令
\[
R_U=U(U^*LU)^{-1}U^*,\quad K=(I-UU^*)(I-LR_U).
\]
若已知参考材料的全部照明电流 \(L^{-1}b_s\) 都在U中，且小core可逆，则
\[
\boxed{Kb_s=0.}
\]
这是可执行的删除规则；参考解本就用于B，不需truthoracle。它不表示materialtangent也精确，更不表示所有P/M在相同degree下重复。

一般P/M包含关系需要fullmaterial方向 \(h_\star=a/a'\)、完整多源注入及一个degree shift；有retainedU时还需处理ΠFU coupling。旧32Dchart或rankcap可能破坏条件。

### 2. 可以先省算，再讨论复杂网络

原程序已缓存FU/F*U，却在K/T及伴随操作里再次调用L/L*。利用LU=U−FU与L*U=U−F*U，可以精确改成小core+缓存乘法。原六源O4/M4/Pforcing的seed形成阶段可删54个fulloperator vector RHS；不是54倍速度，也不是已经测得walltimegain。

更进一步，
\[
\boxed{J_s=Z^*B_s,\qquad Z=L_b^{-*}S^*.}
\]
可以不构建完整currentbasis，直接生成材料–数据映射。具体采用exactadjoint、randomizedtransfer还是sourceanchoredOM，由同质量实际cost决定。

### 3. 真正的 few-pass inverse 来自“相对材料反馈”

对极化率增量h：
\[
X(h)=L_b^{-1}H(h)e_b,\quad T(h)=L_b^{-1}H(h)G,
\]
\[
\boxed{\Delta j=(I-T(h))^{-1}X(h).}
\]
因此
\[
\Delta y=Ah+Q(h,h)+R_3(h),
\quad \|R_3\|\le \|S\|\frac{\eta^2}{1-\eta}\|X\|,
\quad\eta=\|T(h)\|<1.
\]
线性decoder后只作一次修正：
\[
h_1=D\Delta y,\qquad h_2=h_1-D\hat Q(h_1,h_1).
\]
无噪声、精确leftinverse/fullchart下误差由二阶变三阶；有noise/regularization/charttruncation时必须保留bias与放大项。

**这不是首次inverseBorn。** 相关电磁收敛和second-degree方法已有先例[R04–R05]。A23机会在便宜构造、有效压缩、参数化一致与实际fullimage/time优势。

### 4. 不能把所有“二阶新信息”叫 Maxwell feedback

原backend用非线性极化率 \(a(\chi)\)，故
\[
Q_\chi(u,v)=Q_a(a'u,a'v)+\tfrac12J_a(a''uv).
\]
前者是重复散射，后者是局部constitutivecurvature。单频完整复cell材料、a'可逆时，后者在fulltangentrange内；投影到完整tangent的法向后只剩feedbackcurvature。

但有两个重要反转：
- fullJ满行rank时法向空间为零，根本没有额外data维数可增加；
- 32Dchart/稳定截断tangent会让localconstitutive项看起来像“新曲率”。

所以要分别报告local、feedback、chart和nuisance，而不是再提出一个总分描述子。即使没有新data方向，二阶inversecorrection也可能改善原data空间内的成像；不因此立刻杀掉整个方向。

### 5. 物理–先验分离应是曲面，不应固定 hard split

若强/弱坐标为a,b，稳定线性关系 \(U_s^TA V_s=\Sigma_s\)，给定prior提出b后：
\[
a_2=a_0-\Sigma_s^{-1}U_s^TQ(V_sa_0+V_wb,V_sa_0+V_wb).
\]
局部强测量误差降到三阶。它保护的是测量支持，而不是锁死原a的数值。若网络生成chart外结构，相应Q必须支持这些方向。

概率版本还需先验cross-covariance、likelihood和fibreJacobian；单纯“生成b+投影a”并不自动是正确posterior。[R14–R15为直接近邻]

## 五、统计压缩的明确目标

对白化Gaussian模型 \(z=f(x)+\epsilon\)，固定线性压缩P遗漏mean variation的平均平方，控制后验信息损失：
\[
\mathbb E_z KL(p(x|z)\Vert\tilde p(x|z))
\le \tfrac12\mathbb E_x\|(I-P)(f(x)-f_0)\|^2.
\]
二阶近似的最小**线性充分空间**是span[A,Q]，不只是span[A]。精确保留一阶二阶、半径ρ内remainder三阶时，预算为Oρ6；遗漏二阶通常Oρ4；有固定lineartruncation则不能继续声称Oρ6。

可以用Gaussianquadraticprobes估计二阶response范围而不建p²tensor，且利用cachedreceiveradjoint取消Q的outerfullsolve。此处先验加权和随机化都是计算工具，不会增加原测量的Fisher信息。

## 六、本轮最小验证：有正面结果，也有成本警告

独立8cell3DvectorDDA，6源，18个三分量接收位置，共648实数据。参考L条件数约1.189，最大relativefeedbacketa约.0134；这是小相对扰动，不是强散射部署benchmark。

| 检查 | 实际结果 |
|---|---:|
| cachedSchur等价 | 相对误差约1.6–2.1e−16 |
| sourceanchoredP | 3.62e−16 |
| firstinverseerror阶 | 1.99991 |
| secondinverseerror阶 | 2.99985 |
| linearstat维数 | 16 |
| fullquadraticjet维数 | 88 |
| Gaussianweighted二阶增量90%/99%energy | 12 / 26个方向 |

最后两行非常重要：二阶统计保留可能比一阶贵很多。压缩是否划算必须实测。额外algebrachecks还验证了basisgauge与A9被动极化率圆盘，但这些都不是成像质量证据。

## 七、医学/工业定位

首选：固定几何、已知/可重复参考、差分材料变化的监测。例子包括受控工业检验、thermal/differentialsensing研究。理由是绝对背景可复杂，但相对h可能小且N大，满足理论和摊销条件。

未知患者全头/全乳房定量one-shot不应当作首个claim。2026patient-specificheadbackground工作本身仍需形状/皮肤脂肪先验并以phantom验证；2025subspace温度监测已有直接先例。[R23,R25] EIT/DOT/ultrasound的概率/压缩思想可借鉴，物理算子不能不加论证移植。

## 八、只验证三个决定性假设

H1：sourceanchoring/cache/adjoint/randomized能否在同quality下减少真实encoder准备成本。

H2：扣除localconstitutive与chart/nuisance后，finitefeedback是否改善fullmaterialimage；与dressedlinear、linear-a、vanillaIBS2、genericSVD比较。

H3：noise/calibration下是否有totaltime/qualityPareto优势，包含paidfullvalidation、fallback、setup和N次摊销。

未来建议pilot≤2GPU小时，先CPU/小矩阵；四个历史对象、三幅度、zero/nominal20dBnoise作为feasibility。完整预算和关键fullvalidation范围见独立 `CODEX_A23_EXECUTION_SPEC.md`。本轮未启动这个pilot。

## 九、对任务书12个问题的直接回答

| 问题 | 裁决 |
|---|---|
| 1. O/P/M独立吗？ | 不构成三个独立统计信息源；是具体seed/dual构造，P可为零。 |
| 2. P/M能合并吗？ | sourceanchor可删P；一般需hstar可表达、全源保留、degree shift及retainedcoupling条件。 |
| 3. 能绕开完整OPMbasis吗？ | 能，J=Z*B与projection-first/sketch可直接构造transfer。 |
| 4. 大规模究竟省什么？ | 重复传播、outersecond-ordersolve、无用seedactions；不省任意fullimage输出、未知background或验证成本。 |
| 5. 哪些场景利于摊销？ | 固定几何、重复reference的小变化；未知个体/姿势重建不自动可摊销。 |
| 6. 能显著优于Born/SVD吗？ | 可能优于一阶physics；不会仅凭OPM标签优于相同A的最优SVD。必须与dressedBorn/IBS2比较。 |
| 7. Feedback能决定NN吗？ | 能决定explicitbilinearresponse、真实adjoint、gauge和recoil；不能证明NN必需或信息更多。 |
| 8. 不用NN的更好方法？ | 首选解析linear/二阶decoder，辅以Wiener/GMM/wavelet等。 |
| 9. Bayesian/Flow怎么接？ | 接明确compressedlikelihood与prior；处理correlation、density/Jacobian，只有真实多模态才上生成。 |
| 10. 能量/互易/对称能省算吗？ | 可复用场/矩阵、保证gauge与廉价物理投影；不能把L当SPD或固定阵列当object-SE3不变。 |
| 11. 最强TAP组合？ | relativefeedback机制+参数化/归因一致曲率+cost-awarefew-passinverse+fullimagePareto实证。当前尚非已完成强TAP成果。 |
| 12. 少量GPU先验证什么？ | H1计算最小性、H2真实非线性fullimageheadroom、H3总时间质量竞争。 |

## 十、最终投入建议

把下一轮资源集中在 **A23 analytic engine**，不要分散到四种NN/Flow路线。更便宜的adjoint/SVD若获胜，就让它成为engine；二阶有用而jet过贵，就只留少passcorrection；非神经prior够用，就不训练NN。

本轮最有价值的推进，是把“OPM可能是一种好特征”变成了**可证明哪些动作能删、可量化哪些有限幅度响应不能丢、可检验先验补全如何影响数据**。接下来需要的是决定性fullimage/cost证据，不是再增加一个机制分数。



---

<a id="section-2"></a>

# A23 记号与假设

本包研究有限维、固定频率的三维矢量 Maxwell DDA/VIE。原始实现来自 [P01–P03]；新增推导不等于连续 Maxwell 的网格误差证书。参考文献 ID 见 `SOURCES.md`。

## 1. 四种不同的空间

- 电流：\(j_s\in\mathbb C^n\)，\(s\) 为照明编号。本文公式以未缩放 dipole 为主；代码用 \(c_s=j_s/\sqrt v\)，须成套变换 \(B,S\)。
- 材料：\(x\in\mathbb R^p\)，通常是复介电常数的实部与虚部；或极化率的实部与虚部。物理 \(L^2\) 质量度量先归一，不能把 cell 值和归一坐标混用。
- 测量：复数多源接收场先按原代码 pack，再按实际噪声协方差白化，得到 \(y\in\mathbb R^m\)。\(m=2sq\)，若 \(q\) 表示每源复接收通道数。
- 统计压缩：\(U_y\in\mathbb R^{m\times k}\)，\(U_y^TU_y=I\)。它不是电流空间 \(U\)。

\(^*\) 为复共轭转置；纯实材料/白化测量坐标用 \(^T\)。任何复物理链的材料伴随，都要接上实坐标 pullback。

## 2. 前向算子和局部表示

\[
j_s=a(\chi)(e_s^{inc}+Gj_s),\quad
L=I-a(\chi)G,\quad b_s=a(\chi)e_s^{inc},\quad y_s=Sj_s.
\]

\(a(\chi)\) 表示每 cell 的标量极化率，作用于三个矢量分量。\(G\) 含 off-diagonal dyadic coupling，self term 在极化率内。

\[
J_s=SL^{-1}B_s,\quad B_s\delta\chi=a'(\chi)\delta\chi\,e_s.
\]

参考点用下标 \(b\)；\(\Delta y=y(\chi)-y(\chi_b)\)，不沿用优化器的 \(r=y_{\rm predicted}-y_{\rm measured}\) 符号，否则 one-shot decoder 会反号。

## 3. Schur 表示

\[
\Pi=I-UU^*,\quad A_U=U^*LU,\quad R_U=UA_U^{-1}U^*,
\]
\[
K=\Pi(I-LR_U),\quad T=(I-R_UL)\Pi,
\]
\[
F_{\rm eff}=\Pi F\Pi+\Pi FU A_U^{-1}U^*F\Pi,\quad F=I-L.
\]

本包的 \(K\) 是 Schur 注入，不是某篇旧文的 current tangent。\(A_U\) 也不是材料 Jacobian \(A\)。

## 4. 二阶材料响应

白化后的局部材料响应写成
\[
f(x)=f_0+A x+Q(x,x)+R_3(x).
\]
\(Q\) 是对称双线性映射，已包含 Hessian 的 \(1/2\)；因此
\[
D[Q(x,x)]h=2Q(x,h).
\]
\(Q\) 不是电流 basis，也不是原 Gaussian chart。材料图用 \(W\)，电流 basis 用 \(U,V\)，数据 basis 用 \(U_y\)。

## 5. 每个结论的假设

“精确”：针对指定有限维算子，在矩阵可逆等写明条件下的代数恒等式。

“条件界”：还需算子范数、材料半径、可容许集、谱间隙或稳定 decoder。不能把随机 probe 的小残差当作全空间确定性上界。

“实证”：本轮只有独立 8-cell、24-complex-current 的 CPU 检查；不是原 A22 replay，不是强散射成像验证。

“待验证”：新 A23 成像质量、总时间、盲测泛化、临床适用性、网络/后验校准、最优路线的计算优势。

线性/二阶 sufficiency 的 projector 必须在本次未知测量之前固定，或条件于与本次噪声独立的离线资料。数据自适应构基的统计选择效应不能省略。

## 6. 两个不同的“强散射”

绝对对象可以与自由空间相差很大；相对参考对象的扰动仍可能很小。有限幅度展开由
\[
\eta(h)=\|L_b^{-1}\operatorname{diag}(h)G\|
\]
而不是仅由 \(\|\chi\|\) 控制。已知强背景、小变化是优先应用；未知高对比全对象不是同一保证。

被动性约束施加于绝对材料。相对于有耗参考背景的 contrast 虚部不一定非负。跨频时 \(L_f,S_f,B_f,a_f\) 都随频率变化，不能复用单频公式而删除频率索引。

## 7. 统计与先验

白化后标准 Gaussian 噪声只用于明确写出的概率命题。实际非 Gaussian/相干标定误差要另建 likelihood。Gaussian 材料 probe 用于局部二次映射的矩；不要求这些 probe 被当作有限幅度物理对象送入 Maxwell。

\(V_{\rm phys}/V_{\rm prior}\) 只是相对于指定模型、先验度量与噪声的局部划分；不等于绝对可识别/不可识别，也不等于后验独立。



---

<a id="section-3"></a>

# O/P/M 冗余、最小实现与删除条件

**结论：O/P/M 是有用的构造标签，但不是三个不可约的物理信息源。实际代码允许精确删除某些 P；一般 P/M 合并有明确的次数与 retained-coupling 代价；O 可以被直接伴随传输替代。** 未证明低 current rank 必然带来更低成像时间。

来源：[P01–P03] 是实际实现，[B01] §6.4 为 SOM/TSOM 先例，[R09–R11] 为通用压缩和双侧误差理论。新推导与可测预测在下文分别标明。

## 1. 实际 seed，而不是按名称猜测

令 \(\Pi,A_U,R_U,K,T,F_{\rm eff}\) 如 `NOTATION_AND_ASSUMPTIONS.md`。源码 `build_seeds` 的原始块为
\[
M_{\rm raw}=[KB_s v_i]_{s,i},\quad
P_{\rm raw}=[Kb_s]_s,\quad
O_{\rm raw}=[T^*S^*w_{s,i}]_{s,i}.
\]

M 的 \(v_i\) 是实材料 probe，存在历史 accepted step 时首列可能替换为该步；O 的首个 probe 是当前测量残差，其余是白化数据 probe；P 使用全部**已知照明 forcing**。每族先合并所有源，再 SVD 截为配置的 seed rank。原配置每族四列，并非每个源四列全部保留。[P01]

记截断后的种子为 \(M_0,P_0,O_0\)。实际 chains 是
\[
\mathcal K_M(d)=\operatorname{span}\{F_{\rm eff}^jM_0:0\le j\le d\},
\quad
\mathcal K_P(d)=\operatorname{span}\{F_{\rm eff}^jP_0:0\le j\le d\},
\]
\[
\mathcal K_O(d)=\operatorname{span}\{(F_{\rm eff}^*)^jO_0:0\le j\le d\}.
\]
各族独立 Arnoldi，再联合正交化；不是单个共同三项递推。对 raw seeds 的包含关系不能自动转给被 rank-cap 的实际 seeds。

## 2. T1a：source-anchored retained space 使 P 精确消失

**命题。** 在固定参考材料、固定几何与频率，\(L\) 与 \(A_U\) 可逆。若全部参考电流
\[
j_{b,s}=L^{-1}b_s\in\operatorname{Range}U,
\]
则 \(Kb_s=0\)，所以所有 P chains 都为零。

**证明。** 写 \(j_{b,s}=Uc_s\)。则 \(U^*b_s=A_Uc_s\)，故 \(R_Ub_s=Uc_s=j_{b,s}\)。代入 \(Kb_s=\Pi(b_s-LR_Ub_s)\) 即得零。没有弱散射或 Hermitian 假设。

**实现意义。** 原 M 的构建本就需要参考 exciting fields；这些已付费参考解可先放进 \(U\)。六源时参考电流 span 的 rank 不超过六，可在固定 retained rank 预算内与 observation vectors 联合。这里使用已知参考背景，不使用未知真对象电流，不是 A21 oracle。

**近似版。** 若 \(\hat j_s\in\operatorname{Range}U\)，\(r_s=b_s-L\hat j_s\)，则
\[
Kb_s=Kr_s,\qquad \|Kb_s\|\le\|K\|\|r_s\|.
\]
在已知 \(\|(I-F_{\rm eff})^{-1}\|\) 时，还能约束删除 P 对 state response 的影响。只有残差小、没有 resolvent 上界时，不能宣布物理响应误差小。

**边界。** \(L\) 可逆不保证 \(U^*LU\) 可逆。例如 \(L=\begin{bmatrix}0&1\\1&0\end{bmatrix},U=e_1\)。原 core guard 必须保留。采用稳定 Petrov 测试空间可以研究，但必须重新推导，不能悄悄加 ridge。换参考材料或照明后 P 可重新出现。P 消失仅表示 forcing 已在 retained part 中，不表示材料切线或 full image 已被精确表示。

**预测。** 源电流锚定、固定参考点下，P raw norm 接近参考解残差/舍入；继续生成 P chain 不应增加 rank。本轮 tiny 检查为 \(3.62\times10^{-16}\)，仅证明该实现示例。

## 3. T1b：P/M 合并存在一个明确的 degree shift

先取 \(U=0\)，考虑全复 cell 材料的 \(2N\) 实坐标。若 \(a'_i\ne0\)，定义
\[
h_{\star,i}=a_i/a'_i.
\]
由 \(B_s h_\star=a'e_s h_\star=a e_s=j_s\)，得到
\[
b_s=(I-F)B_s h_\star.
\]

若实际 M seed span **保留了所有源的** \(B_sh_\star\)，则
\[
F^j b_s=F^jB_sh_\star-F^{j+1}B_sh_\star
\quad\Longrightarrow\quad
\mathcal K_P(d)\subseteq\mathcal K_M(d+1).
\]

这不是“P 永远等于 M”。它要求：
1. material chart 能表达 \(h_\star\)；
2. 多源 current block 没有在 M 的 SVD cap 中丢掉这些向量；
3. 增加一层 M 的真实 actions 不超过删除 P 所节约的成本；
4. \(h_\star\) 在声明的实材料自由度中合法。固定 loss 或受限 dispersion 参数下不能任意使用复方向。

特别是 32D Gaussian chart 一般不满足第一点；原随机四列不满足第二点。A20-R1 已显示“材料方向在 probe span”仍可在多源 current compression 中丢失，不能跳过此层。[P05]

## 4. 有 U 时为什么不能照搬上一结论

令 \(H_U=\Pi FU\)、\(a_h=A_U^{-1}U^*B_sh_\star\)。可直接验证
\[
KL=(I-F_{\rm eff})\Pi,\qquad
\Pi B_sh_\star=KB_sh_\star-H_Ua_h.
\]
于是
\[
Kb_s=(I-F_{\rm eff})(KB_sh_\star-H_Ua_h).
\]

所以 P 的 descendants 可由 M 与 retained-complement coupling \(H_U\) 的 descendants 联合产生。**只删 P、不补这个 coupling、也不验证 source anchoring，是不成立的简化。** 若 \(H_U\) 已被 M closure 覆盖，才恢复包含结论。source-anchored 条件则更强，直接使左侧为零。

这是实际代码可用的三种 policy：source anchoring 后删 P；保留 coupling seeds 后与 M 合并；或保留原 P 作为 matched-budget control。没有理由先验只选第三种。

## 5. 什么量才能证明“可删除”

正交 bases \(Q_M,Q_P\) 的交空间维数由奇异值为 1 的 \(Q_M^*Q_P\) 给出；数值实施需要冻结容差。联合 rank 为
\[
r_{MP}=r_M+r_P-\dim(\mathcal K_M\cap\mathcal K_P).
\]
主角 \(\theta_i=\arccos\sigma_i(Q_M^*Q_P)\)，增量残差
\[
E_P=(I-Q_MQ_M^*)Q_P.
\]

这些只是 current Euclidean 几何。实际删除判据应再含：
\[
\|S(L^{-1}-R_{\rm reduced})B W\|,
\quad
\|(L^{-*}-R_{\rm reduced}^*)S^*U_y\|,
\]
以及 decoder 放大后的
\[
\|D\,S(L^{-1}-R_{\rm reduced})B W\|.
\]
\(W,U_y,D\) 必须是独立于 truth 的任务/噪声定义。不能由 principal angles 推出这三者小。

**反例。** \(L=\operatorname{diag}(1,\varepsilon^2)\)，被删 seed 为 \(\varepsilon e_2\)，\(S=e_2^T\)。seed 欧氏残差仅 \(\varepsilon\)，输出是 \(1/\varepsilon\)。近共振与非正规放大正是这类遗漏风险。

**近似充分条件。** 对实际待替换的 RHS \(g_P=g_M+e\)，
\[
\|S L^{-1}(g_P-g_M)\|\le\|S L^{-1}\|\,\|e\|.
\]
这是 RHS 替换界，不是两个不同 Galerkin 空间任意变化的误差界。后者还要 projected core 稳定性与投影一致性。

## 6. O 是否独立

物理统计信息只在同一个测量 likelihood 中。O 是对偶方向的计算探针，不会比精确 J 增加 Fisher information。[P07–P08]

若缓存 \(Z=L^{-*}S^*\)，则 \(J_s=Z^*B_s\)，O 的整个用途可转化为 data-to-material pullback，不需要再显式建 observation current Krylov chain。若不缓存完整 Z，用少量对偶 probe 可以改善输出精度，但其必要性取决于误差/预算，不是三标签公理。

A21 的 primal+dual oracle 保住 GN optimum，解释了两侧近似的重要性；不证明双 stream NN 的统计信息比单个精确 transfer 多。[P06]

## 7. 场景分类

| 场景 | 可合理预期的简化 | 必须检查 |
|---|---|---|
| 弱相对散射，参考解已知 | source-anchor P 消失；低 degree 近似 | reference residual、噪声尺度 |
| 大绝对背景、小变化 | P 可消失；对参考 resolvent 做相对反馈 | 不是自由空间 Born，参考成本单列 |
| 强非正规反馈 | M/P 欧氏 overlap 不可靠 | task-weighted residual、core inf-sup |
| 近共振 | 很小遗漏也可产生大响应 | resolvent/小核心极点，拒绝而非隐蔽 ridge |
| 近接触 | 高局域耦合可能需细网格/更多方向 | DDA discretization 和实际质量 |
| 多频 | 单频分别 source-anchor，可能复用近似空间 | 每频 L/S/B、dispersion、传输误差 |
| 换接收几何 | forcing anchor 可保留，Z/S 变化 | source 改变则参考电流也可能需重算 |

## 8. 最小什么，而不是只追求最小 rank

固定频率的 transfer 可以直接压成材料–数据矩阵；动态 moment realization 的最小阶数则与可控可观 Hankel rank 有关。二者不同：静态 \(J\) rank 小不说明多个频率/多个反馈 degree 共享同一小 realization。

最强可执行结论不是“OPM→OM 一定赢”，而是：
\[
\boxed{\text{先删代数上无用的动作与 P，再竞争 direct adjoint / OM / randomized transfer。}}
\]
所有 arms 必须计入 source RHS、QR、参考解、receiver contraction、memory 和下游同质量重建时间。本轮没有完成这些实际 A23 Pareto 比较。



---

<a id="section-4"></a>

# 廉价反馈算子：从代码中可删的动作到不建 current basis 的实现

本文件是算法设计，不是已完成的速度 benchmark。记号见 `NOTATION_AND_ASSUMPTIONS.md`，源码证据 [P01–P03]。

## 1. 四个 Schur 算子可以直接复用缓存

源码已存 \(FU,F^*U\)。令
\[
C=LU=U-FU,\qquad C_H=L^*U=U-F^*U.
\]
原式可以**精确**重写为
\[
Kv=\Pi(v-C A_U^{-1}U^*v),\qquad
Tv=\Pi v-U A_U^{-1}C_H^*\Pi v,
\]
\[
T^*v=\Pi(v-C_H A_U^{-*}U^*v),\qquad
K^*v=\Pi v-U A_U^{-*}C^*\Pi v.
\]

证明仅使用 \(U^*L=C_H^*\) 及 \(U^*L^*=C^*\)。没有近似、谱假设或新训练。每个 block 的成本从额外 full \(L/L^*\) action 变成小 LU solve 和 \(O(nr_0b)\) 乘法，\(r_0=\dim U\)。

原 seed 的六源、M4、O4、P forcing 配置中，K(M) 为 24 RHS、K(P) 为 6 RHS、T*(O) 为 24 RHS：**seed 阶段可删除合计 54 个 full-operator vector RHS**。这不是 54 个 kernel launch，不包括原始 B/S*、FU/F*U、QR、后续 LQ 与 receiver contractions，也不意味着 time-to-image 固定减少某个比例。

若固定参考的 source anchor 使 P 为零，还可免去 P 的压缩和扩展。必须分别记录“代数消除”和“近似删减”两类节省。

## 2. 直接伴随 pullback：不必先建立 OPM

参考材料处解
\[
L_b^* Z=S^*,\qquad J_s=Z^*B_s.
\]
这把 current-to-data 双侧传输直接变成接收伴随场与局部材料注入的 contraction。\(B_s\) 为局部场乘法时，所有材料 cell 的线性灵敏度可通过点积得到，不需要每个 cell 一次 full solve。

每频准备成本：
- 参考 exciting field：\(s\) 个前向 RHS；
- 全接收伴随：\(q\) 个 RHS，而不是 \(sq\)，因为同一 L/S 可跨 source 复用；
- 对 \(k_x\) 个材料方向的 primal-only alternative：\(s k_x\) 个 tangent RHS。

选择参考总 RHS 约 \(s+\min(q,sk_x)\) 的方法还不够，必须比较 contractions、cache \(nq\) 与 block solve 的硬件效率。若天线发射/接收模型随 source 改变，或 L 也改变，该共享不成立。

**实材料处理。** 用 \(B^*\) 时按源码先对三个矢量分量及所有源求复内积，再做 real material pullback，最后应用质量坐标。对白化后的任意数据压缩向量 \(u\)：
\[
J^T u = B_{\mathbb R}^* L^{-*}S^* W_{\rm noise}^T u.
\]
不要把 transpose whitening 写成 inverse whitening。

## 3. Projection-first 的两种合法方式

**材料优先：** 给一个与 truth 无关的全图多尺度 \(W\)，先取 \(AW\)，再做稳定解码。它保留 prior/representation 条件；若 W 很小，不能宣称 full-image recoverability。

**测量优先：** 先取独立于本次噪声的 \(U_y\)，计算
\[
A_c=U_y^T J,\quad z_c=U_y^T(y-y_b).
\]
可以用 \(J^TU_y\) 构建，不存完整 J。任意 source-mixed \(U_y\) 的每列可能需要 \(s\) 个伴随 RHS；不要误写成仅 \(k_y\) 次物理 solve。可分离的 source/receiver sketch 更便宜，但需要验证损失。

默认推荐 full-voxel/多尺度 prior-conditioned 算子，而非继承 truth-dependent Gaussian support。在线输出可以是 \(p\times k\) 的低秩材料 decoder，仍须计 \(O(pk)\) 内存/乘法和完整图像输出。

## 4. 双侧 defect：什么时候可以获得乘积误差

对任意近似解 \(\hat X\approx L^{-1}B,\hat Z\approx L^{-*}S^*\)，定义
\[
H_c=S\hat X+\hat Z^*(B-L\hat X).
\]
则
\[
H-H_c=(S-\hat Z^*L)L^{-1}(B-L\hat X),\qquad H=SL^{-1}B.
\]

**证明。** \(H-S\hat X=SL^{-1}(B-L\hat X)\)，再减去 correction 即得。于是输出误差为 primal residual 与 dual residual 的乘积；这是 DWR/goal-oriented reduction 的已知思想 [R11]，不是 A23 新创造。

**重要修正。** 对未加 correction 的 \(SR_AB\)，
\[
J-SR_AB=(S-SR_AL)L^{-1}(B-LR_AB)
\]
并非对任意 \(R_A\) 成立。展开右侧是 \(J-2SR_AB+SR_ALR_AB\)。需要 \(R_ALR_A=R_A\)，Galerkin inverse 满足该条件；任意 learned closure 通常不满足。标量 \(L=S=B=1,R_A=1/2\) 时真 defect 为 \(1/2\)，错误双侧式给 \(1/4\)。本轮数值反例已保存。

## 5. 保留 direct path 和相干交叉项

精确 Schur transfer 为
\[
J=SR_UB+(ST)(I-F_{\rm eff})^{-1}KB.
\]
在 complement 取多项式 \(p_d\) 时
\[
\tilde J=J_{\rm direct}+(ST)p_d(F_{\rm eff})KB.
\]
若计算 information/Gram，必须包括
\[
\tilde J^*\tilde J
=J_d^*J_d+J_d^*J_f+J_f^*J_d+J_f^*J_f.
\]
把各族“能量”加起来会丢掉相消、相长和相位，不能用于等价解码。

不一定保存全 Q；可保存 moments \(H_j=(ST)F_{\rm eff}^jKB\)、投影 Gram 或小 transfer core。省 Q 后是否重复传播取决于后续需要哪些新输入，不能只比较文件大小。

## 6. 非正规反馈下的 polynomial / Krylov / rational

Neumann 截断的恒等误差是
\[
(I-F)^{-1}-\sum_{j=0}^dF^j=(I-F)^{-1}F^{d+1}.
\]
\(\|F\|<1\) 给几何上界；只有 \(\rho(F)<1\) 不能给统一的小 degree 误差。反例 \(F=\begin{bmatrix}0&100\\0&0\end{bmatrix}\) 的谱半径为零，但 degree0 resolvent error 为 100。可有有限次幂后精确，并不代表浅层已准确。

Block Arnoldi/FOM/GMRES 有稳定正交化和残差监测，但不承诺固定小次数；双侧 Krylov 可能有 breakdown，必要时 look-ahead/重新正交化也有成本。不可对非 Hermitian F 使用自伴随正交多项式的三项递推。

Rational Krylov/Padé 可在近共振区更有效，但 shifted solves、pole selection 和在线条件数都要计入。forward Padé 的先例 [R29] 不提供 inverse decoder 的稳定保证。本轮不开发新的 GMRES/PCG 求解器。

## 7. 二阶反馈的便宜计算：共享内层解

在极化率增量 \(h\) 下，
\[
X(h)=L_b^{-1}H(h)e_b,\quad A h=SX(h),
\quad Q(h,h)=S L_b^{-1}H(h)G X(h).
\]
若已缓存完整接收伴随 \(Z=L_b^{-*}S^*\)，则
\[
Q(h,h)=Z^*H(h)G X(h).
\]
一个 probe 的线性和二阶响应共享 \(X(h)\)，外层 solve 被一次 contraction 代替。这不是 learned resolvent，也不是再次 GN。

K 个全源 probe 的 RHS 对比：
\[
C_{\rm primal}: s+2Ks,\qquad
C_{\rm dual}:s+q+Ks.
\]
在相同准确性下，单看 RHS 的 crossover 是 \(q<Ks\)；wall clock 还取决于传播 \(G X\)、矩阵乘法和 cache。

**不能省掉的限制。** 若 Z 只对应旧线性 data range，就无法发现垂直于该 range 的二阶新响应。要发现新空间，需全接收 Z、独立观察 sketch，或支付 outer propagation。不能先投掉 innovation 再报告“没有 innovation”。

## 8. Gaussian quadratic probes 与 streaming

对 \(Q(x,x)=\sum_{ij}q_{ij}x_ix_j\)，\(q_{ij}=q_{ji}\)，\(g\sim N(0,I)\)：
\[
\mu_Q=\sum_iq_{ii},\quad
\operatorname{Cov}[Q(g,g)]=2\sum_{ij}q_{ij}q_{ij}^T.
\]
因此可通过随机材料方向及其 \(Q(g,g)\) 做 centered range finding，加回 \(\mu_Q\)，而不形成 \(m\times p^2\) tensor。完整证明见 Bayesian 文件。

这是“二阶 transfer 的统计 range”，不是新增观测信息。小 sample 估计缺失 weak方向是可能的；独立 probes 用于评估。非 Gaussian prior 应按其四阶矩或实际 prior probes 重建权重。

不要用纯 Rademacher directions 替代所有 Gaussian directions：\(g_i^2=1\) 会让不同 diagonal quadratic terms 混成一个方向。需要 Gaussian、显式坐标 probe 或专门四阶设计。

## 9. 低内存执行合同

按 frequency、receiver-block、source-block 流式；按需磁盘保存可复用背景场；所有 I/O 单列。若不存 Z，只能重算或降低 receiver rank，没有零成本第三种选择。

禁止大规模部署继续读取 `_operator_L` 的 dense Frobenius norm。可改用已证明上界、可支付的 norm estimation，或明确标记经验 stability guard；不能把随机 norm estimate 当作严格确定性尺度。`compressed_B` 的 \(s r p\) 数组须按材料块构造或隐式作用。

最终必须与直接背景 adjoint、普通 randomized J、POD/ROM 在相同物理 RHS 和同图像质量下比较。[R09–R10] 若这些已有方法更便宜，保留其实现，不保留 OPM 名称作为门槛。



---

<a id="section-5"></a>

# 大规模复杂度、实际时间与摊销条件

**结论：OPM 可能节约的是重复物理传输/线性化准备，不是凭空消除 full-image 维数。** 真正有机会的情形是参考背景、几何和频率可重复使用，且有限幅度 decoder 仍达到可接受质量。小 QP 的毫秒时间不是 end-to-end imaging latency。[P10]

## 1. 统一计费变量

每频：n 为复 current unknowns；p 为实材料 unknowns；s 为源数；q 为每源复 receiver channels；m=2sq 为实测量数；r 为 current ROM rank；k 为压缩数据/材料解码 rank。f 为频率数，N 为重复图像数。

令 \(T_{\rm mv}(n)\) 为一列 Maxwell action 成本，\(T_{\rm solve}(n,\epsilon)\) 为给定容差的一列 reference solve。迭代求解约为 \(\nu(\epsilon)T_{\rm mv}\) 加 preconditioner/orthogonalization；\(\nu\) 依赖频率、对比、非正规性、网格，不是固定常数。

密集 DDA 的 storage \(O(n^2)\)、LU \(O(n^3)\)，多 RHS solves \(O(n^2b)\)。规则网格卷积可用 FFT 实现 \(O(n\log n)\) actions；复杂非均匀背景、天线/边界、局部自项与不规则网格需相应 FMM/FEM/积分方程实现，不能把所有场景都记成 FFT。[B01] §2.9 / Appendix D。

## 2. OPM 原版会在哪里失去优势

| 项目 | 量级 / 必须记录 |
|---|---|
| 背景 current / exciting fields | 至少每频 s RHS，另有 geometry/operator setup |
| U 与 Schur cache | \(O(nr_0)\) storage，FU/F*U 共约 \(2r_0\) RHS |
| 原 raw seeds | M/O 含所有 source，rank cap 前的宽度是 \(s b_M,s b_O\) |
| degree 扩展 | 各族存活列数之和的 F/F* RHS，不按一次 block launch 计一次 |
| 联合 QR/SVD | 随实际 n、r、block宽度增长；常见 \(O(nr^2)\) 累积 |
| 投影 core | LZ actions、Z*LZ、factorization \(O(r^3)\) |
| compressed injection | 原 `compressed_B` 可形成 \(s\times r\times p\) 复数组 |
| receiver transfer | \(SZ\)、real packing/whitening，多源 contractions |
| material decoder | \(O(pk)\) memory/work 或 matrix-free 多次 action |
| image output | 至少 \(\Omega(p)\) 写出；读数据至少 \(\Omega(m)\) |

实际 backend 仍持 dense `_operator_L` 并计算其 Frobenius norm。[P01–P02] 因而“算法支持 operator-only”尚不等于现有程序已经大规模 matrix-free。

## 3. 一个内存数量级例子

以下只是明确公式的假想规模，不是本项目运行结果：n=3,000,000，p=2,000,000，s=6，r=64，k=32，q=256，complex128/float64，十进制 GB。

- 一个 current basis \(n r\)：3.072 GB；
- dense compressed B \(s r p\)：12.288 GB；
- material decoder \(p k\)：0.512 GB；
- 全 receiver adjoint cache \(nq\)：12.288 GB；
- 一个 dense L：144 TB，明显不能构造。

因此“只用64个 current modes”仍可能需要多 GB bank 和注入矩阵。Z 全缓存也可能不划算。合理选择包括 receiver blocking、重算、低秩 observation、磁盘 streaming，但各自会增加 compute/I/O 或误差。不能同时假设全部 cache 免费、全部 memory 不存在、所有新 directions 无代价。

## 4. Direct adjoint 与 projection-first 的成本模型

线性参考 transfer 可通过：
\[
S_{\rm primal}\approx S_{\rm geom}+sT_{\rm solve}+sk_xT_{\rm solve}+C_{\rm contract},
\]
\[
S_{\rm dual}\approx S_{\rm geom}+sT_{\rm solve}+qT_{\rm solve}+C_{\rm contract}.
\]
在 same-L same-S 条件下 receiver adjoint 跨 source 共享。若任意 data sketch 混合源，每个 sketch 可以需要 s RHS；实现必须明示如何拆分。

缓存 D 的 online linear image 为 \(O(mk+pk)\)；若 D 未显式存储，需要相应 prior covariance / iterative regularization actions。小 k 不消除 full p 输出。

二阶方案有两种实现：
1. 在线对 x1 做 \(X(x1)\) reference solve，共 s RHS，再 contraction 得 Q；few-pass 而非零-solve one-shot。
2. 离线对限定 decoder range 建 bilinear tensor，在线 \(O(k_x^2k_y)\)；setup、tensor storage、range 外误差不可省略。

完整 p² tensor 通常不可行；随机/低秩二阶 approximation 需要 report omitted-response budget。

## 5. T3：摊销 crossover

方法 A/B 分别有 setup \(S_A,S_B\)，同一质量标准下每图总耗时 \(t_A,t_B\)。N 张图的总时间：
\[
T_A(N)=S_A+Nt_A,\qquad T_B(N)=S_B+Nt_B.
\]
若 \(t_A<t_B\)，则 A 比 B 快的条件为
\[
\boxed{N>\frac{S_A-S_B}{t_B-t_A}.}
\]
若分子负，A 在所有正 N 已有 setup 优势；若 \(t_A\ge t_B\) 且 \(S_A\ge S_B\)，没有正的 break-even。

**证明。** 直接移项。它是成本会计恒等式，不是独立 strong-TAP 理论贡献。其价值是强制准确填写实际 full-pipeline costs。

加入拒绝/fallback、几何更新和训练：
\[
T_A=S_A+S_{\rm labels}+S_{\rm train}
+N(t_{\rm encode}+t_{\rm decode}+t_{\rm prior}+t_{\rm verify})
+N p_{\rm reject}t_{\rm fallback}+N_{\rm rebuild}S_{\rm update}.
\]
若验证的 full solve 已包含在 fallback 里，避免双重计费。失败、重跑、I/O、GPU synchronization 也保留。

若神经方案训练成本巨大但 online 稍快，必须报告 realistic N 下的净收益；不能只给一个未说明 workload 的理论 N。A18-B 的完整安全/回退路径实际比裸预测贵得多，是现成警告。[P11]

## 6. 四种部署情形

**一次性未知对象。** 参考准备、operator setup、basis全部付费；Born/adjoint/CSI可能更合适。若为每个新对象重新构造 full background，称为“offline”没有意义。

**固定系统、重复对象。** 固定天线和参考背景允许共享。不同对象只改变测量，不等于其真实场和 Jacobian不变；有限幅度误差由相对feedback控制。decoder失效重建须进入有效N。

**几何变化。** 只有receiver变时，G/currentreference可能共享，但S/Z变化；source变时e_b/currentreference也变化；object与系统整体刚体变换可用协变，object-only移动一般不行。需要具体cache invalidation键，而非“同一设备”字符串。

**多频。** total setup/solve对频率求和。频率空间共享只在已验证误差下成立；不同L_f/S_f/B_f、materialdispersion不得合并成一个虚假的频率无关core。commonmaterialprior可减少自由度，不自动减少每频物理actions。

## 7. 固定 geometry 仍不等于原 OPM 可以直接缓存

原 O seed 含当前 residual，随机 seed含parent_id，M可能含previousacceptedstep。[P01] 这些都是 online/data/trajectory依赖。真正离线encoder应冻结reference/source/receiver/material-priorprobes，把新y只放入压缩coefficients，而不是继续声称原data-adaptiveQ是一次setup。

对 self-calibration，unknown source/receiver gains需单独更新或边缘化；若重新白化改变measurementmetric，原TSVD和decoder都可能需重算。

## 8. total time-to-acceptable-image Pareto

预先定义共同可接受集合，例如fullmaterialNRMSE、complexdataresidual、physicalconstraintviolation及实际任务指标的联合阈值。阈值来自研究目标或独立validation，不从test最佳点决定。

每种方法给出Pareto：cold-start time、warm latency、峰值memory、quality、failure/abstentionrate、N=1/10/100的实测/公式摊销。没有达到质量阈值的方法，time-to-acceptable-image记失败/无穷，而不是把最快的错误图作为赢家。

应同时保留无NN baseline、regularization sweep的真实总成本、不同噪声和几何任务。不要拿OPM cached3ms与竞争者geometry+LU+迭代全部成本比较。

## 9. 可证与未证

可证：上述actions消除、RHSsharing、storage公式、break-even条件。

本轮未证：任意大规模3D环境中的wall-timespeedup，强未知背景few-shot成功，临床实时性能，完整decoderbank跨几何转移。下一轮先用真实action账本找到瓶颈，再决定是否扩大。



---

<a id="section-6"></a>

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



---

<a id="section-7"></a>

# 竞争方法的理论和计算审计

本表比较算法类别，不提供虚构的统一迭代次数或跨硬件速度倍率。I为外层迭代数，ν为每个linear/PDEsolve的内部迭代数，K为NN层数或采样步数；均需实测。同类不同实现可有显著区别。出处见 [B01]、[R01–R30]。

## 1. 十五类竞争者

| 类别 | 真正瓶颈 / full solve / J | 迭代与offline | 失败区与A23可能优势 |
|---|---|---|---|
| Born / Rytov / linearized | 已知background下线性operator及regularization；未知background准备另计。J显式或action | cachedinverse可一次乘法；大型线性solve可有ν；SVD可offline | nonlinearphase/currentbias；A23二阶只在额外反馈真实可压缩时有优势 |
| adjoint / BP / time reversal | S*数据传播；fullbackgroundadjoint可需solve，homogeneousGreen可直接 | 一次/fewpass；geometry可缓存 | matchedfilterPSF与幅度bias；小inverse/deconvolution已有，不能只和未经调优BP比较 |
| SOM / TSOM / SOM-Net | currentspace状态/数据equations、Greenactions；不一定每外层fullPDEsolve | SOM/TSOM迭代；SOM-Net固定Kblocks、训练offline | nonradiatingambiguity/representation；A23必须优于现有current-to-material结构而非重命名 |
| CSI | 同时current/material，残差与Greenactions；通常不为每次更新单独求精确fullstate | I次alternating/nonlinearCG等，Green可缓存 | 非凸/初值/收敛；A23可省迭代但不能把CSI误计为I次fullLU |
| DBIM / Newton / GN | 每次更新backgroundfields与sensitivity；Jv/J*v或显式J | I×state/linearizedsolve，部分geometry可reuse | localminimum/大变化/高cost；A23是少步近似，不比相同GN更快的solver |
| full-wave adjoint optimization | 每轮sourceforward+adjoint，checkpoint/memory | I轮；通常不建完整J | 非凸、cycle/modelbias；A23减少在线重复state，但fullimagequality需守住 |
| Krylov / FFT-DDA / fastforward | 加速Lactions/solve，不自行解决materialinverse | 每solveν；preconditioneroffline或更新 | nearresonant/nonnormal/mesh；A23可以使用它们，不是其互斥替代物 |
| projection ROM / POD / reducedbasis | snapshot生成、basisQR、core与onlineparameterassembly | expensiveoffline，cheaprepeatedcore；可需adaptiveenrichment | reference/parameterOOD；A23sourceanchoring/jet仅是候选改进，通用goal-awareROM是强对照 |
| randomizedSVD / TSVD / LIS | J/J*probes、SVD、priorweighting | lowrankprep可offline；LIS可需posterioraveraging | tail误差/固定linearization；同一A同一prior下SVD不会因缺OPM标签更差 |
| directinverse / EBA / inverseBorn | 已知解析approximation、transfer/rationalinverse、nonlinearseries | 非迭代或少项；core/coeff可offline | poles、observability、seriesradius；A23二阶与其直接重合，必须comparevanillaIBS2 |
| deepinverse-scatteringNN | labels/training、fullimagedecoder；inference可无fullsolve | offline成本高，online固定K | trainingfamily/geometrycalibrationOOD；A23explicitresponse可能省labels/解释failure，尚未实证 |
| neuraloperators / encoderdecoder | operatortraining、resolutionmemory、geometryencoding | amortizedfixedK或spectrallayers | 训练distribution与新operator；不能借FNO原论文非Maxwell速度作对照 |
| PnP / RED / learnedprox | 每轮data-consistencysolve+denoise；fullphysics成本可能重复 | I轮；denoiseroffline | convergence/model/denoiser假设；A23one-prox低latency，但priorquality可能不足 |
| Bayesianinversion / sampling | likelihood、多次forward/gradient、covariancedirections | Gaussian可解析；MCMC通常大量步；LIS可offline | highdim/nonlinear/multimodal；A23统计压缩可省likelihood，不自动得到正确posterior |
| diffusion / flow inverse | K次network及可能的physicsguidance；每guidance需J/forward | trainingoffline；多NFEonline，也可能distillfewstep | latency、OOD、posteriorcalibration；A23小latent只是额外prior假设，不是天然降维保证 |

## 2. 与东哥工作的具体关系

教材 [B01] §6.2.4 已有 current back-propagation → internal field → analytic material ratio：
\[
\chi(r)=\frac{\sum_sJ_s(r)\overline{E_s(r)}}{\sum_s|E_s(r)|^2}.
\]
所以“current恢复后直接生成material”不是新贡献。§6.2.3 EBA已有通过中间参数把某些非线性近似拆成两步linear inversion。

TSOM已根据observationweak、propagationstrong区分current；FFT改进正是为了绕过昂贵GD-SVD。[B01] §6.4.2–6.4.3。OPM的M-channel有materialtangent动机，但同一个J的factorization不增加统计信息。

SOM-Net [R02] 输入deterministiccurrent和BP粗图，交替current/material结构，并从current解析得到场/介电图；网络损失同时涉及current、data、material。A23若只是增加一个learnedfeedbackblock，novelty很弱。

2026MFFSOM-Net [R28] 已在多频currentrestoration/EFIE/materialfusion方向推进；本轮只核对IEEE摘要/metadata，仍足以阻止“首次多频SOM网络”的宽泛主张。

## 3. 最容易被弱化、但不能省的对照

**同参考背景的 full-J/adjoint TSVD 或 Wiener。** 不是未知truth-stateJ；knownreferencefullJ可以离线构造为goldstandardencoder。若OPM只近似同一个J，后者代表其线性信息上限，同时actualsetupcost决定是否可部署。

**linear-in-a + exact a→χ。** 把局部depolarization/radiationreaction消掉，检验所谓feedback增益是否只是材料坐标变换。

**vanilla inverseBorn2。** 使用同一个A,Q,D，但不用A23的specialcompression/标签。输出相同就意味着novelty只能在更便宜构造或更有用统计保留，不能声称新inverseformula。

**analyticpolynomialclosure。** A18-B同actionbudget已有强结果，[P11]中degree3poly对某些tailquality/latency优于NN；不再次选择弱anchor制造巨大gain。

**currentBP与合理CSI。** 不把它们强行记为每轮fullLU，以免虚构相对加速。

## 4. 公平比较的四种口径

1. equal-operator-RHS：识别信息效率，但block效率不同，不能当walltime。
2. equal-memory：对大规模场景非常重要；增加Zcache不是免费。
3. equal-quality：同fullimage目标与noise/geometry/priors，测time-to-acceptable。
4. equal-total-resource：含geometry、reference、offlinebasis、training、validation、fallback与N次摊销。

各口径可能不同赢家，应都报告而不事后选有利口径。固定old32chart的physicsNRMSE不能替代fullvoxelimage质量。

## 5. Novelty的实际位置

标准：Schur/adjoint、SVD/Krylov、Gaussianposterior、DWR、inverseBorn、nullspaceprior、few-layerunrolling。

值得做A23实验的组合：真实Maxwellconstitutivenonlinearity与feedbackcurvature分离；按遗漏dataresponse控制posteriorloss；sourceanchoring和cacheddualcontraction节约准备；允许prior沿curvedmeasurementfibre补全；在lossyvector3D full-image任务上给quality/time边界。

现在还没有证明这一组合击败 simpler baselines。若等价输出更贵，应该保留baseline并停止OPM专属路线，而不是增加NN以延续名称。



---

<a id="section-8"></a>

# Feedback-native NN：物理必须决定哪些操作

**本轮不训练 NN。** 主候选先是解析少次成像。NN 的保留条件是：在同一 full-image representation、已控制模型/标定偏差后，确有非神经先验不能便宜补出的残余结构。SOM-Net 已经将 Lippmann–Schwinger/current/material 更新嵌入网络；ICLM 与 learned primal-dual 也都是直接近邻。[R02–R03,R16] 不能以“首次物理原生网络”叙事。

## 1. 网络必须尊重的显式映射

参考背景决定
\[
x\xrightarrow{B} \text{excitation}
\xrightarrow{R_b}\text{current}
\xrightarrow{S}\text{data},
\]
以及二阶重复散射
\[
Q(x,x)=S R_b H(x)G R_b H(x)e_b.
\]
数据 pullback 应使用同一映射的真实离散 adjoint；不另训练一个与 forward 不一致的“逆网络”。

可学习的量：prior distribution、少量 shrinkage/gating 权重、低秩材料 correction、局部合理的 model-discrepancy 参数。不可无代价替代的量：source/receiver 几何变换、复相位相干组合、真实极化率及其导数、数据 likelihood、gauge 变换规则、frozen-reference 的物理适用域。

学到的 discrepancy 与真实材料必须有独立标定/数据来区分，否则存在 attribution confounding。

## 2. N1：Feedback-recurrent network

最简单的 current recurrence \(j_{\ell+1}=b+Fj_\ell\) 加权共享，相当于 polynomial resolvent。单纯学习多项式系数并不是新架构，而且 A18-B 的同 action analytic polynomial 已有很强成本对照。[P11]

**裁决：不作为主路线。** 可保留一个 bounded few-pass material recurrence：
\[
x_1=Dz,\quad
x_2=x_1-\gamma_\theta D\hat Q(x_1,x_1)+R_\theta(z,x_1),
\]
其中 \(\gamma_\theta\in[0,1]\)，R 是受 data/physics 约束的 prior correction。先令 R=0、γ=1 和预定 analytic γ 作为对照，再谈学习。

若使用 \(\|F\|<1\) 的 contractivity 证明，需实际验证该范数；被动介质或 \(\rho(F)<1\) 不足以保证原 Euclidean recurrence 稳定。有限层数可稳定而无限重复不稳定，不能混同。

## 3. N2：Primal-dual encoder

Primal stream 保留 \(Ax,Qxx\)，dual stream 保留
\[
(A+2Q[x,\cdot])^TC^{-1}[z-Ax-Qxx].
\]
它们有不同的**计算角色**：预测观测与归因材料；但由同一精确 A/Q 决定时，不包含两份独立统计信息。可以共享 core、用自动/手工一致伴随，避免重复存储。

A21 支持“双侧近似影响优化”的机制，不授权使用未知 full-GN step/current 作为线上 stream。[P06] 网络信息预算必须与普通 A/Q-based encoder 相同。

Cross-attention 只在能解释所算 bilinear interaction、且比直接低秩 contraction 更便宜时保留。把 primal/dual token concat 后多一个 Transformer，不构成机制结果。

## 4. N3：OPM tokenization

Family、degree、geometry、scale 可以作为元数据，但 token 应以 invariant transfer moments 或 covariant coefficients 编码：
\[
H_j=O_rF_r^jM_r,\quad
G_{ij}=Z_i^*Z_j.
\]
必须联合保留能表示 phase-coherent 交叉项的信息。任意 current basis \(Q_cV\) 不能改变预测。

**裁决：不优先。** 因为原 O/P/M 标签对同一 J 没有独立信息，而 gauge-safe 处理与 attention 都增加开销。只有跨几何/不同 source 数的训练样本效率实测明显改善，才值得继续。当前不以 token 数少作为部署优势。

## 5. N4：曲面上的 physics-supported / prior-dependent decoder

这是最值得保留的学习候选，但应改掉固定 hard split。

网络或非神经 prior 先提出完整弱/形状成分 \(b_\theta\)。随后**解析**执行
\[
a_0=\Sigma_s^{-1}U_s^Tz,
\quad
a_2=a_0-\Sigma_s^{-1}U_s^TQ(V_sa_0+V_wb_\theta,V_sa_0+V_wb_\theta).
\]
输出 \(x=V_sa_2+V_wb_\theta\)，并作物理可行性与 paid data check。

该显式 recoil 来自 `BAYESIAN_FEEDBACK_INVERSION.md` 的 T5。交叉项 \(Q(a,b)\) 解释了为什么补全 invisible/weak structure 也会影响可靠数据；hard freeze a 通常只保持线性一致性。

**全图要求。** \(b_\theta\) 可以包含原32D图外边缘、shell、非对称区域。相应 Q 必须支持这些方向：全空间 operator action、完整 decoder range 的离线 tensor，或有界 approximation。只训练全图 NN、却用32D Q 做“全图物理认证”是错误的。

## 6. N5：物理 latent dynamics

可在 low-rank material latent z 中保留
\[
f_{\rm latent}(z)=A_rz+Q_r(z,z),
\]
或小 rational Schur core，其参数由几何/背景构造。学习的 transition 只用于 residual prior，而不是替换所有 Maxwell dynamics。

这与 quadratic-bilinear ROM/Volterra modeling 的已知思想重合 [R10,R30]。价值只能来自更低 online cost、explicit error budget 和跨对象/几何稳定性。若 latent 未覆盖真实材料变化，内层物理一致性不等于真实 full-image 一致性。

## 7. 训练目标、证据与泄漏防护

后续获批后可以用
\[
\mathcal L=
\mathcal L_{\rm image}
+\lambda_d\|C^{-1/2}(f_{\rm surrogate}(\hat x)-y)\|^2
+\lambda_q\mathcal L_{\rm calibrated\ uncertainty}
+\lambda_g\mathcal L_{\rm gauge}.
\]
各项权重在 validation 冻结；必须另用真实 full-wave forward 评估 surrogate bias。训练标签可含 offline fields/J，但在线构基与推断绝不读取真对象电流/full-J/reference GN step。

必须按**对象**划分训练/验证/测试，而不是把同一个对象的多个 noise realization 分到不同集合。A22四个已暴露对象只能 feasibility，不是泛化测试。校准/geometry holdout 与 object-family holdout 分开报告。

## 8. 必要消融与 cheapest falsification

对相同输入和模型容量，比较：
- 纯 analytic x1/x2；
- 相同 A 的 SVD/Wiener + wavelet/GMM；
- hard split NN；
- 相同 NN + quadratic recoil；
- recoil 中删去 local constitutive 项或删去 mixed Q(a,b)；
- 不加 O/P/M label vs 加 label；
- 随机 unitary basis gauge、改变 source/receiver 数或几何。

正面结果应是相同图像质量更快，或相同时间更准/更校准，或在 OOD 下可解释地失效并拒绝。仅 training loss 更低、NN 参数少、四个熟悉对象更好，不够。

## 9. 最终架构裁决

Primary：不需要 NN 的 projection-first few-pass inverse。

Secondary：analytic Gaussian/GMM/结构 prox；仍无 NN。

High-risk/high-reward：N4 的 full-image prior proposal + Maxwell quadratic recoil，必要时 N2 的一致双侧计算。生成概率版本还需 Jacobian/evidence 权重，不能把 deterministic data projection 当 posterior sampling。

停止：NN current ranking/proposal、learned full resolvent、OPM标签驱动的大 token encoder、缺少 posterior headroom 的 diffusion。它们的已有负结果或直接最近邻使其不应吞掉下一轮有限算力。



---

<a id="section-9"></a>

# Bayesian feedback inversion：充分统计、压缩损失与曲面后验

本文件不预设 diffusion 必要。首先推导能解析获得的 likelihood/后验结构，再决定是否需要生成模型。背景 [R12–R15,R20–R22]；Maxwell 二阶算子由 `ONE_SHOT_INVERSE_THEORY.md` 明确定义。

## 1. T4a：低维线性统计量何时真的充分

模型
\[
z=f(x)+\epsilon,\quad \epsilon\sim N(0,I),\quad t=U_y^Tz,\quad P=U_yU_y^T.
\]
U_y 在本次测量前固定。对于开放参数域，t 对 x 充分的充要条件是
\[
(I-P)f(x)=c
\]
与 x 无关。

**证明。** 正交分解 Gaussian likelihood：
\[
\log p(z|x)
=-\tfrac12\|P(z-f(x))\|^2-\tfrac12\|(I-P)(z-f(x))\|^2+\text{const}.
\]
若 complement mean 为常数，第二项是与 x 无关的因子，满足 factorization。反之任选 x,x'；likelihood ratio 中关于 \(z_\perp\) 的线性项系数为 \((I-P)(f(x)-f(x'))\)。充分性要求它为零，故 complement mean 为常数。

这说明 OPM factorization 本身不产生新统计信息；需要保留的是 mean family 在 measurement space 中的变化，而不是 O/P/M 标签。

## 2. T4b：二阶 jet 的最小线性充分空间

局部二阶 forward
\[
f_2(x)=f_0+A x+Q(x,x).
\]
最小数据线性统计量的维数为
\[
\boxed{k_{\rm jet}=\dim\operatorname{span}
\{Ae_i,\ Q(e_i,e_j):1\le i\le j\le p\}.}
\]

**充分性。** 若 range U_y 包含上述所有向量，\(f_2-f_0\) 全在该空间中，使用 T4a。

**必要性。** 若 complement mean 常数，对开放域的一阶和二阶导数分别求值，得到 \((I-P)A=0\) 与 \((I-P)Q(e_i,e_j)=0\)。

最小性只针对固定的**线性数据压缩**；不声称所有 nonlinear sufficient statistics 必须有同样维数，也不声称 finite-precision representation 存在如此简单的信息论下界。

若 \(A\) 已满行 rank，\(k_{\rm jet}=m\)，根本没有额外二阶数据方向可加入；若 \(A\) rank低，二阶空间可能快速扩到 m。A23 应优化有噪声条件下的可舍弃误差，而不是追求 exact jet 的最小阶。

参数化改变 \(x=\phi(z)\) 的二阶项只额外增加 A 的列空间，因此完整 span[A,Q] 对局部可逆材料重参数化不变。受限 chart 与截断 singular range 不享有相同保证。

## 3. T4c：压缩导致的后验信息损失界

使用相同 prior \(\pi(x)\)，真模型 mean f 与近似 mean
\[
\tilde f(x)=P f(x)+(I-P)f_0.
\]
后者的 posterior 只依赖 t。条件 Gaussian 的 KL 为
\[
\operatorname{KL}(p(z|x)\|\tilde p(z|x))
=\tfrac12\|(I-P)(f(x)-f_0)\|^2.
\]

对联合分布应用 KL chain rule：
\[
\begin{aligned}
\operatorname{KL}(p(x,z)\|\tilde p(x,z))
={}&\operatorname{KL}(p(z)\|\tilde p(z))\\
&+\mathbb E_{z\sim p}\operatorname{KL}(p(x|z)\|\tilde p(x|z)).
\end{aligned}
\]
丢掉非负的 evidence KL，得
\[
\boxed{\mathbb E_z\operatorname{KL}(p(x|z)\|\tilde p(x|z))
\le\tfrac12\mathbb E_x\|(I-P)(f(x)-f_0)\|^2.}
\]

这把“遗漏 feedback response”转换为明确的平均 posterior 损失预算。不是逐对象置信证书，也不是由四个 probe 自动获得的可认证上界。

若 prior 支持于 \(\|x\|\le\rho\)，且
\[
\|(I-P)Ax\|\le\varepsilon_1\|x\|,\quad
\|(I-P)Q(x,x)\|\le\varepsilon_2\|x\|^2,\quad
\|R_3(x)\|\le C\rho^3,
\]
则右侧不超过
\[
\tfrac12(\varepsilon_1\rho+\varepsilon_2\rho^2+C\rho^3)^2.
\]
精确保留 linear+quadratic 时为 \(O(\rho^6)\)；只保留完整 linear range、遗漏 quadratic 时一般为 \(O(\rho^4)\)。

**关键限制。** 若存在固定的线性截断误差 \(\varepsilon_1>0\)，主项仍可为 \(O(\rho^2)\)，不能宣传 \(O(\rho^6)\)。Gaussian prior 无界时应直接使用有限 expectation 或显式处理区域外概率，不能把局部 resolvent 假设默认拓展到所有 Gaussian tails。

## 4. T4d：随机 quadratic probes 为什么可用

写 \(Q(g,g)=\sum_{ij}q_{ij}g_ig_j\)，对称 \(q_{ij}=q_{ji}\)，\(g\sim N(0,I)\)。由
\[
\mathbb E[g_ig_jg_kg_l]
=\delta_{ij}\delta_{kl}+\delta_{ik}\delta_{jl}+\delta_{il}\delta_{jk}
\]
得
\[
\mu_Q=\sum_iq_{ii},\quad
\operatorname{Cov}Q(g,g)=2\sum_{ij}q_{ij}q_{ij}^T,
\]
\[
\mathbb E[Q(g,g)Q(g,g)^T]=
2\sum_{ij}q_{ij}q_{ij}^T+\mu_Q\mu_Q^T.
\]

因此**不能忘掉均值方向**。用 centered covariance 的前几特征向量，加上均值，给出 prior-weighted 二阶响应压缩；线性+二阶的总 second moment 也可一起压缩。Gaussian 下奇数矩为零，A g 与 Q(g,g) 的交叉 second moment 为零；非对称 prior 通常没有这项简化。

此法与 randomized range finding/Volterra–quadratic reduction 的已知邻域相连 [R09,R30]。新候选是 Maxwell 的便宜双侧构造与上述 posterior budget，而不是“首次随机二次型压缩”。

**反例。** \(Q(g,g)=(g_1^2,g_2^2)\)。Rademacher probes 全部输出(1,1)，只看到 rank1，但真实 quadratic output span 为2。Gaussian 或显式 diagonal probes 可辨别。

## 5. 简单 Bayesian estimator 应先于 NN

对线性模型 \(z=Ax+\epsilon\)，prior \(N(\mu,\Gamma)\)，噪声协方差 C：
\[
\Gamma_{\rm post}=(\Gamma^{-1}+A^TC^{-1}A)^{-1},
\quad
\mu_{\rm post}=\mu+\Gamma A^T(A\Gamma A^T+C)^{-1}(z-A\mu).
\]
可在低维 data space 求解，避免 \(p\times p\) inverse；\(\Gamma\) 可隐式为多尺度算子。低秩 posterior update 与 LIS 已有先例 [R12]。

若 prior 为有限 Gaussian mixture，每个 component 都有解析 mean/covariance 和 evidence weight。多模态只有少量 shape alternatives 时，这可能比 flow 更便宜、更易校准。非线性时需要局部/二阶 likelihood approximation；不能继续称为全局 exact Gaussian posterior。

## 6. SVD 正交不等于 posterior 独立

例：\((x_1,x_2)\sim N(0,\begin{bmatrix}1&.8\\.8&1\end{bmatrix})\)，只测 \(z=x_1+\epsilon,\operatorname{Var}\epsilon=.25\)。z=1 时
\[
\mathbb E[x|z]=(.8,.64)^T,\quad
\Gamma_{\rm post}=
\begin{bmatrix}.2&.16\\.16&.488\end{bmatrix}.
\]
第二方向没有直接测量，但通过 prior correlation 更新；两个坐标后验仍相关。本轮数值已核对。固定“physics Gaussian + independent prior complement”不成立。

若拆成 a,b，Gaussian prior 给
\[
\mathbb E[b|a]=\mu_b+\Gamma_{ba}\Gamma_{aa}^{-1}(a-\mu_a),
\]
\[
\Gamma_{b|a}=\Gamma_{bb}-\Gamma_{ba}\Gamma_{aa}^{-1}\Gamma_{ab}.
\]
对线性 likelihood 解析消元 b 时，effective mean 和 noise covariance 都改变：
\[
C_{\rm eff}=C+A_b\Gamma_{b|a}A_b^T.
\]
仅扩大 noise、不修改 conditional mean，会漏掉 cross-covariance。

## 7. T5：先验补全必须沿非线性数据曲面移动

取物理上稳定的线性奇异坐标：
\[
x=V_s a+V_w b,\quad U_s^TA V_s=\Sigma_s,\quad U_s^TA V_w=0.
\]
\(\Sigma_s\) 可逆。给定 b，定义
\[
a_0=\Sigma_s^{-1}U_s^Tz,\quad x_0=V_s a_0+V_w b,
\]
\[
\boxed{a_2(b)=a_0-\Sigma_s^{-1}U_s^TQ(x_0,x_0).}
\]
则在小 x0、稳定 inverse 与有界 Q 的条件下，
\[
U_s^T[A(V_sa_2+V_wb)+Q(V_sa_2+V_wb,V_sa_2+V_wb)]-U_s^Tz
=O(\|x_0\|^3).
\]

**证明。** \(\delta x=V_s(a_2-a_0)=O(x_0^2)\)。线性项恰抵消旧 Q；新旧 Q 差为 \(2Q(x_0,\delta x)+Q(\delta x,\delta x)=O(x_0^3)\)。

固定 a0、只生成 b 的 hard split 则留下 \(O(x_0^2)\) 的 projected data error。NN 或 Bayesian completion 必须允许可靠坐标发生这个可解释的小 recoil，保护的是测量支持，不是旧坐标的数值永不改变。

若 weak linear response 不为零、Q 为近似或 b 很大，另加相应尾部/模型误差项。真实全图补全需要 Q 作用于 chart 外方向，不能拿32D Q tensor处理完整影像然后声称有上式保证。

## 8. 准确 posterior 还需要 density/Jacobian

将强测量近似为无噪声 \(F_s(a,b)=t\)，在 \(\partial_aF_s\) 可逆的区域，隐函数定理给 a=ψ(b)。积分掉 a 时
\[
p(b|t)\propto
\frac{\pi(\psi(b),b)}{|\det\partial_aF_s(\psi(b),b)|},
\]
还应乘上未被强约束部分的 likelihood。只从 prior 采 b、再投影到数据曲面，通常不是正确 posterior。强测量有噪声时更适合联合采样/局部 Gaussian，不宜强行硬约束。

这一 determinant 是 coarea/变量消元的已知因素；二阶 recoil 是便宜的几何近似，不会自动处理概率密度。

同样，current factor graph
\[
p(x,j,z)=\pi(x)\,p(j|x)\,p(z|j)
\]
中 deterministic current 必须写成 \(p(j|x)=\delta(j-L_x^{-1}b_x)\)。若改写为 \(\delta(L_xj-b_x)\)，需乘 \(|\det L_{x,\mathbb R}|\)；复方阵对应 \(|\det L_x|^2\)。漏掉它会人为偏好某些 resonant/material states。不能把这种伪权重当作“Bayesian feedback prior”。

## 9. 二阶 likelihood 与生成方法

二阶近似 likelihood
\[
\log p(z|x)=-\tfrac12\|z-Ax-Q(x,x)\|^2+\text{const}
\]
的 score 为
\[
\nabla_x\log p(z|x)
=(A+2Q[x,\cdot])^T[z-Ax-Q(x,x)].
\]
若有 correlated noise，再加 \(C^{-1}\)。这提供明确的 physics-native conditioning/score，而非 concat 三个 OPM labels。

但给定 b 后，a 中还含 \(Q(V_sa,V_sa)\)，因此 \(p(a|b,z)\) 一般**不是 Gaussian**。只有该项为零或经过受控局部线性化，才可用 conditional Gaussian elimination。不得把双线性 cross-term 的解析形式推广成所有二阶后验解析。

一个 \(f(a,b)=(a,b^2)\) 的例子：线性 statistic 丢掉第二测量，但实际 |b| 可测，符号 ± 构成二模态。二成分 mixture 就可能足够；不需要自动启用 diffusion。

## 10. 标定、偏差与 latent 维数

线性 nuisance \(G_\gamma\gamma\)，Gaussian \(\gamma\sim N(0,\Gamma_\gamma)\) 可被积分为 \(C_{\rm eff}=C+G_\gamma\Gamma_\gamma G_\gamma^T\)。未知 separable gains、phase 和 geometry 与材料耦合时需联合推断/重新线性化；将其噪声化是近似而不是 gauge 已被解决。

“prior complement”不一定低维：full voxel p 很大而稳定 rank小，剩余维数可能巨大。小 latent 是额外形状/稀疏/训练分布假设，需要报告其 full-image approximation error；不能以物理不确定性之名隐藏 shape prior。

模型失配形成的系统性偏差，应通过独立 forward model、geometry扰动与 calibration nuisance 检验。它不是训练一个 residual decoder 就能正当地解释成 posterior ambiguity。

## 11. 路线顺序

先运行 conditional Gaussian / 少量 Gaussian mixture；其次 one-prox 或小 deterministic decoder；只有 held-out data 下确有多模态或分布校准收益，且 latency 可接受，才运行 conditional normalizing flow；diffusion/flow matching 排最后。

比较的量包括 posterior predictive residual、credible-interval calibration、proper scoring rule、多个形状解的真实性及总时间。漂亮 samples、低 latent 维数和一次 data projection 都不是 posterior 正确性的证明。



---

<a id="section-10"></a>

# 非神经先验、Maxwell 能量与廉价物理可行投影

**优先结论。** 先比较 conditional Gaussian、Gaussian mixture、wavelet/group shrinkage 或一次受限结构修正。物理约束能排除不合法材料，但不能补出测量没有确定的真值。PDE residual 与 passivity 都不是“免费 inverse prior”。

## 1. 物理一致性不是正定能量最小化

时间约定为 \(e^{-i\omega t}\)，与教材及 backend 一致 [B01,P03]。局部被动介质的绝对介电张量满足
\[
\operatorname{Im}_H\epsilon=(\epsilon-\epsilon^*)/(2i)\succeq0
\]
（同时需正确处理磁响应、色散和适用频率）。互易性对应 transpose symmetry，而不是 Hermitian。

Maxwell \(L=I-F\) 一般非 Hermitian、非 SPD；不能把 \(x^*Lx\) 当成全局非负材料能量，也不能从介质有耗推出离散 Galerkin core 的 Euclidean coercivity。损耗、辐射边界、源做功共同进入 Poynting balance；limited-aperture 接收数据不能直接估计全部 radiated power。

相对于有耗参考背景的 contrast 虚部可能为负，仍对应被动绝对介质。因此约束 \(\operatorname{Im}\chi\ge0\) 只在相应背景/定义下适用，不应直接搬入所有 differential sensing。

## 2. 一个具体、便宜的 A9 极化率投影

对 [P03] 的单频、free-space scalar CM + radiation-reaction 极化率，
\[
a_{\rm CM}=\frac{3v\chi}{3+\chi},\qquad
a=\frac{a_{\rm CM}}{1-i c_k a_{\rm CM}},\quad c_k=\frac{k^3}{6\pi}.
\]
当绝对背景为实的被动参考且 \(\operatorname{Im}\chi\ge0\)，有
\[
\operatorname{Im}a-c_k|a|^2\ge0.
\]

**证明。** Möbius 映射 \(a_{\rm CM}\) 保持上半平面；\(a^{-1}=a_{\rm CM}^{-1}-ic_k\)，所以
\(-\operatorname{Im}a^{-1}\ge c_k\)，即上式。a=0 用连续性处理。

不等式等价于复平面上的圆盘
\[
\left|a-\frac{i}{2c_k}\right|\le\frac1{2c_k}.
\]
因此最小 Euclidean 修正可逐 cell 显式计算：
\[
c=\frac{i}{2c_k},\ R=\frac1{2c_k},\quad
\Pi_{\rm passive}(a)=c+(a-c)\min\{1,R/|a-c|\}.
\]
中心点单独处理避免 0/0。复杂度 O(p)，不需要 Maxwell solve。

这不是新 passivity 定律；价值在于**对真实代码极化率坐标的精确可行域**，比事后把 χ 的虚部随意截断更明确。映射回 χ 时还要检查 \(3v-\kappa a\) 的极点及已声明材料上界。张量 polarizability、非均匀背景、自项不同的离散算子需另推，不能沿用同一圆盘。

## 3. 物理投影可能破坏数据一致性

即使 projection 是非扩张的，也只相对于包含真值的可行集给距离性质；不能保证当前数据 residual 降低。对材料改动 \(\delta x\)，
\[
\Delta f=A\delta x+2Q(x,\delta x)+Q(\delta x,\delta x)+\Delta R_3.
\]
因此投影后要么执行强测量 recoil，要么用可支付 forward 校核；两项都计时。不能一边承诺 hard physics-coordinate protection，一边做 unrestricted pointwise clipping。

若采用 prior correction \(d\)，在线性模型中可以约束
\[
\|A d\|\le\epsilon_{\rm prior}
\]
或仅约束可靠通道 \(\|U_s^TA d\|\)。非线性时用上一式/二阶 recoil，不仅检查 \(\|V_s^Td\|\)。

## 4. 为什么 PDE residual 本身不是材料先验

若每个候选 χ 都用精确解 \(j(\chi)=L_\chi^{-1}b_\chi\)，则
\[
L_\chi j(\chi)-b_\chi=0
\]
对所有合法 χ 成立。只加此 residual 不会偏好正确材料。它只能约束**未精确求出的 field/current latent**，或作为 surrogate mismatch 诊断，不能代替 measured-data likelihood。

同样，被动性和互易性允许大量不同材料；它们应作为 feasible-set/结构先验，而不是唯一性或分辨率保证。

## 5. 便宜结构先验的真实成本

| 先验 | 可用的廉价操作 | 适用性与风险 |
|---|---|---|
| Gaussian / Matérn | data-space Wiener update，隐式 covariance action | 平滑背景和近 Gaussian 后验；边界被抹平 |
| Gaussian mixture | 每 component 条件 Gaussian 与 evidence 加权 | 少量形状/材料类别；component 数增长需计费 |
| 正交 wavelet 稀疏 | \(W^*\operatorname{soft}(Wx,\lambda)\)，确为一次 prox | 边缘/多尺度；wavelet 不是各向同性 Maxwell 特征 |
| group sparsity | 向量块 shrink，组合 real/imag 或多频参数 | 共享 support；错误 group 会产生 bias |
| TV | TV proximal 或 primal-dual inner solver | 常值区域/边缘好，但“一次 TV prox”内部通常迭代 |
| level set / shape dictionary | 低维形状参数估计或检索 | 真有 shape headroom 才用；不是任意全图重建 |
| low-rank / multiscale | block shrink 或局部 rank reduction | 动态/多频共享结构；可能丢掉小目标 |
| edge-preserving regularizer | 一次预定近端/局部加权修正 | 权重选择和 nonlinear step 也需独立验证 |

PnP/RED [R18–R19] 允许更灵活 denoiser，但一般 denoiser 不等于某个已知能量的梯度，且多次 data-consistency/denoise iteration 不能称为 one-shot。先把一个固定 wavelet/TV baseline 做到位，再决定小 NN 是否有真正收益。

## 6. 跨频物理先验

可使用统一 dispersion 参数，而不是每频独立任意复 χ。例如在 \(e^{-i\omega t}\) 约定下，具有非负 relaxation strength、正 relaxation time、非负 conductivity 的 Debye 型参数化可提供被动性和频率耦合。具体系数及组织范围必须由实际数据/外部组织资料提供，本轮不虚构医学常数。

材料参数一致不代表 \(L_f,S_f,B_f\) 一样；每频先验 pullback 应按链式法则。对有限频点简单裁剪不能证明全频 Kramers–Kronig 一致性。

## 7. 本轮竞争裁决

Primary prior baseline：Gaussian/mixture 或 wavelet/group 单次 prox，取决于预先声明的场景。TV 作强对照但如实计内部迭代。passivity projection 是所有候选可共享的物理约束，不作为 NN 的独占优势。

只有当 residual 在独立模型/标定检查后仍主要是可预测形状结构，才训练 deterministic residual decoder。若残余是系统 Maxwell bias，先修 model/calibration；若残余真是多解，输出不确定性而非单一漂亮真值。



---

<a id="section-11"></a>

# 对称性、互易性与 basis gauge：哪些能省算，哪些不能

物理来源 [B01] §2.11、[P03]；以下矩阵推导在固定离散模型下成立。对称性主要用于共享算子、消除任意坐标依赖与约束 hypothesis class，不会创造新测量。

## 1. Reciprocity 是 transpose，不是 adjoint

互易介质适当边界条件下，dyadic Green 满足 \(G(r,r')=G(r',r)^T\)。有耗介质仍可互易，故复杂数值的 transpose symmetry 不等于 Hermitian symmetry。[B01]

原 current operator \(L=I-A_{\rm loc}G\) 通常不对称，即使 \(G^T=G\)。但完整 transition operator
\[
\mathcal T=(A_{\rm loc}^{-1}-G)^{-1}
\]
在 scalar/reciprocal local response 下满足 \(\mathcal T^T=\mathcal T\)。若零极化率使 \(A_{\rm loc}^{-1}\) 不存在，使用 \(\mathcal T=(I-A_{\rm loc}G)^{-1}A_{\rm loc}\) 和连续延拓。

本轮 tiny DDA 中 \(\mathcal T\) transpose 误差约 \(9.1\times10^{-18}\)，而原 L transpose 相对误差约 \(4.6\times10^{-3}\)，直接展示了两个概念的不同。

## 2. 能否减少 forward / adjoint 成本

对确实 complex symmetric 的算子 M：
\[
M^{-*}v=\overline{M^{-1}\overline v}.
\]
可复用同一个 factorization，但 RHS 需共轭，结果也需共轭。对原非对称 L，应先作正确 local-response/pre-post 转换，或直接复用 LU 的 conjugate-transpose solve 功能。不能把物理 reversed source field 原样当作 adjoint field。

源、接收位置和偏振相匹配、端口定义/标定正确时，互易性可减少重复 transfer entries 或用发射场生成某些 receiver information。若端口集合不同，仍需相应 RHS。对有源、磁光非互易介质，或含非互易测量链时，不应用此简化。

“共享 LU”与“省掉 solve RHS”是不同收益；所有比较分别计数。

## 3. 电流 basis gauge 的精确不变性

令 current basis \(Q_c\to Q_cV\)，\(V^*V=I\)。压缩系数满足
\[
F_r\to V^*F_rV,\quad M_r\to V^*M_r,\quad O_r\to O_rV.
\]
于是
\[
O_r p(F_r)M_r
\]
不变，\(O_r(I-F_r)^{-1}M_r\) 也不变。物理输出不应依赖 SVD 的 sign/phase 或简并子空间内旋转。

适合网络的对象是完整 contractions、cross-Gram、带变换规则的 covariant vectors，而不是孤立的第3个 O-mode 实部。只对每列取绝对值虽可消 phase，却会毁掉相干干涉。

一个 covariant 非线性可以是 \(z\mapsto z\,g(z^*z)\)；多向量使用共同 Gram。一般逐坐标 complex ReLU 不对任意 unitary gauge 等变。固定最大分量 phase 的 gauge-fixing 在 crossing/degeneracy 附近可能不连续，只能作工程便利，不能替代 gauge test。

## 4. 对称性消融应该测什么

同一个物理样本，把 basis 乘独立 Haar unitary V，转换全部 core/injection/observation 系数；输出、likelihood、uncertainty 应在声明浮点容差内不变。只翻符号不够，还要测试简并/近简并子空间旋转。原始 data 与 geometry 不变，故这是无新 Maxwell 数据的强测试。

对 reciprocity，比较 source-receiver swapped transfer（匹配端口 normalization），并确认 adjoint dot-product identity 独立通过。一个检查通过不替代另一个。

## 5. Translation / rotation 的成立条件

均匀各向同性背景中，**对象、全部 sources、receivers、偏振与坐标同时**作刚体变换，Maxwell 系统协变。矢量场和张量材料需随旋转变换；标量像不是唯一需变换的变量。离散网格插值、边界条件和天线方向也可能造成误差。

固定接收阵列、只移动对象通常没有简单 SE(3) 不变性。网络不能把任意 object-only rotation 当作无代价 augmentation。

在均匀背景、plane-wave incidence、远场观察的特例下，对象平移 t 产生已知相位因子
\[
\exp\{ik(\hat d_{\rm in}-\hat d_{\rm out})\cdot t\}.
\]
近场 antennas、异质背景或未知 calibration gain 时不使用此简式；相位与 gain/geometry 可混淆，不能仅靠标准化恢复可识别性。

## 6. 跨频共享

令 \(L_{\omega+\Delta}=L_\omega+\Delta L\)。若
\[
\|L_\omega^{-1}\Delta L\|<1,
\]
则
\[
L_{\omega+\Delta}^{-1}
=(I+L_\omega^{-1}\Delta L)^{-1}L_\omega^{-1}.
\]
这给 interpolation/continuation 的条件边界，不意味着跨频完全共享 \(F_{\rm eff}\)。receiver Green、sources、极化率/dispersion、self term 都可能改变。

被动性/causality 可约束频率间参数；具体 passive ROM construction 是另一个已知领域，不能仅靠 “core eigenvalue clipping” 保证完整 Maxwell passivity。lossless transient ROM [R06] 的 self-adjoint wave structure 也不能直接移植到原有耗频域 F。

## 7. Energy 与端口可实现性

适当功率归一的完整被动端口散射矩阵可满足 contractivity；部分场样本构成的 S 或 current L 并不是该矩阵。有限 aperture 丢失辐射通道时，用 measured norm 做全功率守恒可能拒绝合法对象或接受错误模型。

可落地的便宜物理约束是 `PHYSICS_NATIVE_PRIORS.md` 的局部极化率圆盘、绝对材料可行域、正确 reciprocal tensor symmetry。它们与数据约束一起使用，不替代 likelihood。

## 8. 裁决

真正可优先利用的结构：缓存 adjoint/forward factorization、匹配端口 reciprocity、basis-invariant contractions、固定几何数据映射、受控频率 continuation。

暂不保留：固定阵列 object-only SE(3) 宣称、把 L 当 SPD、任意 lossless norm conservation、只靠 phase/sign canonicalization 的 OPM token network。对称性要体现为可验证 invariance 或实际 operator savings，而不是解释性标签。



---

<a id="section-12"></a>

# 解析 / 近解析 one-shot 理论：相对反馈、误差分解与非线性修正

**主结论。** Maxwell feedback 可以给出无需在线 GN 的二阶材料响应和一次 inverse correction。其适用半径由“相对参考背景的 feedback”控制。它不是全局 inverse formula，也不是首次 inverse Born series [R04–R05]。A23 值得检验的贡献是低成本构造、参数化一致的曲率识别及与完整图像/后验压缩的结合。

## 1. 精确有限幅度 identity

在固定背景 Green \(G\)、固定 source/receiver、局部 isotropic 极化率下：
\[
j_s=a(e_s^{inc}+Gj_s).
\]
令 \(a=a_b+h\)，\(H(h)=\operatorname{diag}(h_i I_3)\)，\(L_b=I-a_bG\)，\(R_b=L_b^{-1}\)，\(e_{b,s}=e_s^{inc}+Gj_{b,s}\)。相减得
\[
L_b\Delta j_s=H(h)e_{b,s}+H(h)G\Delta j_s.
\]
定义
\[
X_s(h)=R_bH(h)e_{b,s},\qquad T(h)=R_bH(h)G.
\]
于是
\[
\boxed{\Delta j_s=(I-T(h))^{-1}X_s(h).}
\]

只需 \(L_b\) 与 \(I-T(h)\) 可逆；它不是 Born 近似。若 \(\eta=\|T(h)\|<1\)，可进一步作受控展开；这个充分条件不等于必要条件。

**物理解释。** \(X(h)\) 是新增材料在已存在总场中的首次激发；\(T(h)X(h)\) 是它通过参考介质传播后，再次被新增材料散射。强已知背景的所有重复散射已包含在 \(R_b,e_b\) 中。因此高绝对对比不必导致展开失效；未知整体高对比、近极点参考或大几何变化则可能使 \(\eta\) 大。

## 2. T2a：二阶响应与 remainder

把全部 source 与白化/实化接在 S 后，记为同一个输出算子。定义
\[
Ah=SX(h),
\]
\[
Q(u,v)=\tfrac12 S R_b[H(u)GX(v)+H(v)GX(u)].
\]
则
\[
\Delta y=Ah+Q(h,h)+R_3(h)
\]
且
\[
R_3(h)=S(I-T(h))^{-1}T(h)^2X(h).
\]
所以
\[
\boxed{\|R_3(h)\|\le \frac{\|S\|\,\eta^2}{1-\eta}\|X(h)\|.}
\]

**证明。** 使用 \((I-T)^{-1}=I+T+(I-T)^{-1}T^2\)。矩阵 T 与自身 resolvent 可交换；没有把 \(H,G,R_b\) 彼此交换。\(X=O(h),T=O(h)\)，在有统一 resolvent margin 的有界邻域内，\(R_3=O(\|h\|^3)\)。

一般非正规系统不宜用 \(\rho(T)\) 替换 \(\|T\|\) 后保留相同常数。可用其他诱导范数、数值范围或经过认证的 residual/resolvent 界扩大适用域，但需实际代价。

## 3. T2b：一次 inverse correction 的完整误差界

令观测
\[
z=Ah+Q(h,h)+R_3(h)+\epsilon.
\]
\(D:\mathbb R^m\to\mathbb R^p\) 为固定稳定线性 decoder，\(\hat Q\) 为近似二阶算子。定义
\[
h_1=Dz,\qquad h_2=h_1-D\hat Q(h_1,h_1).
\]
记 \(\tau(h)=\|(DA-I)h\|\)。假设
\[
\|Q(u,v)\|\le\beta\|u\|\|v\|,
\quad \|(\hat Q-Q)(u,v)\|\le\varepsilon_Q\|u\|\|v\|.
\]
则
\[
\begin{aligned}
\|h_2-h\|\le {}&\tau(h)+\|D\|(\|\epsilon\|+\|R_3(h)\|)\\
&+\|D\|\beta(\|h\|+\|h_1\|)\|h_1-h\|\\
&+\|D\|\varepsilon_Q\|h_1\|^2.
\end{aligned}
\]

**证明。** 展开
\[
h_2-h=(DA-I)h+D[\epsilon+R_3+Q(h,h)-Q(h_1,h_1)]
+D[(Q-\hat Q)(h_1,h_1)].
\]
对中间差用双线性恒等式
\(Q(h,h)-Q(h_1,h_1)=Q(h-h_1,h)+Q(h_1,h-h_1)\)，再三角不等式。

若 \(DA=I\)、无噪声、\(\hat Q=Q\)，则 \(h_1-h=O(h^2)\)，\(h_2-h=O(h^3)\)。这是局部 inverse Born/二阶 predictor–corrector 的结果，不是新原理。[R04–R05]

**不能删去 \(\tau\)。** 在欠定成像、TSVD、Tikhonov、chart truncation 下，\(\tau\) 含不可恢复/被正则化材料。即使二阶模型精确，也不能宣称全图 cubic recovery。若误差主要在 chart 外部，本式不会把它免费修好。

## 4. Feedback approximation、chart、noise 分开计

若用 \(\hat A\) 构造 D，真线性算子为 A，则
\[
\tau(h)\le\|(D\hat A-I)h\|+\|D\|\|A-\hat A\|\,\|h\|.
\]
若 \(h=Wc+h_\perp\)，则额外含 \(\|D A h_\perp\|\) 与未输出的 \(h_\perp\)；其测量影响一般不为零。不能只从分母删去 \(h_\perp\) 再声称完整重建可靠。

对 \(D_\lambda=(A^TA+\lambda I)^{-1}A^T\)，
\[
\|D_\lambda\|\le1/(2\sqrt\lambda),
\]
由 \(\sigma/(\sigma^2+\lambda)\) 的最大值得出；方向 bias 为 \(\lambda/(\sigma^2+\lambda)\)。这是真正的稳定性–分辨率取舍，不是 OPM 标签能消除的。

二阶 correction 会把噪声传播为交叉项及平方项。可用预先冻结的 \(\gamma\in[0,1]\)
\[
h_2=h_1-\gamma D\hat Q(h_1,h_1)
\]
或 low-rank/truncated Q。选择规则应来自已声明 noise/model budget 或独立验证，不能使用 truth 选择最漂亮的图。单次 residual 降低也不能证明 material error 降低。

## 5. 必须使用真实极化率，不能把 F 当作裸 χ

原 backend [P03]：
\[
a(\chi)=\frac{3v\chi}{3+\kappa\chi},\qquad
\kappa=1-i3c_kv,\quad c_k=\frac{k^3}{6\pi}.
\]
\[
a'=\frac{9v}{(3+\kappa\chi)^2},\quad
a''=-\frac{18v\kappa}{(3+\kappa\chi)^3}.
\]
用 χ 坐标时，
\[
\boxed{Q_\chi(u,v)
=Q_a(a'u,a'v)+\tfrac12 J_a(a''uv).}
\]
第二项是**局部 constitutive curvature**，第一项才是追加材料重复散射。只算第一项而称为完整 χ 二阶 Maxwell 是实现错误。

也可直接在 a 坐标求解，再使用精确局部逆
\[
\chi(a)=\frac{3a}{3v-\kappa a},\quad
\frac{d\chi}{da}=\frac{9v}{(3v-\kappa a)^2}.
\]
误差转换需要连接估计值与真值的路径远离 \(3v-\kappa a=0\)。在整个路径上有 \(|d\chi/da|\le C_a\) 才有 \(\|\Delta\chi\|\le C_a\|\Delta a\|\)。

因此必须加入 “linear inversion in a + exact local conversion” 基线。其优于 linear-in-χ 的收益不能自动归于多重散射 feedback。

## 6. T2c：哪个二阶新响应真正来自 feedback

这是 A23 较有价值的机制候选，但必须用正确的完整 tangent。

单频、完整复 cell 材料、\(a'_i\ne0\)，极化率变换是局部实微分同胚，因此
\[
\operatorname{Range}J_\chi=\operatorname{Range}J_a.
\]
令 \(P_J\) 投影到该完整切空间，则
\[
\boxed{(I-P_J)Q_\chi(u,v)
=(I-P_J)Q_a(a'u,a'v).}
\]

**证明。** 前节局部项 \(\tfrac12J_a(a''uv)\) 已在 tangent range 内，投影后为零。更一般，\(x=\phi(z)\) 为可逆光滑参数变换时
\[
D^2(f\circ\phi)[u,v]=D^2f[D\phi u,D\phi v]+Df\,D^2\phi[u,v].
\]
第二项切向，法向二阶响应不受坐标重参数化伪造。这是已知微分几何原理；上式把它具体落实为 Maxwell 的“局部响应非线性 / 重复散射非线性”分离。

**五个不能省略的限定。**

1. 若 full J 具有满行 rank，则 \(P_J=I\)，法向曲率完全为零。大 p、小 m 的有限数据成像中很可能如此。此时不应强行寻找“新 data dimensions”；二阶逆修正仍可在原 data space 内有用。
2. 固定 32D chart 的 \(J_\chi W\) 不包含所有 \(J_a(a''uv)\)。投影到 chart tangent 后出现的“innovation”，可能只是 chart 外部 constitutive 项，不是隐藏 feedback 信息。
3. 噪声截断后的稳定空间 \(P_{\rm stable}\ne P_J\)。被投到 complement 的线性尾部同样要计入，不能继续套精确消去结论。
4. 单实材料自由度、固定 loss、跨频 dispersion 参数等约束不构成完整 a-space 的重参数化；局部 constitutive curvature 可能具有真实法向部分。
5. 新 data response 不等于新参数可识别性。若 nuisance 材料方向的 tangent 可以吸收它，必须进一步做 attribution/profile。对 \(f(a,b)=a+b^2\)，b 的二阶项完全可被 a 吸收。

**可执行用法。** 不论 chart 大小，先显式计算并扣除已知 local \(a''\) 项；再相对于已声明的线性/稳定/nuisance spaces 报告 feedback innovation，并分别保留未扣除总曲率。不能只画一个“OPM nonlinear information score”。

## 7. 固定线性 decoder 的有限区域定理

设材料区域内任意连接 \(\chi_b\) 到 \(\chi\) 的线段合法，且
\[
\sup_{0\le t\le1}\|D J(\chi_b+t\Delta\chi)-C\|\le\delta.
\]
由微积分基本定理，
\[
D[y(\chi)-y(\chi_b)]-C\Delta\chi
=\int_0^1[DJ(\chi_b+t\Delta\chi)-C]\Delta\chi\,dt,
\]
故
\[
\|D(y-y_b)-C\Delta\chi\|\le\delta\|\Delta\chi\|+\|D\|\|\epsilon\|.
\]

这是 [P00] 所要求的 path-decoder 结构，不要求每一步解 GN；但固定 D 在宽材料域是否满足小 δ 是真实难点。feedback identities 帮助构造/估计 δ，不会使它自动小。

背景 decoder bank 可覆盖若干局部区域，但背景选择、区域外检测、参考准备和错误选择都必须进入成本/误差。不能用 truth 找最合适的 decoder。

## 8. Rational inverse 的正面例子与阻碍

单变量 feedback：
\[
y=\frac{x}{1-gx}\quad\Rightarrow\quad x=\frac{y}{1+gy}.
\]
这是 exact nonlinear one-shot，说明“不经 GN”并非逻辑上不可能。但多维观测通常只看到 compressed transfer。

设完整交互 transfer
\[
\mathcal T=(A_{\rm loc}^{-1}-G)^{-1}.
\]
若能完整观测 \(\mathcal T\)，形式上可恢复 \(A_{\rm loc}^{-1}=\mathcal T^{-1}+G\)。然而只观测 retained 子块时，
\[
\mathcal T_{RR}^{-1}
=A_R^{-1}-G_{RR}
-G_{RH}(A_H^{-1}-G_{HH})^{-1}G_{HR}.
\]
隐藏材料通过 Schur self-energy 与局部材料混合。把 \(\mathcal T_{RR}^{-1}+G_{RR}\) 直接当作局部材料会产生系统 bias。

这给出高风险方向的边界：小数量已定位散射体、充分多端口、可辨识 transfer 时可以研究直接 rational inversion；大未知介质、limited aperture 时没有同样的信息。教材 [B01] 第4章已有小散射体非迭代恢复；不能宣称第一次。

## 9. 本轮数值检查及其边界

独立 CPU 8-cell DDA、6源、18个矢量接收位置、16-real-material 全图，\(L_b\) 条件数约 1.189，线性 A 条件数约45.91。参数 h 为归一化极化率增量，五档幅度从 .2 至 .0125。

测得绝对 inverse error 的 log–log slope：
- 一次线性 inverse：1.99991；
- 一次二阶 feedback correction：2.99985；
- forward linear remainder：2.00024；
- forward quadratic remainder：3.00154。

在最大幅度下 \(\eta\approx0.0134\)，因此这是受控小相对扰动，不是 near-resonance/未知高对比测试。所有 identity/bound assertions 通过。细节见 `validation/THEORY_VALIDATION.json`。

最值得重视的负面信息：线性 data span rank16，完整 quadratic jet span rank88；“只有16个材料变量”并不意味着保留二阶 likelihood 的**线性**统计量也只有16维。这将成为下一轮压缩成本的决定性检查。

### 坐标变换的公平 prior

χ 与 a 的 baseline 不能简单使用同一个数值 λI 后称为同一先验。参考点应将物理材料质量度量/协方差按实 Jacobian \(T_a=D_\chi a\) 变换，例如 \(\Gamma_a=T_a\Gamma_\chi T_a^T\)。有限幅度概率比较还需处理非线性 pushforward 的密度/Jacobian。先给相同物理约束与局部 prior metric 的对照，再报告坐标非线性本身的收益，防止把正则化差异误当 feedback 改善。



---

<a id="section-13"></a>

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



---

<a id="section-14"></a>

# 定理、反例与验证账本

“已证明”指本包给出的有限维条件推导；“已验证”指 `validation/` 中的最小CPU检查；“新颖性”不由数学正确性自动获得。标准结论明确注明。

## 1. 六类成果总账

| ID | 数学命题及假设 | 证明/定位 | 计算含义 | 可检验预测 / 状态 |
|---|---|---|---|---|
| T1a | L/AU可逆且全部referencecurrents在U ⇒ Kb=0 | Redundancy §2直接代入 | 删除Pseed/chain，非删materialresponse | Pnorm跟随reference解残差；tiny通过 |
| T1b | U=0、fullcomplexchart含a/a'、rawM完整保留 ⇒ KP(d)⊂KM(d+1) | Redundancy §3逐次幂 | M可替P但多一degree | rankcap/受限chart可破坏；identitytiny通过 |
| T1c | 有U时P由M与ΠFUclosure联合生成 | Redundancy §4 blockSchur | 不可仅按名字合并P/M | 需实际capture；条件identity，非普遍subset |
| T1d | 缓存LU/L*U使K/T/adjoint免额外fullactions | Cheap §1代数 | 原六源4/4配置seed阶段删54vectorRHS | 四种operator相对误差约1e−16；tiny通过 |
| T2a | relativefeedbacketa<1 ⇒ cubicforwardremainderbound | OneShot §1–2 resolventidentity | 已知强背景也可小相对扰动 | finiteampidentity/boundtiny通过 |
| T2b | 稳定D、bilinearQ有界 ⇒ 完整inverseerrorbound | OneShot §3 | bias/noise/chart/Q误差不能省 | fullleftinverse/noiseless才cubic；tiny通过 |
| T2c | fullcomplex单频chart，a'可逆 ⇒ normalcurvature仅feedback项 | OneShot §5–6 chainrule | 分离localconstitutive伪创新 | identity约4.2e−15；one-dirchart反例通过 |
| T3 | 同质量setup/onlinecost给break-even | Complexity §5移项 | N小或online不快则无净收益 | 会计恒等式；无实际A23speedup结论 |
| T4a | Gaussian固定线性stat充分 iff complementmean常数 | Bayesian §1 likelihoodratio | 标签不能增信息 | 一般非线性SVD不充分；证明完成 |
| T4b | quadraticmodel最小linearstat=span[A,Q] | Bayesian §2求导/因子分解 | 可能比linearspand大很多 | 8cellrank16→88；不是内在参数维数 |
| T4c | samepriorGaussiancompression的平均posteriorKL≤遗漏meanenergy/2 | Bayesian §3 KLchainrule | 物理误差→posteriorbudget | exactjet为Oρ6，有linearerror则不是；条件证明 |
| T4d | GaussianquadraticCov=2ΣqijqijT，mean=Σqii | Bayesian §4 Isserlis | matrix-freerandomquadraticrange | exactquadraturetiny通过；Rademacher反例 |
| T5 | strongΣ可逆、小amplitude、完整Q ⇒ priorrecoil强dataerrorOρ3 | Bayesian §7双线性展开 | 保护数据而非固定材料系数 | scalarfibrehardOρ2/recoilOρ3；tiny通过 |
| T6a | gauge-transformedO/F/M的transfercontraction不变 | Symmetry §3代入 | NN使用covariant/invariantops | 必须做Haarunitarygauge测试；代数证明 |
| T6b | current/fibredeterministicfactor消元需Jacobian | Bayesian §8delta变量变换 | 不制造fakeprior或错误posterior | 1/|detL|伪权重反例；标准概率规则 |
| T6c | A9scalarCMRR被动极化率在明确圆盘内 | Priors §2 | O(p)物理投影 | 证明完成；本轮不声称临床/通用tensor验证 |
| AUX1 | 任意Xhat/Zhat的correctedtransfer双侧残差identity | Cheap §4 | 原非Galerkinclosure需显式correction | tiny约6.7e−13，标准DWR |
| AUX2 | DJ沿路径近C ⇒ finite-amplitudefunctionalerror界 | OneShot §7 FTC | referencebank需覆盖而非oracle挑选 | 条件证明；wide-domain常数未知 |
| AUX3 | hidden-currentSchurselfenergy阻碍pointwiseinverse | OneShot §8块逆 | compressedtransferinverse不是localmaterial | exactobstruction，未造有利oracle |

## 2. 必须保留的反例

| ID | 反例 | 否定的过强主张 |
|---|---|---|
| C01 | L=1,RA=.5,真defect=.5，未经修正doubledefect=.25 | 任意learnedresolvent也满足Galerkin双侧identity |
| C02 | F=[[0,100],[0,0]]，rho=0但degree0error100 | 小谱半径保证浅多项式精度 |
| C03 | L=diag(1,eps²)，遗漏eps e2输出1/eps | currentoverlap近1就能放心删P |
| C04 | L=[[0,1],[1,0]],U=e1，AU=0 | 完整L可逆⇒Galerkincore安全 |
| C05 | M的raw多源probe经rankcap丢掉关键方向 | materialprobe包含方向⇒currentseed完整 |
| C06 | fullJrowrank=m ⇒ PJ=I | 强非线性总会增加新data-space方向 |
| C07 | chart只含一个方向，a''uu在chart之外 | chart-normalquadratic全部来自feedback |
| C08 | f(a,b)=a+b² | 任何二阶response都可唯一归因到weakparameter |
| C09 | f(a,b)=(a,b²) | linearSVDsufficient / 弱方向完全没数据 |
| C10 | ρ=.8correlatedGaussianprior只测x1，x2posterior随y变 | weakposterior等于独立原prior |
| C11 | Rademacherg，Q=(g1²,g2²)总为(1,1) | 任意随机±1probe都能探索所有二阶方向 |
| C12 | f(a,b)=a+.7ab+.4b²+.2b³，固定a补b | 线性nullspace补全保持nonlineardata |
| C13 | δ(Lχj−bχ)不乘det积分得到1/|detLχ| | 未归一currentfactor是合法physicsprior |
| C14 | 曲面采b再投影a但不加det∂aFs | data-consistent样本自动是posterior样本 |
| C15 | L=I−AG，G对称而A非标量 | reciprocity等于rawL的Hermitian/transpose对称 |
| C16 | 完整Maxwell解对每个χ的PDEresidual均为0 | PDE-onlyresidual可识别正确材料 |
| C17 | highcontrastunknownbackground使eta≥1或inversepole逼近 | one-shot局部界无条件覆盖全部强散射 |
| C18 | fullQR/Hessian虽tiny，但cachedB和Z为多GB | 小rank自动可扩展或快 |
| C19 | 任意object-onlyrotation在固定阵列改变S/einc | fixed-systemSE(3)invariance |
| C20 | χreal/imag投影相对于有耗背景误裁合法负contrastloss | contrast被动性永远是Imχ≥0 |

C01/C02/C07/C10/C11/C12等有本轮数值项；其他为正文明确代数构造或条件反例，不写成已经运行的Maxwell实例。

## 3. 原项目证据与本轮证据必须分开

A20/A20-R1/A21/A22/A22-R1 的数值取自[P04–P10]，没有重跑。A21oracle验证不等于A23上线；A22in-chart统计不能变fullimage；已暴露四对象不是独立盲测；原gate未改。

本轮脚本是独立8cellvectorDDA，不读上游数据，float64/complex128，CPU。它证明有限矩阵例子与预期一致，不提供复杂组织、未知背景、large-n、GPUlatency、posteriorcalibration或publicationacceptance证据。

## 4. 验证的关键数字

完整原始数值在 `validation/THEORY_VALIDATION.json`，这里列便于核对的量：
- cachedSchurrelativeerrors：约1.6–2.1e−16；
- sourceanchoredP：3.62e−16；
- materialinverseabsoluteerrorslope：first1.99991，second2.99985；
- linear/quadraticforwardremainder：2.00024/3.00154；
- linear/jetdiscardedmeanslope：2.00031/2.99993；
- datareal648，materialreal16，linearstat16，fulljetstat88；
- Gaussianweightedquadraticinnovation90%/99%/99.9%energy：12/26/37个增量方向；
- 最大相对feedbacketa约.0134，背景Lcondition约1.189。

能量保留比例不是后验KL阈值，也不是对每对象的保证；更不能把局部额外26个方向称为26个新独立可识别材料变量。

## 5. 尚未解决但可直接实验的问题

实际fullvoxelprior下，反馈响应是否低秩到足以抵消准备成本？二阶correction能否改善noise/modelbias条件下的完整材料图？未知参考与calibration是否占主导？curvedpriorcompletion是否比GMM/wavelet/现有data-consistentNN更有价值？这些是本轮研究留下的具体可判定假设，而不是以“开放难题”搁置。



---

<a id="section-15"></a>

# A23 路线竞争与裁决（独立阅读版）

## 1. 问题与当前证据

目标是三维矢量Maxwell的fast material imaging，不再研究currentranking、exchange或更准确的GNstep。参考物理为
\[
j=a(\chi)(e^{inc}+Gj),\quad L=I-aG,\quad J=SL^{-1}B.
\]
原项目A20的early/late结果主要是frozenGNdiagnostic；A21为oracle双侧机制；A22-R1只有固定32Dchart的分离/one-shot统计，完整复杂形状大量能量在chart外，totaldeploymenttime尚未建立。[P04–P10]

本轮真正完成的是源码阅读、文献审计、条件推导和独立8cellCPU验证，没有A23大规模成像或NN训练。

## 2. PRIMARY ROUTE

**Category A：projection-first、curvature-budgeted、one/few-pass material inverse。**

先用已知参考背景的forward/adjointfields直接构造或sketch材料–数据映射A，允许sourceanchoredOM、普通randomizedJ或exactadjoint作为最便宜实现；不要求保留O/P/M标签。

\[
x_1=D(y-y_b),\qquad
x_2=x_1-D\hat Q(x_1,x_1).
\]
Q由相对参考介质的首次追加反馈产生。使用χ坐标时还含真实极化率的a''项。保持全图材料表示或与truth无关的prior-conditionedfullp映射，不能只回到32Dchart。

**两个分支而不是一个教条。**
- 若Q的有效新数据方向低秩且高于noise/modelbudget，补充datajet空间。
- 若完整A已满行rank、或新方向无法经济压缩，不扩数据空间；只检验二阶inversecorrection是否在原数据空间里值得。
- 若二阶修正也不值得，保留linearadjoint/SVD/Wiener，并停止A23专属反馈模块。

最强理论：relativefeedbackidentity、finiteamplitudebound、精确sourceP删除、cacheddualconstruction、quadraticstat/后验损失界。主要未知：完整图像的实际质量–时间优势。

## 3. SECONDARY ROUTE

**解析Bayesian / GMM / 一次结构prox。** Gaussianprior用data-spacelinearposterior；少量多模态用mixture；边缘用wavelet/group或计费TV。可与Primary组合，但不是四类都开工。

先验证残余是可以预测的材料结构，而不是Maxwell/calibrationbias。若解析prior已足够，不训练NN。

## 4. HIGH-RISK / HIGH-REWARD

**Category B/D，必要时再C：curved physics–prior completion。**

prior/小NN生成弱材料b后，不固定强坐标a，而是用Maxwell二阶cross-feedback作解析recoil：
\[
a_2=a_0-\Sigma_s^{-1}U_s^TQ(V_sa_0+V_wb,V_sa_0+V_wb).
\]
局部强dataresidual由二阶降为三阶。真实全图b需完整Qaction或有界approximation；probabilistic版本还需要evidence/Jacobian，data-consistent不等于posterior-correct。

最近邻是nonlineardata-consistentNN [R15]，所以不是“首次沿非线性fibre补全”；机会在Maxwell特定便宜构造、明确误差界与fullwavecost/generalization。

## 5. 评分：立项判断，不是实验成绩

1低、5高。计算节省/成像潜力均是条件性预期；不作论文证据，不把各项相加制造伪客观总分。

| 路线 | 理论新意 | 成像潜力 | 节省潜力 | 大规模性 | 鲁棒性 | 数学可控 | 工程可行 | 发表潜力 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A0 exact/随机adjoint + linearWiener | 1 | 3 | 4 | 4 | 3 | 5 | 5 | 2 |
| A1 budgetedfeedbackfew-pass | 3 | 4 | 4 | 3 | 3 | 4 | 4 | 4 |
| A2 decoderbank/rationaldirect | 3 | 4 | 3 | 3 | 2 | 3 | 3 | 3 |
| A/B analyticGaussian/GMM/prox | 2 | 4 | 4 | 4 | 4 | 4 | 5 | 3 |
| B hard-splitNN | 1 | 3 | 3 | 4 | 2 | 2 | 4 | 2 |
| B/D curvedrecoil+smallpriorNN | 4 | 4 | 3 | 3 | 3 | 4 | 3 | 4 |
| C conditionalflow/diffusion | 2 | 4 | 1 | 2 | 2 | 2 | 2 | 3 |
| D rawOPMtoken/learnedclosure | 1 | 3 | 1 | 2 | 2 | 2 | 2 | 2 |
| 外部data-drivenMaxwellROM路线 | 3 | 4 | 3 | 3 | 3 | 3 | 2 | 4 |

最后一行是值得持续比较的独立竞争方向 [R06–R08]，不自动启动第三个大项目。其假设/数据采集模式与当前频域有耗backend不同。

## 6. 每条路线的支持、未知与淘汰条件

| 路线 | 最强支持 | 最大未知 | 最近竞争者 | Killer / 最便宜证伪 |
|---|---|---|---|---|
| A0 | exactJ=Z*B、标准Wiener | reference成本/OOD | Born/TSVD | strongnonlinearfullimage误差不够；四对象幅度扫描 |
| A1 | inverseerrorbound与tinycubic | 二阶低秩/实际time | vanillaIBS2+dressedBorn | 同A/Q输出相同却更贵；记录setup+online |
| A2 | scalar rational exact、localbankpathbound | hiddenSchurselfenergy/银行覆盖 | EBA/directROM | 两不同hidden介质同compresseddata；smallblockcounterexample |
| analyticprior | 解析Gaussian/GMM、oneprox | 残余是否prior可解释 | TV/PnP | posterior太非Gaussian或shapeprior错误；noNNresidualpilot |
| hardNN | 推断便宜 | hardlinearprotection破坏非线性data | nullspaceNN | f(a,b)cross-termtoy即失败；无须GPU |
| curvedNN | 强dataerrorOρ3 | fullpQ成本与OOD | nonlinearDCNN | 混合Q校正不比普通DC便宜；同容量消融 |
| flow/DPS | 多解posterior表示能力 | 校准/NFE/latent真实维数 | GMM/conditionalGaussian | 两成分mixture已足够或采样慢；小latentposterior比较 |
| OPMtoken/closure | 可表达feedback | 相对analyticbaseline的额外价值 | SOM-Net/poly | basisgauge不稳定或same-A SVD等价；无需新大数据 |
| dataROM | 已有直接MaxwellROM结果 | 有耗3D/采集兼容 | 已有R06本身 | 当前频点不足其time-domainmodel；先核数据合同 |

## 7. ROUTES TO KILL / DEFER

立即停止：NNcurrentranking/proposal、learnedfullresolvent、单纯OPM标签token化、通过更准确GNfidelity延续旧主线、把chart内分离直接升级fullimage。

暂缓：diffusion/flow、backgrounddecoderbank、强散射全局rationalinverse。除非分别获得真实多模态、可摊销背景变化、可观测transferheadroom，不能先投训练资源。

保留为control：Born、BP、genericROM/randomizedSVD、analyticpoly、inverseBorn2、SOM/CSI。这些不是需要“击败后删除”的旧代码，而是新研究不自欺的基准。

## 8. 只有三个先行假设

H1：实际sourceanchoring/cache/directadjoint能减少同质量encoder的总准备成本，而非只减rank。

H2：扣除localconstitutive、chart外部与nuisance后，有限幅度feedback修正确有fullimageheadroom；不要求一定新增数据维数。

H3：headroom在噪声/标定条件下仍转化为总time-to-acceptable-image Pareto优势，含fullverification与N次摊销。

H1败、H2成：可保留已有便宜operator实现，不保留OPM专属压缩。
H2败：停止二阶专属模块，保留linearphysics+prior。
H3败：不扩大训练/医学宣传；研究结果是明确cost/quality边界。
三个有正面证据，再进入小priorcomparison；不是自动四条路线同时开工。

## 9. 最终科研判断

最强的下一步不是“把OPM接上Flow”，而是先把**relativefeedback造成的有限幅度材料响应**做成一个可计费、可压缩、可检验的few-passinverse。若成功，curvedpriorcompletion才有坚实的物理接口。

这有strongTAP候选潜力，但本轮尚无full-image/time实证，不能宣布已达到强TAP。论文价值最终由一个真实Maxwellregime中的明确Pareto优势及可复核机制决定，不由16份文档或漂亮名称决定。



---

<a id="section-16"></a>

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



---

<a id="section-17"></a>

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



---

<a id="section-18"></a>

# A23 来源、版本与阅读边界

研究日期：2026-10-08。正文用 `[Pxx]` 指项目证据、`[B01]` 指用户提供的书、`[Rxx]` 指外部论文。数学推导以本包中的假设为准，引用不表示被引用作者证明过本文的新组合。

## 项目版本

A20/A22-R1 的代码审计固定到：
`migodam/a20-opm-imaging@b85a29a51f4ea7b4d93617e827d88e23933b89df`，
由 `a22-r1-subspace-separation` 分支解析获得。

A22 初始交接按用户指定：
`4dd4a9fa69d4272f35a6b93d8455f77cb139187b`。

下面的“已读”指通过 GitHub 连接器读取文本，不表示重新运行原实验。

| ID | 来源及定位 | 阅读与证据范围 |
|---|---|---|
| P00 | 用户附件《A23 — Strong-TAP Theory and Architecture Exploration》，2,290 行 | 全部任务要求；不是实验或优先权证据 |
| P01 | [`src/a20/opm.py`](https://github.com/migodam/a20-opm-imaging/blob/b85a29a51f4ea7b4d93617e827d88e23933b89df/src/a20/opm.py)，1–250 行 | 已读实际 SchurFeedback、build_seeds、分流递推、Projection 开头 |
| P02 | [`src/a20/backend.py`](https://github.com/migodam/a20-opm-imaging/blob/b85a29a51f4ea7b4d93617e827d88e23933b89df/src/a20/backend.py)，1–300 行 | 已读规范化、实材料坐标、B/B*、full-state、dense L、compressed_B |
| P03 | [`vendor/a17/a9_engine.py`](https://github.com/migodam/a20-opm-imaging/blob/b85a29a51f4ea7b4d93617e827d88e23933b89df/vendor/a17/a9_engine.py)，1–230 行 | 已读 DDA/Green/极化率定义与计费合同；不是连续 Maxwell 误差证书 |
| P04 | [`RESEARCH_REPORT_ZH.md`](https://github.com/migodam/a20-opm-imaging/blob/b85a29a51f4ea7b4d93617e827d88e23933b89df/RESEARCH_REPORT_ZH.md) | 已读 A20 真实 gate、early/late、未运行项、QP 失败与费用 |
| P05 | [`LATE_STATE_SEED_ANATOMY.md`](https://github.com/migodam/a20-opm-imaging/blob/b85a29a51f4ea7b4d93617e827d88e23933b89df/LATE_STATE_SEED_ANATOMY.md) | 已读 A20-R1，不能将高 primal capture 当作 GN optimum 保证 |
| P06 | [`RELEASE_NOTES_A21.md`](https://github.com/migodam/a20-opm-imaging/blob/b85a29a51f4ea7b4d93617e827d88e23933b89df/RELEASE_NOTES_A21.md) | 已读五个 exposed states 的 oracle 双侧结果，非部署算法 |
| P07 | [`A22_GPT_HANDOFF.md`](https://github.com/migodam/a20-opm-imaging/blob/4dd4a9fa69d4272f35a6b93d8455f77cb139187b/A22_GPT_HANDOFF.md)，前 170 行 | 已读初始结论、A2/A3 对比、NOT_RUN、证据索引 |
| P08 | [`A22_R1_GPT_HANDOFF.md`](https://github.com/migodam/a20-opm-imaging/blob/b85a29a51f4ea7b4d93617e827d88e23933b89df/A22_R1_GPT_HANDOFF.md) | 读取交接主要结果与边界；大响应未逐项复算底层表格 |
| P09 | [`CHART_EXTERIOR_AUDIT.md`](https://github.com/migodam/a20-opm-imaging/blob/b85a29a51f4ea7b4d93617e827d88e23933b89df/CHART_EXTERIOR_AUDIT.md) | 已读四个原对象的全图材料能量与 chart 外部能量 |
| P10 | [`CACHED_ONE_SHOT_RUNTIME.md`](https://github.com/migodam/a20-opm-imaging/blob/b85a29a51f4ea7b4d93617e827d88e23933b89df/CACHED_ONE_SHOT_RUNTIME.md) | 已读 cached kernel 与未建立的总部署计时边界 |
| P11 | [A18-B README](https://github.com/migodam/a18-b-maxwell-feedback-closure/blob/main/README.md)；[PRIMARY_REVIEW](https://github.com/migodam/a18-b-maxwell-feedback-closure/blob/main/research/PRIMARY_REVIEW.md) | 已读原结论与详细科学审查；main 按本次读取，未固定分支 commit；README blob b0afab3b773ad4abd5cc3fc2647f5e5bef1d4948，review blob 1679799484af0879aa8c595e53b6a6cb8a0ff34d |
| P12 | [A18 proposal README](https://github.com/migodam/a18-physics-native-current-proposal/blob/main/README.md) | 已读 NO_GO_BOTH、学习 gate 与无成像结论；未复读全部原始训练表。blob 6fa65de346f2e7a62fb004b7dfc70ee776eb9781 |
| P13 | [A19 README](https://github.com/migodam/a19-task-adaptive-feedback/blob/main/README.md) | 已读 NO_GO_LARGER_STUDY、G3 与 cost 条件、无 nonlinear imaging。blob f51d11b9fbe44f931b66a9ee5c959d712146ddcc |
| P14 | [`docs/PUBLIC_PACKAGE_INDEX.md`](https://github.com/migodam/a20-opm-imaging/blob/b85a29a51f4ea7b4d93617e827d88e23933b89df/docs/PUBLIC_PACKAGE_INDEX.md) | 已读 runtime/offline 数据边界、Q 的历史 support 风险、held-receiver 未建立 |

本包没有重新下载/运行 A20–A22 的 teacher、训练集或完整重建。A17 的当前代数以任务书及 vendored A9 内核核对；没有声称审阅 A17 全部论文或全部历史实验。

## 用户提供的教材

**[B01]** Xudong Chen. *Computational Methods for Electromagnetic Inverse Scattering*. Wiley–IEEE Press, 2018. ISBN 9781119311980。用户已上传 PDF，本包不重新分发。

实际重点阅读：§2.1 时间约定；§2.9 离散矢量 DDA；§2.11 互易性；§6.2.3 extended Born；§6.2.4 back-propagation；§6.4.1–6.4.3 SOM/TSOM/FFT 改进。打印页 131–133、149–151、161–163 对应 PDF 页 150–152、168–170、180–182。图 6.13（打印页 162）显示 TSOM 中观测弱子空间与传播强子空间的交集：这本身已经是 observation/propagation 分解思想，不能重新包装成 O/P/M 首创。

## 外部论文

“摘要”表示只据作者/出版社/大学资料或论文摘要判断，不把它写成已审核所有证明。网络抓取失败保留为访问边界。下列简述集中在本表；正文的算法比较与数学推论是本轮分析。

| ID | 论文、标识及主来源 | 本轮阅读层级 |
|---|---|---|
| R01 | X. Chen, “Subspace-based optimization method for solving inverse-scattering problems,” JOSA A 26, 1022–1026 (2009). DOI [10.1364/JOSAA.26.001022](https://doi.org/10.1364/JOSAA.26.001022)；[PubMed](https://pubmed.ncbi.nlm.nih.gov/19340278/) | 摘要；方法细节另由 B01 支持 |
| R02 | Y. Liu et al., “SOM-Net: Unrolling the Subspace-based Optimization for Solving Full-wave Inverse Scattering Problems.” [arXiv:2209.03567v2](https://arxiv.org/abs/2209.03567) | PDF 正文 §II，含输入、四个 unrolled blocks、解析材料更新及多变量损失；2D TM。不是任意 3D 跨几何保证 |
| R03 | Z. Wei and X. Chen, “Physics-Inspired Convolutional Neural Network for Solving Full-Wave Inverse Scattering Problems,” IEEE TAP 67(9), 6138–6148 (2019). DOI [10.1109/TAP.2019.2922779](https://doi.org/10.1109/TAP.2019.2922779)；[作者同题报告](https://fit.fudan.edu.cn/En/Data/View/3272) | 作者大学报告与 R02 正文引用；IEEE DOI 全文抓取失败。不能据此声称已逐页审核 ICLM |
| R04 | K. Kilgore, S. Moskow, J. C. Schotland, “Convergence of the Born and inverse Born series for electromagnetic scattering,” Applicable Analysis 96(10), 1737–1748 (2017). DOI [10.1080/00036811.2017.1292349](https://doi.org/10.1080/00036811.2017.1292349)；[Drexel](https://researchdiscovery.drexel.edu/esploro/outputs/journalArticle/Convergence-of-the-Born-and-inverse/991019167764504721) | 出版社及作者大学摘要；足以确认电磁 inverse Born 及收敛理论已有先例，未审核完整常数 |
| R05 | F. Hettlich and W. Rundell, “A Second Degree Method for Nonlinear Inverse Problems,” SIAM J. Numer. Anal. 37(2), 587–620 (1999). DOI [10.1137/S0036142998341246](https://doi.org/10.1137/S0036142998341246) | 出版社摘要；二阶 predictor–corrector 不是新思想 |
| R06 | L. Borcea, Y. Liu, J. Zimmerling, “Electromagnetic inverse wave scattering in anisotropic media via reduced order modeling,” JCP 515, 113272 (2024). DOI [10.1016/j.jcp.2024.113272](https://doi.org/10.1016/j.jcp.2024.113272)；[正文](https://arxiv.org/html/2403.03844v1) | HTML 正文及出版社；lossless、data-driven transient ROM；定量反演仍有 optimization，数值研究降为二维，不是已验证的大型有耗 3D one-shot |
| R07 | L. Borcea, V. Druskin, J. Zimmerling, “A reduced order model approach to inverse scattering in lossy layered media.” [arXiv:2012.00861](https://arxiv.org/abs/2012.00861) | 摘要；有耗层状电磁，不等于任意三维异质介质 |
| R08 | L. Borcea, V. Druskin, A. Mamonov, M. Zaslavsky, “Untangling the nonlinearity in inverse scattering with data-driven reduced order models.” [arXiv:1704.08375](https://arxiv.org/abs/1704.08375) | 摘要与引言级；声学 data-to-Born，不能未经证明移植全部物理 |
| R09 | N. Halko, P.-G. Martinsson, J. Tropp, “Finding Structure with Randomness: Probabilistic Algorithms for Constructing Approximate Matrix Decompositions,” SIAM Review 53(2), 217–288 (2011). DOI [10.1137/090771806](https://doi.org/10.1137/090771806)；[arXiv:0909.4061](https://arxiv.org/abs/0909.4061) | 摘要及已核对出版信息；本包不转引未经核对的概率常数 |
| R10 | P. Benner, S. Gugercin, K. Willcox, “A Survey of Projection-Based Model Reduction Methods for Parametric Dynamical Systems,” SIAM Review (2015). DOI [10.1137/130932715](https://doi.org/10.1137/130932715) | 出版社摘要；ROM/offline-online 为已知理论类别 |
| R11 | R. Becker and R. Rannacher, “An optimal control approach to a posteriori error estimation in finite element methods,” Acta Numerica 10, 1–102 (2001). DOI [10.1017/S0962492901000010](https://doi.org/10.1017/S0962492901000010) | 出版社摘要；dual-weighted residual 先例 |
| R12 | T. Cui et al., “Likelihood-informed dimension reduction for nonlinear inverse problems,” Inverse Problems 30, 114015 (2014). [arXiv:1403.4680](https://arxiv.org/abs/1403.4680) | 摘要；prior-relative likelihood subspaces，非任意 SVD 的后验独立定理 |
| R13 | J. Alsing and B. Wandelt, “Generalized massive optimal data compression,” MNRAS Letters 476, L60–L64 (2018). DOI [10.1093/mnrasl/sly029](https://doi.org/10.1093/mnrasl/sly029)；[arXiv:1712.00012](https://arxiv.org/abs/1712.00012) | 摘要；score/Fisher 局部压缩先例 |
| R14 | J. Schwab, S. Antholzer, M. Haltmeier, “Deep Null Space Learning for Inverse Problems: Convergence Analysis and Rates,” Inverse Problems 35, 025008 (2019). DOI [10.1088/1361-6420/aaf14a](https://doi.org/10.1088/1361-6420/aaf14a)；[arXiv:1806.06137](https://arxiv.org/abs/1806.06137) | 作者预印本摘要 |
| R15 | Y. E. Boink, M. Haltmeier, S. Holman, J. Schwab, “Data-consistent neural networks for solving nonlinear inverse problems,” Inverse Problems and Imaging 17(1), 203–229 (2023). DOI [10.3934/ipi.2022037](https://doi.org/10.3934/ipi.2022037)；[arXiv:2003.11253](https://arxiv.org/abs/2003.11253) | 出版社与作者摘要；本轮 HTML 全文抓取失败，非线性 data consistency 已有直接先例 |
| R16 | J. Adler and O. Öktem, “Learned Primal-Dual Reconstruction,” IEEE TMI 37(6), 1322–1332 (2018). DOI [10.1109/TMI.2018.2799231](https://doi.org/10.1109/TMI.2018.2799231)；[arXiv:1707.06474](https://arxiv.org/abs/1707.06474) | 摘要；学习 primal-dual 不是 Maxwell 专属新概念 |
| R17 | Z. Li et al., “Fourier Neural Operator for Parametric Partial Differential Equations.” [arXiv:2010.08895](https://arxiv.org/abs/2010.08895) | 作者摘要；原论文例题不是 Maxwell 成像，不能搬用其速度倍率 |
| R18 | S. V. Venkatakrishnan, C. Bouman, B. Wohlberg, “Plug-and-Play Priors for Model Based Reconstruction” (2013). [Purdue 原始报告](https://docs.lib.purdue.edu/ecetr/448/) | 大学原始报告摘要 |
| R19 | E. Reehorst and P. Schniter, “Regularization by Denoising: Clarifications and New Interpretations.” [arXiv:1806.02296](https://arxiv.org/abs/1806.02296) | 作者摘要；一般 denoiser 不自动是某个显式势能的梯度 |
| R20 | H. Chung et al., “Diffusion Posterior Sampling for General Noisy Inverse Problems.” [arXiv:2209.14687](https://arxiv.org/abs/2209.14687) | 作者摘要；非线性 inverse problem 的生成先例，非本项目 Maxwell 验证 |
| R21 | M. Pourya, B. El Rawas, M. Unser, “FLOWER: A Flow-Matching Solver for Inverse Problems.” [arXiv:2509.26287](https://arxiv.org/abs/2509.26287) | 作者摘要（v2，2026-02-22）；linear inverse problems 的 flow、约束修正与 posterior approximation，非强散射 Maxwell 验证 |
| R22 | J. Kim, B. S. Kim, J. C. Ye, “FlowDPS: Flow-Driven Posterior Sampling for Inverse Problems.” [arXiv:2503.08136](https://arxiv.org/abs/2503.08136) | 作者摘要；展示的是四类线性逆问题，不是本项目强散射证明 |
| R23 | D. Ninkovic et al., “Patient-Specific Background Model Estimation for Effective Brain Stroke Microwave Imaging,” IEEE TMI 45(6), 2662–2673 (2026). DOI [10.1109/TMI.2026.3660568](https://doi.org/10.1109/TMI.2026.3660568)；[PubMed](https://pubmed.ncbi.nlm.nih.gov/41632681/) | PubMed 作者摘要与大学出版记录；使用头形、粗略皮肤/脂肪知识，验证为 anthropomorphic phantom |
| R24 | “An Experimental 10-Port Microwave System for Brain Stroke Diagnosis—Potentials and Limitations,” Sensors 25(14), 4360 (2025). DOI [10.3390/s25144360](https://doi.org/10.3390/s25144360) | 出版社搜索可读摘要；直接打开遇 429。仅用其系统/phantom/有限几何范围，不作临床准确率外推 |
| R25 | J. Wu et al., “Non-Invasive Differential Temperature Monitoring Using Sensor Array for Microwave Hyperthermia Applications: A Subspace-Based Approach,” JSAN 14(1), 19 (2025). DOI [10.3390/jsan14010019](https://doi.org/10.3390/jsan14010019) | 出版社摘要、引言、结论；2D 数值乳房模型，SOM/固定 Green/TwIST，不是新 A23 临床证据 |
| R26 | “Microwave imaging for monitoring breast cancer treatment: A pilot study,” Medical Physics 50, 7118–7129 (2023). DOI [10.1002/mp.16756](https://doi.org/10.1002/mp.16756) | 出版社摘要；用于 repeated-monitoring 应用背景，不搬用为 full-wave quantitative tomography 验证 |
| R27 | [MammoWave 临床研究，PubMed 37450545](https://pubmed.ncbi.nlm.nih.gov/37450545/) (2023) | 摘要级；检查/分类终点不等于完整介电图像的 NRMSE |
| R28 | “MFFSOM-Net: Multi-Frequency Fusion Subspace Optimization Network for Inverse Scattering,” IEEE AWPL, early access, 24 Aug 2026. DOI [10.1109/LAWP.2026.3727140](https://doi.org/10.1109/LAWP.2026.3727140) | IEEE 搜索结果中的完整摘要与元数据；直接打开失败，未审核全文。已覆盖多频 current restoration、EFIE 更新与跨 stage 融合 |
| R29 | “Padé approximants of the Born series of electromagnetic scattering by a diffraction grating,” Physical Review A 109, 033522 (2024). DOI [10.1103/PhysRevA.109.033522](https://doi.org/10.1103/PhysRevA.109.033522) | 出版社摘要；强散射矢量 forward Padé，不自动给出稳定 inverse decoder |
| R30 | “Input-Tailored System-Theoretic Model Order Reduction for Quadratic-Bilinear Systems,” SIAM J. Sci. Comput. DOI [10.1137/18M1216699](https://doi.org/10.1137/18M1216699) | 出版社检索元数据；用于标识 quadratic-bilinear/moment reduction 的已知理论邻域，不据此推断具体定理常数 |

## 优先权审计边界

这是一轮有明确最近邻的研究审计，不是所有数据库的穷尽优先权证明。尤其需要投稿前继续逐页比较 R04、R15 与 quadratic-bilinear/Volterra 压缩文献。当前可以排除“首次 inverse Born”“首次 physics-native/current NN”“首次 nonlinear data-consistent completion”等宽泛声称；不能据“未检出同一标题”宣布 A23 的组合全球首创。

本包不包含第三方论文全文、教材 PDF、上游训练集或用户账号凭据。



---

<a id="section-19"></a>

# 验证与阅读指南

本包完成了16项指定交付，并另有统一记号、来源审计和可重跑CPU检查。三个独立入口是 executive、route decision、Codex spec。

数学阅读顺序：Redundancy → Cheap operators → One-shot theory → Bayesian theory → Ledger。
算法阅读顺序：Executive → Complexity/Competitors → Minimal experiments → Codex spec。
先验与架构：Priors → Symmetry → NN architectures。
定位与投稿：Medical applicability → Novelty audit → Route decision。

## 已执行的检查

`validate_theory.py`：Schur、P删除、PMidentity、DWR、独立8cellvectorDDA、finiteamplitudeorders、quadraticcovariance、correlatedprior、curvedfibre。
`validate_extra.py`：passivepolarizabilitydisk、exactinverseconversion、unitarygauge。
均为CPU/NumPy，全部 assertions 通过。

Markdown交付检查：16个指定文件均存在且非空；codefence、inline/display math delimiter配对；本包显式本地Markdown链接目标存在；未检测到Unicode replacement字符。

这些检查不是数学定理的形式化验证；也不是上游实验重现、posteriorcalibration、fullimagequality或speedup测试。网页可读摘要与全文层级在SOURCES明确区分。

## 原始证据

`validation/THEORY_VALIDATION.json`和`validation/EXTRA_VALIDATION.json`是实测输出；code与raw结果一起提供。wall_seconds仅为小检查耗时，不用于任何成像速度宣称。

`RESEARCH_MANIFEST.json`列出交付文件SHA-256及上游pin；不包含账户信息、第三方PDF或原项目训练数据。
