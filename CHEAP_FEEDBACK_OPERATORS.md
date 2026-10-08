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
