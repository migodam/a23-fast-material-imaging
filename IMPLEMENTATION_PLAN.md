# A23 首轮实施与冻结记录

先复用已冻结 A17 DenseDDA/A20 Adapter、实化与 Schur 层级，不复制旧成像入口。新增 `a23` 的 reference/response/encoder、阶段驱动、独立离线评价、账本与报告。

1. Phase0：独立运行原 tiny 包；用同一真实内核检查 cached Schur、源 anchor、伴随、极化率一/二阶导数、二阶响应、白化/packing、gauge、反例与拒绝路径。实现正确性通过才运行 H1。
2. H1：四对象已知背景，固定 U8/O4/P4/M4 degree1，比较原/cached/source-anchor OPM、OM、MP、M-only、直接伴随及固定 rank32 随机 transfer；8个独立全材料 probes。实际动作与总准备时间分列。
3. H2：完整 cell 实材料质量坐标；四对象×三幅度×两噪声，统一满维物理 L2 prior，冻结谱相对 Tikhonov 1e-3。对比 Born/BP、dressed χ、linear-a 精确转换、vanilla IBS2、压缩 feedback、current-BP ratio 及通用 SVD。分别核验局部 constitutive 与重复散射。
4. H3：固定三臂×四 noisy nominal 条件共12个付费 full forward；额外四 calibration 条件和最多8个预测验证，仅预算允许时运行。cold1/warm5，计入 setup、验证、失败与 IO，N10/100 只公式外推。可接受区域预注册为 full χ NRMSE≤0.60、差分数据 residual≤0.20，不用结果移动阈值。
5. 全部结果与失败原样保存。无 NN、degree 增长、solver 修改或新增对象。H1不是H2的必要机制前提：若direct更便宜采用direct；H2失败后不扩先验/训练，仅完成已预注册H3验证以界定成本。
6. 独立公开仓库交付中文报告/README/raw入口/commit。旧源码与参考冻结；SHA256 新检查按用户长期指令不执行，记录commit、文件字节与历史hash字段。

所有 config 在候选质量结果产生前写入。工作不依赖再次许可，用户已直接授权实施及公开发布。
