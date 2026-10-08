# A23 显式实现合同说明

1. 上游runtime NPZ只有points/data0/init，acquisition信息来自已冻结A22的known-geometry manifest及原函数。补全A23 runtime元数据，不读取shape/support/labels。旧data0的生成网格不同，不能当相同backend标签；改为规定12次full-cell插值生成。
2. 用户长期明确要求永远不再检查SHA256。新manifest不计算SHA256，使用固定upstream/current commit、文件schema/字节、准确命令及历史hash字段。原理论包hash保留历史。
3. 原协议提出warm5及12个关键fullprediction。重复5次fullverification会超出12次矩阵，因此本轮测cold1/warm5真实decode，完整prediction每个关键条件一次。未跑的warm完整pipeline明确NOT_RUN；不据warm kernel宣称端到端加速。
4. Source-anchor P按全forcing尺度判断结构零，不让数值roundoff生成虚假P4。原与cache使用同一合法、与本次噪声无关的known-reference observationprobe；不能声称跨测量摊销一个data-dependent Oseed。
5. 满维χ和a的线性先验在背景点按a'映射匹配；强幅度a→χ仅局部prior匹配，不是全局概率pushforward。所有输出的可行性显式检验；无jitter、pinv、QP容差放宽或隐藏projection。
6. H2/H3汇总规则在任何full-image质量输出前登记于configs/SCIENTIFIC_AGGREGATION_FREEZE.json。旧项目gates和negative记录未改。

7. 首版H1缓存没有序列化完整key。H2不直接复用该背景map/decoder：重新付费构建已知背景的全transfer、receiver伴随及decoder，逐元素检查与H1一致，然后登记geometry/source/receiver/frequency/reference/whitening/metric/probe/dtype key；旧H1缓存不覆盖。该准备成本计入真实账本。
8. full-state额度按阶段在调用前reservation落盘，跨jobs取receipt/日志的保守最大计数；未结算orphan job阻止新物理运行。已有pilot结果不允许自动覆盖/重跑；部分结果保留并报告。clean label缓存须同时验证材料和完整key。单方法算法错误保留失败行，不抹去其他方法。
