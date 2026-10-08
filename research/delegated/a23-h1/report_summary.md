# H1 receipt summary helper

完成：新增 `src/a23/h1_report.py`。`summarize_h1(root)` 写入 `results/a23/H1_SUMMARY.csv` 与 `SEED_REDUNDANCY.csv`，返回 `summary_rows`、`seed_rows`、`metadata_concerns`、`paths` 四个键。Parent 负责调用；本子任务没有写入实际结果目录、执行物理任务或判断 gate。

- 已只读核对真实 H1：4 scenes × 8 arms，共 32 行；所有 cold/warm receipts 保留。
- Full cold encoder = common reference/geometry + 必要 receiver-mode preparation + cold encoder/export increment；direct 另加 `independent_preparation.cold_seconds`。共同评价 decoder 准备单列，另提供显式包含它的成本列。
- Warm vector 按五个原始 attempt slots 加 direct 独立 warm construction，明确排除已缓存的 reference/receiver cold cost。
- 仅使用 `repeats[0].counts`，direct 仅加一次独立 `cold_counts`。L/F/G/S/伴随/solve RHS 独立列，无 RHS 总数、无 alias 双计；direct 实际记录 solve-adjoint128、S-adjoint128、B-adjoint768。
- SEED_REDUNDANCY 共 96 arm/channel 行；提供 raw/effective/capped rank、joint rank/deflation、P norm、principal-angle JSON 与原始 JSON pointers。Randomized/direct 的 O/P/M 标为不适用，不伪造零 rank。
- Source-anchored OPM 四场景 P 的 saved-receipt 消失验证成立：relative Kb 约 5.67–6.15e-15，raw own-scale rank6、effective/capped0。OM 的 P 是 omitted，引用同场景 OPM evidence，未声称独立测试过。
- Metadata concern：四个 direct arm 的 exact-transfer rank 均为 null；本地没有 cached transfer spectrum，故报告留空并标 NOT_RECORDED，没有从 1536×3456 dimensions 推断 rank。

标准库只读验证通过：32 summary/96 seed 行；核对完整 cold formula、direct RHS、五个 warm slots、P provenance 和临时目录 CSV round trip。Direct 完整 cold encoder 秒数依场景为 2001:12.83225、2003:16.81776、2014:15.52639、2009:15.02375；这些数值排除共同 evaluation-decoder 准备与 probe 评价。

未修改 pilot、冻结配置、物理实现或门槛；未进行任何新 hash 检查。
