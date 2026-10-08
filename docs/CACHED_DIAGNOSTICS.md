# 已保存数组的独立诊断

`src/a23/cached_diagnostics.py`只读取公開重建、旧chart空间基、quadraticsketch及metadata，拒绝重复覆盖现有输出。不启动Maxwell、不生成labels、不挑选rank或方法。2026-10-08执行一次，wall0.253156秒、processCPU0.159637秒；receipt在 `results/a23/theory_verification/CACHED_DIAGNOSTICS_RECEIPT.json`。

- `CHART_DIAGNOSTICS.csv`：204行完整deltaχ的旧32chart内外能量/误差。W为既有fixedmassbasis；正交与能量恒等均通过1e−9。仅OFFLINE解释，不是新成像自由度。
- `FEASIBILITY_DIAGNOSTICS.csv`：204行rawRe/Imextrema、cell违规数与原physicalstatus一致性；无projection。
- `QUADRATIC_CORRECTION_DIAGNOSTICS.csv`：28观测中 `x1−x_IBS2` 与 `x1−x_A23` 的材料范数/cosine/差异；不是Q的dataspacecapture。
- `SKETCH_MEAN_DIAGNOSTICS.csv`：4场景Uy对实际训练均值的保留。relativeerror1.15–1.58e−15；independentholdoutmeanerror0.614–0.643。保留均值不等于整个Q可被rank32充分表达。

仅额外小矩阵导出所需的四个 `QUADRATIC_SKETCH_<scene>.npz`来自已存在workspace；其导出/传输计费，没有重做物理。gate没有因为这些解释性诊断改变。
