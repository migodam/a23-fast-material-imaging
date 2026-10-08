# A23 路线竞争与裁决（独立阅读版）

## 1. 问题与当前证据

目标是三维矢量Maxwell的fast material imaging，不再研究currentranking、exchange或更准确的GNstep。参考物理为
\[
j=a(\chi)(e^{inc}+Gj),\quad L=I-aG,\quad J=SL^{-1}B.
\]
原项目A20的early/late结果主要是frozenGNdiagnostic；A21为oracle双侧机制；A22-R1只有固定32Dchart的分离/one-shot统计，完整复杂形状大量能量在chart外，totaldeploymenttime尚未建立。[P04–P10]

本轮真正完成的是源码阅读、文献审计、条件推导和独立8cellCPU验证，没有A23大规模成像或NN训练。

## 2. PRIMARY ROUTE

**Category A：projection-first、curvature-budgeted、one/few-pass material inverse。**

先用已知参考背景的forward/adjointfields直接构造或sketch材料–数据映射A，允许sourceanchoredOM、普通randomizedJ或exactadjoint作为最便宜实现；不要求保留O/P/M标签。

\[
x_1=D(y-y_b),\qquad
x_2=x_1-D\hat Q(x_1,x_1).
\]
Q由相对参考介质的首次追加反馈产生。使用χ坐标时还含真实极化率的a''项。保持全图材料表示或与truth无关的prior-conditionedfullp映射，不能只回到32Dchart。

**两个分支而不是一个教条。**
- 若Q的有效新数据方向低秩且高于noise/modelbudget，补充datajet空间。
- 若完整A已满行rank、或新方向无法经济压缩，不扩数据空间；只检验二阶inversecorrection是否在原数据空间里值得。
- 若二阶修正也不值得，保留linearadjoint/SVD/Wiener，并停止A23专属反馈模块。

最强理论：relativefeedbackidentity、finiteamplitudebound、精确sourceP删除、cacheddualconstruction、quadraticstat/后验损失界。主要未知：完整图像的实际质量–时间优势。

## 3. SECONDARY ROUTE

**解析Bayesian / GMM / 一次结构prox。** Gaussianprior用data-spacelinearposterior；少量多模态用mixture；边缘用wavelet/group或计费TV。可与Primary组合，但不是四类都开工。

先验证残余是可以预测的材料结构，而不是Maxwell/calibrationbias。若解析prior已足够，不训练NN。

## 4. HIGH-RISK / HIGH-REWARD

**Category B/D，必要时再C：curved physics–prior completion。**

prior/小NN生成弱材料b后，不固定强坐标a，而是用Maxwell二阶cross-feedback作解析recoil：
\[
a_2=a_0-\Sigma_s^{-1}U_s^TQ(V_sa_0+V_wb,V_sa_0+V_wb).
\]
局部强dataresidual由二阶降为三阶。真实全图b需完整Qaction或有界approximation；probabilistic版本还需要evidence/Jacobian，data-consistent不等于posterior-correct。

最近邻是nonlineardata-consistentNN [R15]，所以不是“首次沿非线性fibre补全”；机会在Maxwell特定便宜构造、明确误差界与fullwavecost/generalization。

## 5. 评分：立项判断，不是实验成绩

1低、5高。计算节省/成像潜力均是条件性预期；不作论文证据，不把各项相加制造伪客观总分。

| 路线 | 理论新意 | 成像潜力 | 节省潜力 | 大规模性 | 鲁棒性 | 数学可控 | 工程可行 | 发表潜力 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A0 exact/随机adjoint + linearWiener | 1 | 3 | 4 | 4 | 3 | 5 | 5 | 2 |
| A1 budgetedfeedbackfew-pass | 3 | 4 | 4 | 3 | 3 | 4 | 4 | 4 |
| A2 decoderbank/rationaldirect | 3 | 4 | 3 | 3 | 2 | 3 | 3 | 3 |
| A/B analyticGaussian/GMM/prox | 2 | 4 | 4 | 4 | 4 | 4 | 5 | 3 |
| B hard-splitNN | 1 | 3 | 3 | 4 | 2 | 2 | 4 | 2 |
| B/D curvedrecoil+smallpriorNN | 4 | 4 | 3 | 3 | 3 | 4 | 3 | 4 |
| C conditionalflow/diffusion | 2 | 4 | 1 | 2 | 2 | 2 | 2 | 3 |
| D rawOPMtoken/learnedclosure | 1 | 3 | 1 | 2 | 2 | 2 | 2 | 2 |
| 外部data-drivenMaxwellROM路线 | 3 | 4 | 3 | 3 | 3 | 3 | 2 | 4 |

最后一行是值得持续比较的独立竞争方向 [R06–R08]，不自动启动第三个大项目。其假设/数据采集模式与当前频域有耗backend不同。

## 6. 每条路线的支持、未知与淘汰条件

| 路线 | 最强支持 | 最大未知 | 最近竞争者 | Killer / 最便宜证伪 |
|---|---|---|---|---|
| A0 | exactJ=Z*B、标准Wiener | reference成本/OOD | Born/TSVD | strongnonlinearfullimage误差不够；四对象幅度扫描 |
| A1 | inverseerrorbound与tinycubic | 二阶低秩/实际time | vanillaIBS2+dressedBorn | 同A/Q输出相同却更贵；记录setup+online |
| A2 | scalar rational exact、localbankpathbound | hiddenSchurselfenergy/银行覆盖 | EBA/directROM | 两不同hidden介质同compresseddata；smallblockcounterexample |
| analyticprior | 解析Gaussian/GMM、oneprox | 残余是否prior可解释 | TV/PnP | posterior太非Gaussian或shapeprior错误；noNNresidualpilot |
| hardNN | 推断便宜 | hardlinearprotection破坏非线性data | nullspaceNN | f(a,b)cross-termtoy即失败；无须GPU |
| curvedNN | 强dataerrorOρ3 | fullpQ成本与OOD | nonlinearDCNN | 混合Q校正不比普通DC便宜；同容量消融 |
| flow/DPS | 多解posterior表示能力 | 校准/NFE/latent真实维数 | GMM/conditionalGaussian | 两成分mixture已足够或采样慢；小latentposterior比较 |
| OPMtoken/closure | 可表达feedback | 相对analyticbaseline的额外价值 | SOM-Net/poly | basisgauge不稳定或same-A SVD等价；无需新大数据 |
| dataROM | 已有直接MaxwellROM结果 | 有耗3D/采集兼容 | 已有R06本身 | 当前频点不足其time-domainmodel；先核数据合同 |

## 7. ROUTES TO KILL / DEFER

立即停止：NNcurrentranking/proposal、learnedfullresolvent、单纯OPM标签token化、通过更准确GNfidelity延续旧主线、把chart内分离直接升级fullimage。

暂缓：diffusion/flow、backgrounddecoderbank、强散射全局rationalinverse。除非分别获得真实多模态、可摊销背景变化、可观测transferheadroom，不能先投训练资源。

保留为control：Born、BP、genericROM/randomizedSVD、analyticpoly、inverseBorn2、SOM/CSI。这些不是需要“击败后删除”的旧代码，而是新研究不自欺的基准。

## 8. 只有三个先行假设

H1：实际sourceanchoring/cache/directadjoint能减少同质量encoder的总准备成本，而非只减rank。

H2：扣除localconstitutive、chart外部与nuisance后，有限幅度feedback修正确有fullimageheadroom；不要求一定新增数据维数。

H3：headroom在噪声/标定条件下仍转化为总time-to-acceptable-image Pareto优势，含fullverification与N次摊销。

H1败、H2成：可保留已有便宜operator实现，不保留OPM专属压缩。
H2败：停止二阶专属模块，保留linearphysics+prior。
H3败：不扩大训练/医学宣传；研究结果是明确cost/quality边界。
三个有正面证据，再进入小priorcomparison；不是自动四条路线同时开工。

## 9. 最终科研判断

最强的下一步不是“把OPM接上Flow”，而是先把**relativefeedback造成的有限幅度材料响应**做成一个可计费、可压缩、可检验的few-passinverse。若成功，curvedpriorcompletion才有坚实的物理接口。

这有strongTAP候选潜力，但本轮尚无full-image/time实证，不能宣布已达到强TAP。论文价值最终由一个真实Maxwellregime中的明确Pareto优势及可复核机制决定，不由16份文档或漂亮名称决定。
