# 验证与阅读指南

本包完成了16项指定交付，并另有统一记号、来源审计和可重跑CPU检查。三个独立入口是 executive、route decision、Codex spec。

数学阅读顺序：Redundancy → Cheap operators → One-shot theory → Bayesian theory → Ledger。
算法阅读顺序：Executive → Complexity/Competitors → Minimal experiments → Codex spec。
先验与架构：Priors → Symmetry → NN architectures。
定位与投稿：Medical applicability → Novelty audit → Route decision。

## 已执行的检查

`validate_theory.py`：Schur、P删除、PMidentity、DWR、独立8cellvectorDDA、finiteamplitudeorders、quadraticcovariance、correlatedprior、curvedfibre。
`validate_extra.py`：passivepolarizabilitydisk、exactinverseconversion、unitarygauge。
均为CPU/NumPy，全部 assertions 通过。

Markdown交付检查：16个指定文件均存在且非空；codefence、inline/display math delimiter配对；本包显式本地Markdown链接目标存在；未检测到Unicode replacement字符。

这些检查不是数学定理的形式化验证；也不是上游实验重现、posteriorcalibration、fullimagequality或speedup测试。网页可读摘要与全文层级在SOURCES明确区分。

## 原始证据

`validation/THEORY_VALIDATION.json`和`validation/EXTRA_VALIDATION.json`是实测输出；code与raw结果一起提供。wall_seconds仅为小检查耗时，不用于任何成像速度宣称。

`RESEARCH_MANIFEST.json`列出交付文件SHA-256及上游pin；不包含账户信息、第三方PDF或原项目训练数据。
