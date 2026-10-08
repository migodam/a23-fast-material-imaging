# A23：3D Vector-Maxwell 少次反馈材料成像实验

**首轮真实 Maxwell pilot 已完成：H1 / H2 / H3 全部 FAIL，决定为 `STOP_NO_EXPANSION`。** 这是保留负结果的研究与复现包。没有训练 NN，没有增加 OPM degree，没有运行 nonlinear GN/DBIM，也没有修改 Maxwell solver。

研究问题是：能否删去 O/P/M 编码中的重复计算，用一次二阶反馈改善完整材料图像，并在同等质量下减少完整 time-to-image？材料输出为完整 **1728-cell / 3456 实维**；旧 32D chart 只用于离线诊断。

## 阅读入口

- **[完整中文研究报告](A23_RESEARCH_REPORT_ZH.md)**：背景、公式、强对照、逐对象结果、失败机制、成本及建议。
- [机器可读裁决](A23_GATE_DECISION.json)、[运行 manifest](A23_RUN_MANIFEST.json)、[冻结配置](FROZEN_CONFIG.json)。
- [数据与证据索引](docs/EVIDENCE_INDEX.md)、[复现说明](docs/REPRODUCE.md)、[后端与信息边界](docs/BACKEND_MAP.md)。
- [网页 GPT 入口](https://raw.githubusercontent.com/migodam/a23-fast-material-imaging/main/A23_RESEARCH_REPORT_ZH.md)：可匿名读取的单份中文报告。
- [发布版本](https://github.com/migodam/a23-fast-material-imaging/releases/tag/v0.1.0-pilot)：代码与公开证据；大尺寸可再生成 workspace 不打包。

## 实测结论

| 假设 | 冻结门槛 | 证据 | 判断 |
|---|---|---|---|
| H1 计算最小性 | transfer error≤5%，完整 encoder 成本降低≥20%；或同预算 decoder error改善 | cached Schur一致，但完整冷启动只减少约0.35–0.86%；source anchor后P消失仍未达到同质量成本门槛 | FAIL |
| H2 一次反馈成像 | 两个不同家族、nominal零噪声/20dB均比最强匹配线性改善≥10%，且材料可行 | A23强Gaussian原始改善约5.8–7.8%，其余家族不改善；未压缩IBS2更好但仍违反材料约束 | FAIL |
| H3 端到端成本 | 同质量完整时间降低≥20%，或同成本非支配收益 | 12个关键检查中11个材料拒绝；唯一full验证图像材料误差81.24%、数据残差10.94%，完整归因耗时44.57秒 | FAIL |

对象 **2001、2003、2014、2009 均为历史暴露对象**。3幅度×2噪声×8方法=192行，另有12行标定扰动，共 **204行**。79行材料可行、125行拒绝；全部原始图像和错误保留。未运行的full数据残差为空值。

GPU累计占用 **1628.926秒（27.15分钟）**，含尾部，低于2小时硬预算。12个clean多源标签全部计费。CPU、LU、RHS、传输、冷/暖计时和失败见 [成本汇总](results/a23/COST_SUMMARY.json)。

![完整质量与成本](figures/a23/quality_time_pareto.png)

## 证据边界

已知背景 `0.1+0.04i`、固定六源单频、相同离散Maxwell模型，不是盲测、临床验证或未知背景成像。full Jacobian数据行秩1536，但此prior/λ下稳定方向仅46–48个，材料维数3456；低数据残差不等于正确图像。

50项测试及tiny验证通过，支持所测实现一致性；它们没有让成像gate通过。warm5覆盖decode、材料转换及可行性检查，完整warm full验证未运行。10/100图像摊销仅公式外推。

## 复现与目录

- `src/a23/`：材料接口、cached Schur、projection-first transfer、χ/a二阶、decoder、pilot、guards和报告。
- `src/a20/`、`vendor/a17/`：冻结复用物理代码；上游commit `b85a29a51f4ea7b4d93617e827d88e23933b89df`。
- `data/online/`：白名单几何/初始化；`data/offline_eval/`：仅评价使用的材料标签。runtime不读取truth-state J、GN optimum、oracle current。
- `results/a23/`：CSV、重建NPZ、clean数据、probes/sketch、provenance、终止receipts、失败与成本账本。
- `figures/a23/`：26图PNG/SVG、raw绘图表和manifest。

只读结果复核与新的独立复现实验分别见 [REPRODUCE.md](docs/REPRODUCE.md)。已有结果不得自动覆盖或扩大。

## 理论包与实际执行

实施前理论、文献、条件定理和反例保留；原README另存为 [THEORY_PACKAGE_START_HERE.md](THEORY_PACKAGE_START_HERE.md)。其中“未来执行/尚未实现”是历史状态，本次实测以本README、中文报告、receipts及gate为准。第三方全文、个人连接配置和密钥不在公开包中。

MIT许可。公开发布与科学GO/NO-GO分开，发布负结果不改变 `STOP_NO_EXPANSION`。
