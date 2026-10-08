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
