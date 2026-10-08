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
