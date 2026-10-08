# 复现

先读取根目录README和中文研究报告。公开结果不是盲测；四个对象均已历史暴露。

## 环境

实验：Windows、Python3.10.9、NumPy2.2.6、SciPy1.15.3、PyTorch2.6.0+cu124，RTX4060 Laptop 8GB；数值为complex128/float64。本地微型测试使用Python3.13/NumPy/SciPy，不需要CUDA。绘图需要matplotlib。使用已有环境，没有部署新solver或调度框架。

## 检查公开证据

`results/a23`保存所有CSV、数组、失败、逐操作账本与终止receipt。`FROZEN_CONFIG.json`和`configs/SCIENTIFIC_AGGREGATION_FREEZE.json`在候选质量输出前冻结。`RUN_SOURCE_SNAPSHOT.json`记录实际后期phase0/pilot源码commit。部分早期phase0/micro/H1 manifest没有A23源码snapshot；该来源缺口保留为missing，不事后反推或伪造commit。冻结backend文件与原资产直接字节一致。

公开目录不含约3.15GB可再生成的receiver/transfer/current-basis缓存。这些缓存保留在原运行机器；结果pull receipt记录省略的文件/字节。重建所需代码、全部合法输入、随机probe bank和raw结果已公开。发布的zip也不冒充完整Maxwell workspace。

## 新建独立复现实验

不要在原结果目录重跑或删除旧账本。以下仅创建新工作目录，尚未启动任何计算：

```text
python tools/make_replay.py --destination ../a23-independent-replay
```

随后进入新目录，设置`PYTHONPATH=src`。Windows PowerShell用`$env:PYTHONPATH='src'`；macOS/Linux用`export PYTHONPATH=src`。

```text
python -B -m a23.cli phase0 --job a23-phase0-replay --device cpu
python -B -m a23.cli micro --job a23-micro-replay --device cuda
python -B -m a23.cli h1 --job a23-h1-replay --device cuda
python -B -m a23.cli pilot --job a23-pilot-replay --device cuda
python -B -m a23.cli report --job a23-report-replay --device cpu
```

micro必须通过预算预测，单位/伴随测试必须通过。不要自动执行后续命令来绕过失败。单次独立复现仍受7200秒GPU和12个clean多源full states硬限制；失败/重跑计费。主实验当前已经完成并停止，不因这份说明而启动第二轮。

native CLI自身执行累计计费与锁。需要严谨的远端进程外硬期限时，使用`tools/a23_remote.py`的foreground controller；它依赖已有可信private transport helper。连接配置仅存在外部或ignored private目录，public代码没有账号/密钥。共享锁与排队策略见`A23_TRANSPORT_SUMMARY.md`。外部读者可直接在已配置CUDA主机运行native入口，无需该私有连接。

## 结果定义

- fullχNRMSE使用完整1728-cell材料和质量范数；deltaχ/实/虚/edge/support单列。
- `status=REJECTED_PHYSICAL`的raw图像保留，不能进入有效质量和速度gate。
- `datafullresidual`仅在RUN的full验证时存在；NOT_RUN/REJECTED为null，不填0。
- cold1/warm5包含真实decode/材料转换/可行性检查。只对预注册key cases做一次full验证；warm端到端重复full验证NOT_RUN。
- N10/N100列是setup+N*online公式外推，未真正处理10/100幅图像。
- RHS计数按L/F/G/S、伴随、forward/adjoint solve、LU等分别保存，不把聚合计数重复求和或等价为时间。

报告端只读取保存证据，不调用Maxwell、不训练模型、不改变冻结配置。`src/a23/report.py`复现gate表，中文解释由主线程审阅。复制源代码也包含tiny反例；它们支持实现一致性，不构成完整成像证据。

`validation/*_VALIDATION.json`是原理论包的历史运行；`results/a23/theory_verification/`是本次重跑的独立数值/runtime记录。原脚本保留，但两次运行输出不必逐字相等，不混淆成一个receipt。`src/a23/cached_diagnostics.py`的四张表已生成，它禁止覆盖；无需为拿到表重新运行物理。
