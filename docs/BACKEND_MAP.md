# 后端、坐标与信息边界

物理内核固定来自 `migodam/a20-opm-imaging@b85a29a51f4ea7b4d93617e827d88e23933b89df`。
`src/a20/{backend,opm,costs}.py` 与 `vendor/a17/a9_engine.py` 是复用文件；A23 没有改写 Maxwell solver。

| 数学对象 | 实现与布局 |
|---|---|
| 材料 | `ReferencePhysics` + `MaterialChart`；1728 cells，3456实质量坐标，`x=sqrt(v)*[Re(delta chi),Im(delta chi)]` |
| 体积、频率 | v=(1.5/12)^3=0.001953125，k=2；所有源/接收器采用场景冻结几何 |
| 电流 | 每源5184复分量，`c=j/sqrt(v)`；源数6 |
| 测量 | 每源128复通道；按源依次 `[Re128,Im128]`，合计1536实维 |
| 白化 | pack 后采用已知背景场的RMS尺度；实伴随使用同一转置。复噪声每实/虚分量方差sigma²/2 |
| 极化率 | A17 CM/RR；复a、a′和解析a″一致；实材料动作包含实/虚两块 |
| 完整线性映射 | `ReferencePhysics.matrix()`，接收伴随Z*=S L_b^-1，按源流式与B收缩；不分配 current×material Jacobian |
| 二阶 | `ReferencePhysics.quadratic()`，反馈项和local a″项；Q含Hessian的1/2 |
| χ/a先验 | a增量使用h=a′_b deltaχ的pullback坐标；同一D、同一lambda；强幅度下只声称局部先验匹配 |
| Schur | 原`SchurFeedback`与`CachedSchur`，同core guard，无jitter、pinv或automatic fallback |
| 估计 | `TikhonovDecoder`，lambda=1e-3*smax(A_ref)^2，γ=1；输出不裁剪，材料不合法即拒绝 |

在线模块只持有已知几何、背景、测量、参考场、参考映射和冻结decoder。Known-background J 合法；truth-state J、full-GN optimum、旧oracle current不加载。`data/online`通过白名单；`data/offline_eval`只由离线标签生成/误差评价器读取。曲率的truth-direction审计是OFFLINE，不用于挑选方法或参数。

原A22对象测量的生成网格是14，当前solver材料网格是12。旧测量因此没有作为本次clean标签；本次12个多源full-wave标签在相同n12模型上付费生成。旧32维chart仅作离线投影诊断，不限制成像输出。

背景、源、接收器、频率、材料metric、白化和probe配置共同决定缓存。首次H1缓存没有序列化完整key的缺口被记录；pilot付费重建一次完整transfer与decoder，逐元素核对背景映射并写新provenance，不覆盖原H1缓存。
