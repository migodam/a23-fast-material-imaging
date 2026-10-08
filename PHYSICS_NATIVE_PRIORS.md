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
