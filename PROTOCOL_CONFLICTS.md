# A23 显式实现合同说明

1. 上游runtime NPZ只有points/data0/init，acquisition信息来自已冻结A22的known-geometry manifest及原函数。补全A23 runtime元数据，不读取shape/support/labels。旧data0的生成网格不同，不能当相同backend标签；改为规定12次full-cell插值生成。
2. 用户长期明确要求永远不再检查SHA256。新manifest不计算SHA256，使用固定upstream/current commit、文件schema/字节、准确命令及历史hash字段。原理论包hash保留历史。
3. 原协议提出warm5及12个关键fullprediction。重复5次fullverification会超出12次矩阵，因此本轮测cold1/warm5真实decode，完整prediction每个关键条件一次。未跑的warm完整pipeline明确NOT_RUN；不据warm kernel宣称端到端加速。
4. Source-anchor P按全forcing尺度判断结构零，不让数值roundoff生成虚假P4。原与cache使用同一合法、与本次噪声无关的known-reference observationprobe；不能声称跨测量摊销一个data-dependent Oseed。
5. 满维χ和a的线性先验在背景点按a'映射匹配；强幅度a→χ仅局部prior匹配，不是全局概率pushforward。所有输出的可行性显式检验；无jitter、pinv、QP容差放宽或隐藏projection。
6. H2/H3汇总规则在任何full-image质量输出前登记于configs/SCIENTIFIC_AGGREGATION_FREEZE.json。旧项目gates和negative记录未改。
