# A23 公开证据审计

日期：2026-10-08。范围是公开候选文件的隐私、来源、计费与复现边界；不重新运行物理实验，不修改配置、账本、报告或 gate，不承担科学结论裁决。主线程继续拥有 H1/H2/H3、novelty 与 matched-method 成本归因的解释权。

本审计是发布前的工作区快照，不能替代发布后对实际仓库与下载包的核对。首次扫描后的修复、费用刷新和公开脱敏由主线程完成；下表明确区分首次观察与最终只读复核。没有新增必须依靠物理重跑解决的阻断问题。

闭环复核：四份公开副本已脱敏，原字节保存在 ignored 私人存档；审计再次读取这四份公开副本，没有发现剩余个人路径。`PUBLICATION_AUDIT.json` 已生成。主线程报告最终 363 个公开候选文件的路径/密钥/token 模式扫描为 0 个命中，合计约 54.25 MB，没有文件达到 95 MB；本审计没有读取私人原件。全部 12 个 job 已有终止 receipt，当前费用汇总无 orphan，GPU 精确累计 1628.925567 s。CPU 精确总量因小项 allowance 保持 unknown，保守收费完整。bytes/receiver 分类已修正，raw 动作和资源收费不变。审计的第二份检查 receipt 刚生成，仍应纳入最后一次费用刷新；发布后验证另外记录。

## 需要关闭或明确披露的事项

| 事项 | 具体证据 | 状态与处理边界 |
|---|---|---|
| 四份公开候选文件曾包含个人绝对路径 | `research/delegated/a23-tests/TEST_AUDIT.md`；`results/a23/theory_verification/ADAPTER_TEST_RUN_0003.json`、同名 `.log`；`results/a23/theory_verification/ORIGINAL_VALIDATORS_LEDGER.jsonl` | 已关闭：主线程脱敏，第二次只读检查无剩余个人路径。原字节由主线程保存在 ignored 私人存档。审计只记录安全文件名，没有复述删除的路径值。 |
| 首次成本汇总的输入快照已过期 | 首次 `COST_SUMMARY.json` 尚未包含后来终止的报告 job、绘图、cached diagnostics 和审计费用 | 已刷新：当前汇总包含 12 个终止 job、绘图、cached diagnostics 和审计 RUN_0001，无 orphan；`a23-report-local-002` CPU 12.187729 s、GPU 0。刚写出的审计 RUN_0002 仍需纳入最后刷新。先前失败与报告支出保留。 |
| 早期阶段缺少 A23 源码 snapshot | `micro-001`、`h1-001`、`phase0-remote-001` 与 `phase0-local-001/002/003` 的 manifest 没有 `source_snapshot` | 后端 upstream pin 可核对，但不能据此补写未记录的 A23 执行 commit。主线程已在复现说明和主报告明确保留此缺口；完整图像 pilot 的 `8e7d8cf209c6e54f55567b940658e1742aa4cc55` snapshot 已记录且在本地 Git 中可解析。 |
| 历史理论验证与后来的重跑不是逐字节副本 | `validation/{THEORY,EXTRA}_VALIDATION.json` 与 `results/a23/theory_verification/` 下同名文件有数值/环境差异 | 主线程已补充两个时期的区别。应分别引用正确路径，不能把这种差异称为仅删除机器路径，或把两组既存结果当作一次运行的重复计费。 |
| 费用类别曾混合单位 | 首次 `canonical_action_families_by_scope` 把 `L_upload_bytes` 放进 L matvec 类，且把 `full_*_receiver_rhs` 放进 full-solve RHS 类 | 已关闭：主线程修正 `_family` 后刷新汇总，bytes 与 receiver contractions 优先分类；raw counters 和资源总计没有改动。不得对不同单位或 instrumentation aliases 求和。 |
| 30 s 发布费用是 allowance，不是精确新增 CPU 消耗 | `EXTERNAL_CPU_LEDGER.jsonl` 的发布 allowance 范围包含 shell、审阅、报告与发布；后来的绘图/审计另有测量 receipt | 它可以覆盖剩余未测量开销，但必须继续标为 conservative allowance，并说明与已测量部分的归属。不能把它当作已证明不重叠的精确 30 s 实际消耗。CPU exact total 保持未知是诚实状态。 |
| 首次扫描时脱敏清单尚未生成 | 首次未发现 `PUBLICATION_AUDIT.json`，而 `docs/NOTICE.md` 已引用它 | 已关闭：第二次只读检查确认清单已存在。发布后对实际仓库/包的检查由主线程另行记录；不得把工作区候选扫描称为对全部 Git 历史的证明。 |

上述事项不授权重新做物理实验，也不改变已保存的负 gate。

## 已核对的来源和资源证据

- `src/a20/backend.py`、`src/a20/opm.py`、`src/a20/costs.py` 与 `vendor/a17/a9_engine.py` 逐字节等于冻结的 A22-R1 checkout。没有计算 SHA256；历史 manifest 的 hash 字段只是既存来源记录。
- 当前 Git 可解析完整图像 pilot 声明的源码 commit。`SOURCE_MANIFEST.json`、冻结配置和各 job manifest 提供相互区分的输入/协议/执行来源；早期 snapshot 的缺失不能由后来的 global snapshot 消除。
- 首次扫描的 CUDA job receipt 合计 **1620.1521561000263 s**，唯一 transport GPU tails 合计 **8.773410899972077 s**，相加等于保存汇总的 **1628.9255669999984 s**。完整 CUDA job 的 host 工作仍计入 GPU 占用。
- 保存的 62 个 cost component ID 没有重复。独立 remote 文件、local envelope 和 transport JSONL 的相同 attempt 没有再次收费；`prior_cost` 与嵌套 action spans 没有再加入资源总额。
- standalone adapter tests 的 parent CPU 收据是收费依据；重叠 book lifetimes 只提供计数/时间诊断。原 validator child CPU 有独立 ledger。未测量的 H1 standalone CPU、初始 query CPU、发布 allowance 没有被伪装为精确 0。
- 新的绘图 receipt 报告 CPU **11.517299 s**；cached diagnostics receipt 报告 CPU **0.159637 s**。两者是已有证据的处理，不是新增 full-state/Maxwell 成像试验。它们应进入最终费用刷新，并保留自己的测量范围。

CPU 单位测试、报告/展示处理与生产物理支出必须通过原始 scope 区分；本审计没有重新推断每个候选方法的独立部署成本。公开 RHS 列保持原标签：L/F/G/S、receiver contractions、forward/tangent/adjoint solves、LU/core factorizations 与 bytes 不能合并成一个无单位的“操作次数”。

## 公开子集与外部缓存复现

公开候选工作区包含合法 runtime/evaluator 输入、全部结果表、raw 图像、失败记录和计费证据。首次扫描了 229 个文本文件及 72 个 NPZ；未发现 credential 命名文件、credential assignment 候选、private-IP literal 候选、NPZ object arrays 或 NPZ scalar metadata 中的个人路径。此处是明确范围内的模式扫描，不是对所有历史 Git 对象的安全证明；凭证内容没有读取。排除了 `.git`、ignored `private/` 与再生缓存。

约 **3.15 GB** 的 receiver/transfer/current-basis 缓存没有 pull 或打包，仍保留在原机器。pull receipts 报告的是每次传输跳过的字节；多次 skip 的累计字节不是独立缓存总大小。没有删除远端缓存。公开候选文件中没有单文件超过 50 MiB。

复现不依赖私人连接：`tools/make_replay.py` 只复制 frozen source/config/input 到新的外部目录，那里没有原 `results/a23` 的已用预算或已用 clean-label caps。读者可以在自己的已配置 CUDA 主机使用 native CLI；私有 transport helper 只用于作者的远端控制。旧结果目录不可直接重跑、删除账本或用旧费用当作新预算。

四个场景均公开 `H1_FIXED_PROBES.npz` 和 `H1_RANDOMIZED_TRAINING.npz`。已有二阶 sketch 的公开路径为 `results/a23/QUADRATIC_SKETCH_2001.npz`、`_2003.npz`、`_2014.npz`、`_2009.npz`，合计 3,016,552 bytes。完整 transfer/current basis 需要按 frozen inputs 与代码重新生成，重建成本应重新计入独立复现实验。

初始 H1 cache key 序列化缺口没有被抹去。pilot 对参考 transfer/decoder 做了付费 fresh preparation 与核对；`docs/BACKEND_MAP.md` 已描述此边界。被排除的 `cache/` 下 provenance 文件如果仍仅在原机器，公开读者只能依据合法输入、源代码和公开 probe/结果重建自己的缓存，不能声称已验证未发布缓存的全部字节。

审计 receipt 的第一次 `probe_file_presence.quadratic` 查询使用了错误的假定目录 `quadratic_sketch/scene_<id>.npz`。该布尔值只说明假定路径不存在，**不是缺失 sketch 的证据**；第二份 receipt 已检查以上四个实际公开路径，全部存在。保留原 receipt，并在本文明确纠正这个检查范围错误。

## 保存的结论边界与审计成本

这里只读取并复制既存决定：`A23_GATE_DECISION.json` 中 H1/H2/H3 均为 **FAIL**，最终为 **STOP_NO_EXPANSION**。公开失败、raw rejected 输出、单位测试成功、图表生成与仓库发布均不能把这些状态改成 GO。历史 exposed 对象不成为新的 blind holdout；没有建立 NN、clinical 或跨模型泛化结论。

本审计有两个独立 process lifetime 的检查 receipt，均在 `results/a23/theory_verification/`：

- `PUBLIC_EVIDENCE_AUDIT_RUN_0001.json`：Python process CPU **1.395065 s**，检查 wall **1.518212583 s**，GPU **0**；记录首次扫描和来源/计费核对。
- `PUBLIC_EVIDENCE_AUDIT_RUN_0002.json`：Python process CPU **0.036792 s**，检查 wall **0.008496041 s**，GPU **0**；记录四份公开副本的脱敏闭环、真实 sketch 路径与脱敏清单存在性。其 scope 与第一次不重叠。

测得 CPU 合计 **1.431857 s**。早先 shell 元数据读取、最终文档写出和 receipt 写出不在这些测量 span 内，receipt 明确标记；主线程可将其归入剩余发布 allowance。当前汇总已包含 RUN_0001，最后刷新应加入 RUN_0002。receipt 的检查成功只表示审计执行完成，不是科学 gate PASS。没有远端动作、物理求解、新 scene/label/gate 或新的 SHA256 检查。
