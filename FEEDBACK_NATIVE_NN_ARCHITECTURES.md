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
