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
