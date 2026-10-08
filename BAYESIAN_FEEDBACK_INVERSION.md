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
