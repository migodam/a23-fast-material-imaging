# 定理、反例与验证账本

“已证明”指本包给出的有限维条件推导；“已验证”指 `validation/` 中的最小CPU检查；“新颖性”不由数学正确性自动获得。标准结论明确注明。

## 1. 六类成果总账

| ID | 数学命题及假设 | 证明/定位 | 计算含义 | 可检验预测 / 状态 |
|---|---|---|---|---|
| T1a | L/AU可逆且全部referencecurrents在U ⇒ Kb=0 | Redundancy §2直接代入 | 删除Pseed/chain，非删materialresponse | Pnorm跟随reference解残差；tiny通过 |
| T1b | U=0、fullcomplexchart含a/a'、rawM完整保留 ⇒ KP(d)⊂KM(d+1) | Redundancy §3逐次幂 | M可替P但多一degree | rankcap/受限chart可破坏；identitytiny通过 |
| T1c | 有U时P由M与ΠFUclosure联合生成 | Redundancy §4 blockSchur | 不可仅按名字合并P/M | 需实际capture；条件identity，非普遍subset |
| T1d | 缓存LU/L*U使K/T/adjoint免额外fullactions | Cheap §1代数 | 原六源4/4配置seed阶段删54vectorRHS | 四种operator相对误差约1e−16；tiny通过 |
| T2a | relativefeedbacketa<1 ⇒ cubicforwardremainderbound | OneShot §1–2 resolventidentity | 已知强背景也可小相对扰动 | finiteampidentity/boundtiny通过 |
| T2b | 稳定D、bilinearQ有界 ⇒ 完整inverseerrorbound | OneShot §3 | bias/noise/chart/Q误差不能省 | fullleftinverse/noiseless才cubic；tiny通过 |
| T2c | fullcomplex单频chart，a'可逆 ⇒ normalcurvature仅feedback项 | OneShot §5–6 chainrule | 分离localconstitutive伪创新 | identity约4.2e−15；one-dirchart反例通过 |
| T3 | 同质量setup/onlinecost给break-even | Complexity §5移项 | N小或online不快则无净收益 | 会计恒等式；无实际A23speedup结论 |
| T4a | Gaussian固定线性stat充分 iff complementmean常数 | Bayesian §1 likelihoodratio | 标签不能增信息 | 一般非线性SVD不充分；证明完成 |
| T4b | quadraticmodel最小linearstat=span[A,Q] | Bayesian §2求导/因子分解 | 可能比linearspand大很多 | 8cellrank16→88；不是内在参数维数 |
| T4c | samepriorGaussiancompression的平均posteriorKL≤遗漏meanenergy/2 | Bayesian §3 KLchainrule | 物理误差→posteriorbudget | exactjet为Oρ6，有linearerror则不是；条件证明 |
| T4d | GaussianquadraticCov=2ΣqijqijT，mean=Σqii | Bayesian §4 Isserlis | matrix-freerandomquadraticrange | exactquadraturetiny通过；Rademacher反例 |
| T5 | strongΣ可逆、小amplitude、完整Q ⇒ priorrecoil强dataerrorOρ3 | Bayesian §7双线性展开 | 保护数据而非固定材料系数 | scalarfibrehardOρ2/recoilOρ3；tiny通过 |
| T6a | gauge-transformedO/F/M的transfercontraction不变 | Symmetry §3代入 | NN使用covariant/invariantops | 必须做Haarunitarygauge测试；代数证明 |
| T6b | current/fibredeterministicfactor消元需Jacobian | Bayesian §8delta变量变换 | 不制造fakeprior或错误posterior | 1/|detL|伪权重反例；标准概率规则 |
| T6c | A9scalarCMRR被动极化率在明确圆盘内 | Priors §2 | O(p)物理投影 | 证明完成；本轮不声称临床/通用tensor验证 |
| AUX1 | 任意Xhat/Zhat的correctedtransfer双侧残差identity | Cheap §4 | 原非Galerkinclosure需显式correction | tiny约6.7e−13，标准DWR |
| AUX2 | DJ沿路径近C ⇒ finite-amplitudefunctionalerror界 | OneShot §7 FTC | referencebank需覆盖而非oracle挑选 | 条件证明；wide-domain常数未知 |
| AUX3 | hidden-currentSchurselfenergy阻碍pointwiseinverse | OneShot §8块逆 | compressedtransferinverse不是localmaterial | exactobstruction，未造有利oracle |

## 2. 必须保留的反例

| ID | 反例 | 否定的过强主张 |
|---|---|---|
| C01 | L=1,RA=.5,真defect=.5，未经修正doubledefect=.25 | 任意learnedresolvent也满足Galerkin双侧identity |
| C02 | F=[[0,100],[0,0]]，rho=0但degree0error100 | 小谱半径保证浅多项式精度 |
| C03 | L=diag(1,eps²)，遗漏eps e2输出1/eps | currentoverlap近1就能放心删P |
| C04 | L=[[0,1],[1,0]],U=e1，AU=0 | 完整L可逆⇒Galerkincore安全 |
| C05 | M的raw多源probe经rankcap丢掉关键方向 | materialprobe包含方向⇒currentseed完整 |
| C06 | fullJrowrank=m ⇒ PJ=I | 强非线性总会增加新data-space方向 |
| C07 | chart只含一个方向，a''uu在chart之外 | chart-normalquadratic全部来自feedback |
| C08 | f(a,b)=a+b² | 任何二阶response都可唯一归因到weakparameter |
| C09 | f(a,b)=(a,b²) | linearSVDsufficient / 弱方向完全没数据 |
| C10 | ρ=.8correlatedGaussianprior只测x1，x2posterior随y变 | weakposterior等于独立原prior |
| C11 | Rademacherg，Q=(g1²,g2²)总为(1,1) | 任意随机±1probe都能探索所有二阶方向 |
| C12 | f(a,b)=a+.7ab+.4b²+.2b³，固定a补b | 线性nullspace补全保持nonlineardata |
| C13 | δ(Lχj−bχ)不乘det积分得到1/|detLχ| | 未归一currentfactor是合法physicsprior |
| C14 | 曲面采b再投影a但不加det∂aFs | data-consistent样本自动是posterior样本 |
| C15 | L=I−AG，G对称而A非标量 | reciprocity等于rawL的Hermitian/transpose对称 |
| C16 | 完整Maxwell解对每个χ的PDEresidual均为0 | PDE-onlyresidual可识别正确材料 |
| C17 | highcontrastunknownbackground使eta≥1或inversepole逼近 | one-shot局部界无条件覆盖全部强散射 |
| C18 | fullQR/Hessian虽tiny，但cachedB和Z为多GB | 小rank自动可扩展或快 |
| C19 | 任意object-onlyrotation在固定阵列改变S/einc | fixed-systemSE(3)invariance |
| C20 | χreal/imag投影相对于有耗背景误裁合法负contrastloss | contrast被动性永远是Imχ≥0 |

C01/C02/C07/C10/C11/C12等有本轮数值项；其他为正文明确代数构造或条件反例，不写成已经运行的Maxwell实例。

## 3. 原项目证据与本轮证据必须分开

A20/A20-R1/A21/A22/A22-R1 的数值取自[P04–P10]，没有重跑。A21oracle验证不等于A23上线；A22in-chart统计不能变fullimage；已暴露四对象不是独立盲测；原gate未改。

本轮脚本是独立8cellvectorDDA，不读上游数据，float64/complex128，CPU。它证明有限矩阵例子与预期一致，不提供复杂组织、未知背景、large-n、GPUlatency、posteriorcalibration或publicationacceptance证据。

## 4. 验证的关键数字

完整原始数值在 `validation/THEORY_VALIDATION.json`，这里列便于核对的量：
- cachedSchurrelativeerrors：约1.6–2.1e−16；
- sourceanchoredP：3.62e−16；
- materialinverseabsoluteerrorslope：first1.99991，second2.99985；
- linear/quadraticforwardremainder：2.00024/3.00154；
- linear/jetdiscardedmeanslope：2.00031/2.99993；
- datareal648，materialreal16，linearstat16，fulljetstat88；
- Gaussianweightedquadraticinnovation90%/99%/99.9%energy：12/26/37个增量方向；
- 最大相对feedbacketa约.0134，背景Lcondition约1.189。

能量保留比例不是后验KL阈值，也不是对每对象的保证；更不能把局部额外26个方向称为26个新独立可识别材料变量。

## 5. 尚未解决但可直接实验的问题

实际fullvoxelprior下，反馈响应是否低秩到足以抵消准备成本？二阶correction能否改善noise/modelbias条件下的完整材料图？未知参考与calibration是否占主导？curvedpriorcompletion是否比GMM/wavelet/现有data-consistentNN更有价值？这些是本轮研究留下的具体可判定假设，而不是以“开放难题”搁置。
