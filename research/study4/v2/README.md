# Study4 v2：共享协议、固定scorer与本地调度验收

**当前完成本地协议/fixture与六题scorer/四臂调度适配；没有运行mini四臂ceiling、训练或5000题生成。**
旧SFT87及其32episode结果不变，[旧结果入口](../README.md)继续保留。

阅读：[v1.1设计/变更合同](DESIGN_v1_1_ZH.md)＋[v1.2本地适配补充](LOCAL_ADAPTER_CONTRACT_v1_2_ZH.md) →
[最新实际阶段报告](reports/LOCAL_ADAPTER_STAGE_ZH.md)（[前阶段](reports/PHASE1_LOCAL_ZH.md)保留） →
[ceiling pilot与预算待签](CEILING_PILOT_ZH.md)。
原[用户v1设计](../STUDY4_CONTROLLER_DESIGN_v1.md)及
[论文侧建议](../ADVICE_FROM_PAPER_SESSION_20261111.md)保留，修订冲突以v1.1为准。

## 可实际复跑的零网络检查

在本研究分支的repository root运行（Python标准库，不安装包）：

```powershell
python -m unittest research.study4.v2.test_protocol -v
python -m unittest research.study4.v2.test_ceiling_adapter -v
python -m research.study4.v2.local_acceptance --output LOCAL_PROOF_NEW.json
python -m research.study4.v2.local_ceiling_check --output LOCAL_ADAPTER_NEW.json
```

CLI拒绝覆盖existing output；它只写指定的新JSON，不读取旧模型/episode/账本、凭据或其他私有目录。
`LOCAL_PROOF_NEW.json`是手写fixture proof，不是benchmark score；
无需/不可连接Colab、API或receiver。
`LOCAL_ADAPTER_NEW.json`是六个公开开发题包×四臂的脚本回放与真实固定scorer，不是mini推理。
报告中的public signature兼容检查也不是完整生成器可辨识性证明。

## 模块边界

| 模块 | 当前实际能力 |
|---|---|
| [contracts.py](contracts.py) | public/private分型、合法动作、workspace与DAG结构检查 |
| [executor.py](executor.py) | 一套普通tool schema/prompt；注入固定回调；问题intent/选定已获值保留验收 |
| [runtime.py](runtime.py) | 内存workspace、稳定send/reply/read、公开progress、SELF一步/ASK自动读后一步、提交门、私有snapshot |
| [npc_rule.py](npc_rule.py) | 小fixture确定性依赖/context/authority release与明确refusal |
| [oracle.py](oracle.py) | 特权DAG路径参考、多合法标签与不可辨识检测，非理论最优 |
| [fixtures.py](fixtures.py) | 9个手写单元环境及public-only deterministic executor |
| [local_acceptance.py](local_acceptance.py) | 实际运行reference/always-SELF proof，输出来源指纹和未通过的真实门 |
| [test_protocol.py](test_protocol.py) | 行为、消息/来源、拒绝、交付、观察、上下文等针对性测试 |
| [benchmark.py](benchmark.py) | 固定MIT资产、public-only题包构建、结构化规则NPC与官方scorer证据绑定 |
| [mini_request.py](mini_request.py) | Responses候选wire payload，本地callback/全请求计数；无HTTP或key |
| [scheduler.py](scheduler.py) | 四臂权限、关键点合并、proposal复用/ASK失效刷新 |
| [budget.py](budget.py) | 内存模拟token/call/episode/USD reservation与unknown-stop；非paid ledger |
| [training_data.py](training_data.py) | 三头acceptable tuple/mask/public投影与严格cross-group proof |
| [test_ceiling_adapter.py](test_ceiling_adapter.py) | 六题适配、私有边界、调度、费用和监督接口针对性测试 |

v1的`HelpRuntime/ServiceRuntime`不改：本版本保留它们的tool envelope、虚拟路径边界、
stable ID/幂等读和ASK→自动交付→普通一步语义，做独立的小型本地协议实现。
没有引入旧REST/API transport；因为旧完整实现未随报告公开，
v2采用标准库自包含边界，避免新代码依赖未上传的运行包。
这不是重写整个旧系统，也不是已接入真实mini的声明。

三头/candidate-shared-scoring有[数据接口](training_data.py)与[train-only sanity规范](configs/fit_sanity_spec.json)，
尚无模型头/训练器。proposal失效/关键点合并已通过本地mock，真实API持久调用绑定未通过。
context_view仅验收保留/溢出规则，未用真实Qwen tokenizer证明6k容量。

## 指纹与未决门

[Scorer实际版本绑定](configs/scorer_binding.json)、
[预算/任务方案](configs/ceiling_pilot.json)、
[实际9fixture报告](reports/LOCAL_ACCEPTANCE.json)及
[前阶段文件指纹](reports/PUBLICATION_MANIFEST.json)（仅针对历史commit `31edc9f`）。
当前[本地适配证据](reports/LOCAL_ADAPTER_CHECK.json)与
[当前发布字节指纹](reports/LOCAL_ADAPTER_PUBLICATION_MANIFEST.json)另列。
TribalBench原MIT scorer已固定字节、复制并实际本地执行；旧fixture checker依然不是`tribalbench-1.0`。
付费ceiling、真实API/NPC语义/持久费用、新split/generator/模型均需后续阶段门。
