# A23 H1 实现交付

状态：实现与小型算子检查完成；本子任务未运行场景实验、未判断 H1 gate。

- `src/a23/h1.py` 提供 `CachedSchur` 和 `build_h1(reference, config, output_dir, *, direct_preparation=None)`；返回 `(rows, matrices)`，八个 arm 的名称为 `original_opm`、`cached_opm`、`source_anchored_opm`、`source_anchored_om`、`mp`、`m_only`、`randomized_transfer`、`direct_adjoint`。
- Cached K/T/K*/T* 复用 FU/F*U 与原 LU；不增加 L 动作，保留原 unsafe-core 拒绝。原/cached transfer equality、unitary gauge、空 U、实伴随与 streamed transfer 均已检查。
- O/M probes 固定且跨 arm 相同；O 不读取观测残差或噪声。八个独立 full-cell material probes 含 smooth/local/edge/random，另有八个固定独立 data-dual probes。
- Source anchor 包含全部六个参考 current，再以 receiver columns 填充至最多八维；不 padding。P 同时报告原始 Kb norm、own-scale rank 和相对 forcing 的消失判定，避免把 roundoff 做成 P4。
- Transfer 按 128-cell blocks contraction；无 n-current × p Jacobian。随机 arm 固定 Gaussian32，真正支付每次 192 primal RHS 及 6×实际 rank adjoint RHS，不使用已缓存的 exact matrix 构造。
- 每个 arm 实际执行 cold1/warm5；记录 stages、动作、完整时间向量、失败、I/O、raw seed angles/rank 与 joint deflation。共享实际成本与独立部署归因分列，不作合计双计。
- Decoder-weighted error 使用共同 exact-reference Tikhonov：λ=1e-3×λmax(A Aᵀ)。优先读取 `reference.evaluation_decoder.decode`；没有时只建立 data Gram，不建立 p×p Gram。
- Direct control 的 independent matrix preparation 必须由 parent 的实测 cold1/warm5 receipt 通过 `direct_preparation` 传入；本模块明确标注自身仅复用 shared exact control，不能把这个缓存拷贝时间当成 direct construction。

验证：单线程，`Gaussian/.venv_nn/bin/python -m unittest discover -s tests -p test_a23_h1.py -v`，10 项全部通过，约 0.14 秒。该解释器没有 pytest，因此测试使用标准库 unittest；没有安装依赖、启动 worker/job、改变 config/gates 或读取 offline labels。

Parent 接口注意：`row['repeats']` 有六个完整 receipt；`metadata` 内有 retained/seed_records/seed_redundancy/hierarchy；`cold_encoder_preparation_wall_seconds` 与 warm 向量排除评价时间但包含 I/O 和 seed audit；`shared_actual_cost` 是一次共享支出，`shared_receiver_geometry_attribution` 是每 arm 的独立准备归因。科学结论、H1 比较与后续选择仍由 parent 决定。
