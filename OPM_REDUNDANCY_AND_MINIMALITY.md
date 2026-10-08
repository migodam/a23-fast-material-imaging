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
