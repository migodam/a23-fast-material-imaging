# A23 来源、版本与阅读边界

研究日期：2026-10-08。正文用 `[Pxx]` 指项目证据、`[B01]` 指用户提供的书、`[Rxx]` 指外部论文。数学推导以本包中的假设为准，引用不表示被引用作者证明过本文的新组合。

## 项目版本

A20/A22-R1 的代码审计固定到：
`migodam/a20-opm-imaging@b85a29a51f4ea7b4d93617e827d88e23933b89df`，
由 `a22-r1-subspace-separation` 分支解析获得。

A22 初始交接按用户指定：
`4dd4a9fa69d4272f35a6b93d8455f77cb139187b`。

下面的“已读”指通过 GitHub 连接器读取文本，不表示重新运行原实验。

| ID | 来源及定位 | 阅读与证据范围 |
|---|---|---|
| P00 | 用户附件《A23 — Strong-TAP Theory and Architecture Exploration》，2,290 行 | 全部任务要求；不是实验或优先权证据 |
| P01 | [`src/a20/opm.py`](https://github.com/migodam/a20-opm-imaging/blob/b85a29a51f4ea7b4d93617e827d88e23933b89df/src/a20/opm.py)，1–250 行 | 已读实际 SchurFeedback、build_seeds、分流递推、Projection 开头 |
| P02 | [`src/a20/backend.py`](https://github.com/migodam/a20-opm-imaging/blob/b85a29a51f4ea7b4d93617e827d88e23933b89df/src/a20/backend.py)，1–300 行 | 已读规范化、实材料坐标、B/B*、full-state、dense L、compressed_B |
| P03 | [`vendor/a17/a9_engine.py`](https://github.com/migodam/a20-opm-imaging/blob/b85a29a51f4ea7b4d93617e827d88e23933b89df/vendor/a17/a9_engine.py)，1–230 行 | 已读 DDA/Green/极化率定义与计费合同；不是连续 Maxwell 误差证书 |
| P04 | [`RESEARCH_REPORT_ZH.md`](https://github.com/migodam/a20-opm-imaging/blob/b85a29a51f4ea7b4d93617e827d88e23933b89df/RESEARCH_REPORT_ZH.md) | 已读 A20 真实 gate、early/late、未运行项、QP 失败与费用 |
| P05 | [`LATE_STATE_SEED_ANATOMY.md`](https://github.com/migodam/a20-opm-imaging/blob/b85a29a51f4ea7b4d93617e827d88e23933b89df/LATE_STATE_SEED_ANATOMY.md) | 已读 A20-R1，不能将高 primal capture 当作 GN optimum 保证 |
| P06 | [`RELEASE_NOTES_A21.md`](https://github.com/migodam/a20-opm-imaging/blob/b85a29a51f4ea7b4d93617e827d88e23933b89df/RELEASE_NOTES_A21.md) | 已读五个 exposed states 的 oracle 双侧结果，非部署算法 |
| P07 | [`A22_GPT_HANDOFF.md`](https://github.com/migodam/a20-opm-imaging/blob/4dd4a9fa69d4272f35a6b93d8455f77cb139187b/A22_GPT_HANDOFF.md)，前 170 行 | 已读初始结论、A2/A3 对比、NOT_RUN、证据索引 |
| P08 | [`A22_R1_GPT_HANDOFF.md`](https://github.com/migodam/a20-opm-imaging/blob/b85a29a51f4ea7b4d93617e827d88e23933b89df/A22_R1_GPT_HANDOFF.md) | 读取交接主要结果与边界；大响应未逐项复算底层表格 |
| P09 | [`CHART_EXTERIOR_AUDIT.md`](https://github.com/migodam/a20-opm-imaging/blob/b85a29a51f4ea7b4d93617e827d88e23933b89df/CHART_EXTERIOR_AUDIT.md) | 已读四个原对象的全图材料能量与 chart 外部能量 |
| P10 | [`CACHED_ONE_SHOT_RUNTIME.md`](https://github.com/migodam/a20-opm-imaging/blob/b85a29a51f4ea7b4d93617e827d88e23933b89df/CACHED_ONE_SHOT_RUNTIME.md) | 已读 cached kernel 与未建立的总部署计时边界 |
| P11 | [A18-B README](https://github.com/migodam/a18-b-maxwell-feedback-closure/blob/main/README.md)；[PRIMARY_REVIEW](https://github.com/migodam/a18-b-maxwell-feedback-closure/blob/main/research/PRIMARY_REVIEW.md) | 已读原结论与详细科学审查；main 按本次读取，未固定分支 commit；README blob b0afab3b773ad4abd5cc3fc2647f5e5bef1d4948，review blob 1679799484af0879aa8c595e53b6a6cb8a0ff34d |
| P12 | [A18 proposal README](https://github.com/migodam/a18-physics-native-current-proposal/blob/main/README.md) | 已读 NO_GO_BOTH、学习 gate 与无成像结论；未复读全部原始训练表。blob 6fa65de346f2e7a62fb004b7dfc70ee776eb9781 |
| P13 | [A19 README](https://github.com/migodam/a19-task-adaptive-feedback/blob/main/README.md) | 已读 NO_GO_LARGER_STUDY、G3 与 cost 条件、无 nonlinear imaging。blob f51d11b9fbe44f931b66a9ee5c959d712146ddcc |
| P14 | [`docs/PUBLIC_PACKAGE_INDEX.md`](https://github.com/migodam/a20-opm-imaging/blob/b85a29a51f4ea7b4d93617e827d88e23933b89df/docs/PUBLIC_PACKAGE_INDEX.md) | 已读 runtime/offline 数据边界、Q 的历史 support 风险、held-receiver 未建立 |

本包没有重新下载/运行 A20–A22 的 teacher、训练集或完整重建。A17 的当前代数以任务书及 vendored A9 内核核对；没有声称审阅 A17 全部论文或全部历史实验。

## 用户提供的教材

**[B01]** Xudong Chen. *Computational Methods for Electromagnetic Inverse Scattering*. Wiley–IEEE Press, 2018. ISBN 9781119311980。用户已上传 PDF，本包不重新分发。

实际重点阅读：§2.1 时间约定；§2.9 离散矢量 DDA；§2.11 互易性；§6.2.3 extended Born；§6.2.4 back-propagation；§6.4.1–6.4.3 SOM/TSOM/FFT 改进。打印页 131–133、149–151、161–163 对应 PDF 页 150–152、168–170、180–182。图 6.13（打印页 162）显示 TSOM 中观测弱子空间与传播强子空间的交集：这本身已经是 observation/propagation 分解思想，不能重新包装成 O/P/M 首创。

## 外部论文

“摘要”表示只据作者/出版社/大学资料或论文摘要判断，不把它写成已审核所有证明。网络抓取失败保留为访问边界。下列简述集中在本表；正文的算法比较与数学推论是本轮分析。

| ID | 论文、标识及主来源 | 本轮阅读层级 |
|---|---|---|
| R01 | X. Chen, “Subspace-based optimization method for solving inverse-scattering problems,” JOSA A 26, 1022–1026 (2009). DOI [10.1364/JOSAA.26.001022](https://doi.org/10.1364/JOSAA.26.001022)；[PubMed](https://pubmed.ncbi.nlm.nih.gov/19340278/) | 摘要；方法细节另由 B01 支持 |
| R02 | Y. Liu et al., “SOM-Net: Unrolling the Subspace-based Optimization for Solving Full-wave Inverse Scattering Problems.” [arXiv:2209.03567v2](https://arxiv.org/abs/2209.03567) | PDF 正文 §II，含输入、四个 unrolled blocks、解析材料更新及多变量损失；2D TM。不是任意 3D 跨几何保证 |
| R03 | Z. Wei and X. Chen, “Physics-Inspired Convolutional Neural Network for Solving Full-Wave Inverse Scattering Problems,” IEEE TAP 67(9), 6138–6148 (2019). DOI [10.1109/TAP.2019.2922779](https://doi.org/10.1109/TAP.2019.2922779)；[作者同题报告](https://fit.fudan.edu.cn/En/Data/View/3272) | 作者大学报告与 R02 正文引用；IEEE DOI 全文抓取失败。不能据此声称已逐页审核 ICLM |
| R04 | K. Kilgore, S. Moskow, J. C. Schotland, “Convergence of the Born and inverse Born series for electromagnetic scattering,” Applicable Analysis 96(10), 1737–1748 (2017). DOI [10.1080/00036811.2017.1292349](https://doi.org/10.1080/00036811.2017.1292349)；[Drexel](https://researchdiscovery.drexel.edu/esploro/outputs/journalArticle/Convergence-of-the-Born-and-inverse/991019167764504721) | 出版社及作者大学摘要；足以确认电磁 inverse Born 及收敛理论已有先例，未审核完整常数 |
| R05 | F. Hettlich and W. Rundell, “A Second Degree Method for Nonlinear Inverse Problems,” SIAM J. Numer. Anal. 37(2), 587–620 (1999). DOI [10.1137/S0036142998341246](https://doi.org/10.1137/S0036142998341246) | 出版社摘要；二阶 predictor–corrector 不是新思想 |
| R06 | L. Borcea, Y. Liu, J. Zimmerling, “Electromagnetic inverse wave scattering in anisotropic media via reduced order modeling,” JCP 515, 113272 (2024). DOI [10.1016/j.jcp.2024.113272](https://doi.org/10.1016/j.jcp.2024.113272)；[正文](https://arxiv.org/html/2403.03844v1) | HTML 正文及出版社；lossless、data-driven transient ROM；定量反演仍有 optimization，数值研究降为二维，不是已验证的大型有耗 3D one-shot |
| R07 | L. Borcea, V. Druskin, J. Zimmerling, “A reduced order model approach to inverse scattering in lossy layered media.” [arXiv:2012.00861](https://arxiv.org/abs/2012.00861) | 摘要；有耗层状电磁，不等于任意三维异质介质 |
| R08 | L. Borcea, V. Druskin, A. Mamonov, M. Zaslavsky, “Untangling the nonlinearity in inverse scattering with data-driven reduced order models.” [arXiv:1704.08375](https://arxiv.org/abs/1704.08375) | 摘要与引言级；声学 data-to-Born，不能未经证明移植全部物理 |
| R09 | N. Halko, P.-G. Martinsson, J. Tropp, “Finding Structure with Randomness: Probabilistic Algorithms for Constructing Approximate Matrix Decompositions,” SIAM Review 53(2), 217–288 (2011). DOI [10.1137/090771806](https://doi.org/10.1137/090771806)；[arXiv:0909.4061](https://arxiv.org/abs/0909.4061) | 摘要及已核对出版信息；本包不转引未经核对的概率常数 |
| R10 | P. Benner, S. Gugercin, K. Willcox, “A Survey of Projection-Based Model Reduction Methods for Parametric Dynamical Systems,” SIAM Review (2015). DOI [10.1137/130932715](https://doi.org/10.1137/130932715) | 出版社摘要；ROM/offline-online 为已知理论类别 |
| R11 | R. Becker and R. Rannacher, “An optimal control approach to a posteriori error estimation in finite element methods,” Acta Numerica 10, 1–102 (2001). DOI [10.1017/S0962492901000010](https://doi.org/10.1017/S0962492901000010) | 出版社摘要；dual-weighted residual 先例 |
| R12 | T. Cui et al., “Likelihood-informed dimension reduction for nonlinear inverse problems,” Inverse Problems 30, 114015 (2014). [arXiv:1403.4680](https://arxiv.org/abs/1403.4680) | 摘要；prior-relative likelihood subspaces，非任意 SVD 的后验独立定理 |
| R13 | J. Alsing and B. Wandelt, “Generalized massive optimal data compression,” MNRAS Letters 476, L60–L64 (2018). DOI [10.1093/mnrasl/sly029](https://doi.org/10.1093/mnrasl/sly029)；[arXiv:1712.00012](https://arxiv.org/abs/1712.00012) | 摘要；score/Fisher 局部压缩先例 |
| R14 | J. Schwab, S. Antholzer, M. Haltmeier, “Deep Null Space Learning for Inverse Problems: Convergence Analysis and Rates,” Inverse Problems 35, 025008 (2019). DOI [10.1088/1361-6420/aaf14a](https://doi.org/10.1088/1361-6420/aaf14a)；[arXiv:1806.06137](https://arxiv.org/abs/1806.06137) | 作者预印本摘要 |
| R15 | Y. E. Boink, M. Haltmeier, S. Holman, J. Schwab, “Data-consistent neural networks for solving nonlinear inverse problems,” Inverse Problems and Imaging 17(1), 203–229 (2023). DOI [10.3934/ipi.2022037](https://doi.org/10.3934/ipi.2022037)；[arXiv:2003.11253](https://arxiv.org/abs/2003.11253) | 出版社与作者摘要；本轮 HTML 全文抓取失败，非线性 data consistency 已有直接先例 |
| R16 | J. Adler and O. Öktem, “Learned Primal-Dual Reconstruction,” IEEE TMI 37(6), 1322–1332 (2018). DOI [10.1109/TMI.2018.2799231](https://doi.org/10.1109/TMI.2018.2799231)；[arXiv:1707.06474](https://arxiv.org/abs/1707.06474) | 摘要；学习 primal-dual 不是 Maxwell 专属新概念 |
| R17 | Z. Li et al., “Fourier Neural Operator for Parametric Partial Differential Equations.” [arXiv:2010.08895](https://arxiv.org/abs/2010.08895) | 作者摘要；原论文例题不是 Maxwell 成像，不能搬用其速度倍率 |
| R18 | S. V. Venkatakrishnan, C. Bouman, B. Wohlberg, “Plug-and-Play Priors for Model Based Reconstruction” (2013). [Purdue 原始报告](https://docs.lib.purdue.edu/ecetr/448/) | 大学原始报告摘要 |
| R19 | E. Reehorst and P. Schniter, “Regularization by Denoising: Clarifications and New Interpretations.” [arXiv:1806.02296](https://arxiv.org/abs/1806.02296) | 作者摘要；一般 denoiser 不自动是某个显式势能的梯度 |
| R20 | H. Chung et al., “Diffusion Posterior Sampling for General Noisy Inverse Problems.” [arXiv:2209.14687](https://arxiv.org/abs/2209.14687) | 作者摘要；非线性 inverse problem 的生成先例，非本项目 Maxwell 验证 |
| R21 | M. Pourya, B. El Rawas, M. Unser, “FLOWER: A Flow-Matching Solver for Inverse Problems.” [arXiv:2509.26287](https://arxiv.org/abs/2509.26287) | 作者摘要（v2，2026-02-22）；linear inverse problems 的 flow、约束修正与 posterior approximation，非强散射 Maxwell 验证 |
| R22 | J. Kim, B. S. Kim, J. C. Ye, “FlowDPS: Flow-Driven Posterior Sampling for Inverse Problems.” [arXiv:2503.08136](https://arxiv.org/abs/2503.08136) | 作者摘要；展示的是四类线性逆问题，不是本项目强散射证明 |
| R23 | D. Ninkovic et al., “Patient-Specific Background Model Estimation for Effective Brain Stroke Microwave Imaging,” IEEE TMI 45(6), 2662–2673 (2026). DOI [10.1109/TMI.2026.3660568](https://doi.org/10.1109/TMI.2026.3660568)；[PubMed](https://pubmed.ncbi.nlm.nih.gov/41632681/) | PubMed 作者摘要与大学出版记录；使用头形、粗略皮肤/脂肪知识，验证为 anthropomorphic phantom |
| R24 | “An Experimental 10-Port Microwave System for Brain Stroke Diagnosis—Potentials and Limitations,” Sensors 25(14), 4360 (2025). DOI [10.3390/s25144360](https://doi.org/10.3390/s25144360) | 出版社搜索可读摘要；直接打开遇 429。仅用其系统/phantom/有限几何范围，不作临床准确率外推 |
| R25 | J. Wu et al., “Non-Invasive Differential Temperature Monitoring Using Sensor Array for Microwave Hyperthermia Applications: A Subspace-Based Approach,” JSAN 14(1), 19 (2025). DOI [10.3390/jsan14010019](https://doi.org/10.3390/jsan14010019) | 出版社摘要、引言、结论；2D 数值乳房模型，SOM/固定 Green/TwIST，不是新 A23 临床证据 |
| R26 | “Microwave imaging for monitoring breast cancer treatment: A pilot study,” Medical Physics 50, 7118–7129 (2023). DOI [10.1002/mp.16756](https://doi.org/10.1002/mp.16756) | 出版社摘要；用于 repeated-monitoring 应用背景，不搬用为 full-wave quantitative tomography 验证 |
| R27 | [MammoWave 临床研究，PubMed 37450545](https://pubmed.ncbi.nlm.nih.gov/37450545/) (2023) | 摘要级；检查/分类终点不等于完整介电图像的 NRMSE |
| R28 | “MFFSOM-Net: Multi-Frequency Fusion Subspace Optimization Network for Inverse Scattering,” IEEE AWPL, early access, 24 Aug 2026. DOI [10.1109/LAWP.2026.3727140](https://doi.org/10.1109/LAWP.2026.3727140) | IEEE 搜索结果中的完整摘要与元数据；直接打开失败，未审核全文。已覆盖多频 current restoration、EFIE 更新与跨 stage 融合 |
| R29 | “Padé approximants of the Born series of electromagnetic scattering by a diffraction grating,” Physical Review A 109, 033522 (2024). DOI [10.1103/PhysRevA.109.033522](https://doi.org/10.1103/PhysRevA.109.033522) | 出版社摘要；强散射矢量 forward Padé，不自动给出稳定 inverse decoder |
| R30 | “Input-Tailored System-Theoretic Model Order Reduction for Quadratic-Bilinear Systems,” SIAM J. Sci. Comput. DOI [10.1137/18M1216699](https://doi.org/10.1137/18M1216699) | 出版社检索元数据；用于标识 quadratic-bilinear/moment reduction 的已知理论邻域，不据此推断具体定理常数 |

## 优先权审计边界

这是一轮有明确最近邻的研究审计，不是所有数据库的穷尽优先权证明。尤其需要投稿前继续逐页比较 R04、R15 与 quadratic-bilinear/Volterra 压缩文献。当前可以排除“首次 inverse Born”“首次 physics-native/current NN”“首次 nonlinear data-consistent completion”等宽泛声称；不能据“未检出同一标题”宣布 A23 的组合全球首创。

本包不包含第三方论文全文、教材 PDF、上游训练集或用户账号凭据。
