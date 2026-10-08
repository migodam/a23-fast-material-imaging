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
