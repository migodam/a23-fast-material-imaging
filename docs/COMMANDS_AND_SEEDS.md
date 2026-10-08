# 实际执行与复现命令

以下按实际job manifest/receipt重建；工作目录归一成`<WORKSPACE>`，不包含私人连接参数。早期源码snapshot缺口见RUN_MANIFEST，不能据此反推未记录commit。

| job | stage/device | status | native命令 |
|---|---|---|---|
| a23-h1-001 | h1 / cuda | COMPLETE | `PYTHONPATH=src python -B -m a23.cli h1 --job a23-h1-001 --device cuda` |
| a23-micro-001 | micro / cuda | COMPLETE | `PYTHONPATH=src python -B -m a23.cli micro --job a23-micro-001 --device cuda` |
| a23-phase0-local-001 | phase0 / cpu | FAILED | `PYTHONPATH=src python -B -m a23.cli phase0 --job a23-phase0-local-001 --device cpu` |
| a23-phase0-local-002 | phase0 / cpu | COMPLETE | `PYTHONPATH=src python -B -m a23.cli phase0 --job a23-phase0-local-002 --device cpu` |
| a23-phase0-local-003 | phase0 / cpu | COMPLETE | `PYTHONPATH=src python -B -m a23.cli phase0 --job a23-phase0-local-003 --device cpu` |
| a23-phase0-local-004 | phase0 / cpu | COMPLETE | `PYTHONPATH=src python -B -m a23.cli phase0 --job a23-phase0-local-004 --device cpu` |
| a23-phase0-local-005 | phase0 / cpu | COMPLETE | `PYTHONPATH=src python -B -m a23.cli phase0 --job a23-phase0-local-005 --device cpu` |
| a23-phase0-remote-001 | phase0 / cpu | COMPLETE | `PYTHONPATH=src python -B -m a23.cli phase0 --job a23-phase0-remote-001 --device cpu` |
| a23-phase0-remote-002 | phase0 / cpu | COMPLETE | `PYTHONPATH=src python -B -m a23.cli phase0 --job a23-phase0-remote-002 --device cpu` |
| a23-pilot-001 | pilot / cuda | COMPLETE | `PYTHONPATH=src python -B -m a23.cli pilot --job a23-pilot-001 --device cuda` |
| a23-report-local-001 | report / cpu | COMPLETE | `PYTHONPATH=src python -B -m a23.cli report --job a23-report-local-001 --device cpu` |
| a23-report-local-002 | report / cpu | COMPLETE | `PYTHONPATH=src python -B -m a23.cli report --job a23-report-local-002 --device cpu` |

远端控制器负责deadline、queue、lock及childtail；native命令记录业务步骤，不表示controller开销免费。报告stage不执行Maxwell；最后BornBP baseline修正只重建derived表。

原理论验证脚本及实际adapter测试命令、seeds与费用在`results/a23/theory_verification/`。独立读者使用`tools/make_replay.py`创建空输出目录；不要在已发表目录自动重跑任何物理。
