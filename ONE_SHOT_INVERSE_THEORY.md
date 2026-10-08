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
