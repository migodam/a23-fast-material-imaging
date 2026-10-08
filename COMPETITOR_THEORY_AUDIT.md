# 竞争方法的理论和计算审计

本表比较算法类别，不提供虚构的统一迭代次数或跨硬件速度倍率。I为外层迭代数，ν为每个linear/PDEsolve的内部迭代数，K为NN层数或采样步数；均需实测。同类不同实现可有显著区别。出处见 [B01]、[R01–R30]。

## 1. 十五类竞争者

| 类别 | 真正瓶颈 / full solve / J | 迭代与offline | 失败区与A23可能优势 |
|---|---|---|---|
| Born / Rytov / linearized | 已知background下线性operator及regularization；未知background准备另计。J显式或action | cachedinverse可一次乘法；大型线性solve可有ν；SVD可offline | nonlinearphase/currentbias；A23二阶只在额外反馈真实可压缩时有优势 |
| adjoint / BP / time reversal | S*数据传播；fullbackgroundadjoint可需solve，homogeneousGreen可直接 | 一次/fewpass；geometry可缓存 | matchedfilterPSF与幅度bias；小inverse/deconvolution已有，不能只和未经调优BP比较 |
| SOM / TSOM / SOM-Net | currentspace状态/数据equations、Greenactions；不一定每外层fullPDEsolve | SOM/TSOM迭代；SOM-Net固定Kblocks、训练offline | nonradiatingambiguity/representation；A23必须优于现有current-to-material结构而非重命名 |
| CSI | 同时current/material，残差与Greenactions；通常不为每次更新单独求精确fullstate | I次alternating/nonlinearCG等，Green可缓存 | 非凸/初值/收敛；A23可省迭代但不能把CSI误计为I次fullLU |
| DBIM / Newton / GN | 每次更新backgroundfields与sensitivity；Jv/J*v或显式J | I×state/linearizedsolve，部分geometry可reuse | localminimum/大变化/高cost；A23是少步近似，不比相同GN更快的solver |
| full-wave adjoint optimization | 每轮sourceforward+adjoint，checkpoint/memory | I轮；通常不建完整J | 非凸、cycle/modelbias；A23减少在线重复state，但fullimagequality需守住 |
| Krylov / FFT-DDA / fastforward | 加速Lactions/solve，不自行解决materialinverse | 每solveν；preconditioneroffline或更新 | nearresonant/nonnormal/mesh；A23可以使用它们，不是其互斥替代物 |
| projection ROM / POD / reducedbasis | snapshot生成、basisQR、core与onlineparameterassembly | expensiveoffline，cheaprepeatedcore；可需adaptiveenrichment | reference/parameterOOD；A23sourceanchoring/jet仅是候选改进，通用goal-awareROM是强对照 |
| randomizedSVD / TSVD / LIS | J/J*probes、SVD、priorweighting | lowrankprep可offline；LIS可需posterioraveraging | tail误差/固定linearization；同一A同一prior下SVD不会因缺OPM标签更差 |
| directinverse / EBA / inverseBorn | 已知解析approximation、transfer/rationalinverse、nonlinearseries | 非迭代或少项；core/coeff可offline | poles、observability、seriesradius；A23二阶与其直接重合，必须comparevanillaIBS2 |
| deepinverse-scatteringNN | labels/training、fullimagedecoder；inference可无fullsolve | offline成本高，online固定K | trainingfamily/geometrycalibrationOOD；A23explicitresponse可能省labels/解释failure，尚未实证 |
| neuraloperators / encoderdecoder | operatortraining、resolutionmemory、geometryencoding | amortizedfixedK或spectrallayers | 训练distribution与新operator；不能借FNO原论文非Maxwell速度作对照 |
| PnP / RED / learnedprox | 每轮data-consistencysolve+denoise；fullphysics成本可能重复 | I轮；denoiseroffline | convergence/model/denoiser假设；A23one-prox低latency，但priorquality可能不足 |
| Bayesianinversion / sampling | likelihood、多次forward/gradient、covariancedirections | Gaussian可解析；MCMC通常大量步；LIS可offline | highdim/nonlinear/multimodal；A23统计压缩可省likelihood，不自动得到正确posterior |
| diffusion / flow inverse | K次network及可能的physicsguidance；每guidance需J/forward | trainingoffline；多NFEonline，也可能distillfewstep | latency、OOD、posteriorcalibration；A23小latent只是额外prior假设，不是天然降维保证 |

## 2. 与东哥工作的具体关系

教材 [B01] §6.2.4 已有 current back-propagation → internal field → analytic material ratio：
\[
\chi(r)=\frac{\sum_sJ_s(r)\overline{E_s(r)}}{\sum_s|E_s(r)|^2}.
\]
所以“current恢复后直接生成material”不是新贡献。§6.2.3 EBA已有通过中间参数把某些非线性近似拆成两步linear inversion。

TSOM已根据observationweak、propagationstrong区分current；FFT改进正是为了绕过昂贵GD-SVD。[B01] §6.4.2–6.4.3。OPM的M-channel有materialtangent动机，但同一个J的factorization不增加统计信息。

SOM-Net [R02] 输入deterministiccurrent和BP粗图，交替current/material结构，并从current解析得到场/介电图；网络损失同时涉及current、data、material。A23若只是增加一个learnedfeedbackblock，novelty很弱。

2026MFFSOM-Net [R28] 已在多频currentrestoration/EFIE/materialfusion方向推进；本轮只核对IEEE摘要/metadata，仍足以阻止“首次多频SOM网络”的宽泛主张。

## 3. 最容易被弱化、但不能省的对照

**同参考背景的 full-J/adjoint TSVD 或 Wiener。** 不是未知truth-stateJ；knownreferencefullJ可以离线构造为goldstandardencoder。若OPM只近似同一个J，后者代表其线性信息上限，同时actualsetupcost决定是否可部署。

**linear-in-a + exact a→χ。** 把局部depolarization/radiationreaction消掉，检验所谓feedback增益是否只是材料坐标变换。

**vanilla inverseBorn2。** 使用同一个A,Q,D，但不用A23的specialcompression/标签。输出相同就意味着novelty只能在更便宜构造或更有用统计保留，不能声称新inverseformula。

**analyticpolynomialclosure。** A18-B同actionbudget已有强结果，[P11]中degree3poly对某些tailquality/latency优于NN；不再次选择弱anchor制造巨大gain。

**currentBP与合理CSI。** 不把它们强行记为每轮fullLU，以免虚构相对加速。

## 4. 公平比较的四种口径

1. equal-operator-RHS：识别信息效率，但block效率不同，不能当walltime。
2. equal-memory：对大规模场景非常重要；增加Zcache不是免费。
3. equal-quality：同fullimage目标与noise/geometry/priors，测time-to-acceptable。
4. equal-total-resource：含geometry、reference、offlinebasis、training、validation、fallback与N次摊销。

各口径可能不同赢家，应都报告而不事后选有利口径。固定old32chart的physicsNRMSE不能替代fullvoxelimage质量。

## 5. Novelty的实际位置

标准：Schur/adjoint、SVD/Krylov、Gaussianposterior、DWR、inverseBorn、nullspaceprior、few-layerunrolling。

值得做A23实验的组合：真实Maxwellconstitutivenonlinearity与feedbackcurvature分离；按遗漏dataresponse控制posteriorloss；sourceanchoring和cacheddualcontraction节约准备；允许prior沿curvedmeasurementfibre补全；在lossyvector3D full-image任务上给quality/time边界。

现在还没有证明这一组合击败 simpler baselines。若等价输出更贵，应该保留baseline并停止OPM专属路线，而不是增加NN以延续名称。
