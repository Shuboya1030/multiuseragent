# Study4 v2：共享协议、固定scorer与本地调度验收

**最新验证通过后已启动真实ceiling，首slot在7个普通动作后因双message输出整批停。
0完整episode/配对；累计unknownUSD3.432＋settled上界USD0.013762650，
占原USD50总帽。尚无四臂headroom或训练收益；没有新训练或5000题生成。**
旧SFT87及其32episode结果不变，[旧结果入口](../README.md)继续保留。

阅读：[v1.1设计/变更合同](DESIGN_v1_1_ZH.md)＋[v1.2本地适配补充](LOCAL_ADAPTER_CONTRACT_v1_2_ZH.md) →
[原生单函数升级合同](NATIVE_FUNCTION_PROTOCOL_v1_ZH.md) →
[最新实际ceiling部分轨迹/停止报告](reports/CEILING_V2_ACTUAL_PARTIAL_ZH.md) →
[前次prompt v2传输停止与诊断修复](reports/PROMPT_V2_VALIDATION_STOP_ZH.md) →
[前次双动作诊断](reports/SINGLE_DIAGNOSTIC_ACTUAL_ZH.md) →
[持久诊断v2修复](reports/PERSISTENT_DIAGNOSIS_V2_ZH.md) →
[USD50真实接口停止报告](reports/CEILING50_ACTUAL_STOP_ZH.md)（[模型最大费用上界](reports/MODEL_MAXIMUM_BOUND_ZH.md)、
[持久执行前门](reports/DURABLE_PREFLIGHT_ZH.md)、
[适配阶段](reports/LOCAL_ADAPTER_STAGE_ZH.md)、
[第一阶段](reports/PHASE1_LOCAL_ZH.md)保留） →
[ceiling pilot与预算待签](CEILING_PILOT_ZH.md)。
原[用户v1设计](../STUDY4_CONTROLLER_DESIGN_v1.md)及
[论文侧建议](../ADVICE_FROM_PAPER_SESSION_20261111.md)保留，修订冲突以v1.1为准。

## 可实际复跑的零模型调用检查

在本研究分支的repository root运行（Python标准库，不安装包）：

```powershell
python -m unittest research.study4.v2.test_protocol -v
python -m unittest research.study4.v2.test_ceiling_adapter -v
python -m unittest research.study4.v2.test_durable_preflight -v
python -m unittest research.study4.v2.test_provider_bound -v
python -m unittest research.study4.v2.test_paid_driver -v
python -m unittest research.study4.v2.test_persistent_diagnosis -v
python -m unittest research.study4.v2.test_diagnostic_dispatch -v
python -m unittest research.study4.v2.test_prompt_single_action -v
python -m unittest research.study4.v2.test_ceiling_continuation -v
python -m unittest research.study4.v2.test_transport_diagnosis -v
python -m unittest research.study4.v2.test_native_protocol -v
python -m research.study4.v2.local_acceptance --output LOCAL_PROOF_NEW.json
python -m research.study4.v2.local_ceiling_check --output LOCAL_ADAPTER_NEW.json
```

CLI拒绝覆盖existing output；它只写指定的新JSON，不读取旧模型/episode/账本、凭据或其他私有目录。
durable tests仅创建临时SQLite及本机127.0.0.1 HTTP服务，故障退出的子进程与服务均结束/清理；
不访问provider、不开正式paid ledger。它不是完全“零socket”测试。
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
| [admission.py](admission.py) | 独立授权/价格/runtime/static schema与模型最大token费用bound；USD50已批，真实完整接口未验收 |
| [provider_bound.py](provider_bound.py) | 固定snapshot/standard纯文本域的272000＋128000模型上界，非税费等所有账单保证 |
| [durable.py](durable.py) | 持久reserve/settle/unknown、崩溃恢复、一次call缓存与OS批次互斥 |
| [http_transport.py](http_transport.py) | 一次性HTTP、无隐式key/代理/redirect/retry；实际传输阶段/脱敏错误与cleanup诊断，不回填旧unknown |
| [test_durable_preflight.py](test_durable_preflight.py) | 真实子进程退出/并发、SQLite与loopback故障注入测试 |
| [paid_driver.py](paid_driver.py) | 绑定独立批准/唯一fresh批次，逐call/event/slot持久证据；中断后禁止工具或episode重放 |
| [test_paid_driver.py](test_paid_driver.py) | 48slot脚本回放、漂移/usage失败、工具生效后中断及禁止二次启动 |
| [response_diagnosis.py](response_diagnosis.py) | 实际decode路径逐阶段错误和脱敏shape，失败事务持久化；不保留任意正文 |
| [recovery_guard.py](recovery_guard.py) | 显式来源/批准绑定的单诊断例外门，同50总帽先计入旧unknown；一次额度已用完 |
| [test_persistent_diagnosis.py](test_persistent_diagnosis.py) | 7阶段真实子进程退出后读回、旧metadata拒绝、累计旧占用与新批准门 |
| [diagnostic_dispatch.py](diagnostic_dispatch.py) | 显式新批准的一次请求，继承旧unknown并持原批mutex；不执行工具、不恢复episode |
| [ceiling_continuation.py](ceiling_continuation.py) | 新来源绑定的一次prompt v2验证，继承两笔旧unknown；只有合法settle才允许原48slot fresh批次 |
| [test_ceiling_continuation.py](test_ceiling_continuation.py) | 临时ledger/mock的同帽、前置成功门、48脚本slot、互斥、漂移/重复拒绝及传输候选边界 |
| [test_transport_diagnosis.py](test_transport_diagnosis.py) | 子进程退出/重开后的HTTP阶段、敏感异常不落盘、主错误/cleanup优先级及unknown/no retry |

v1的`HelpRuntime/ServiceRuntime`不改：本版本保留它们的tool envelope、虚拟路径边界、
stable ID/幂等读和ASK→自动交付→普通一步语义，做独立的小型本地协议实现。
没有引入旧REST/API transport；因为旧完整实现未随报告公开，
v2采用标准库自包含边界，避免新代码依赖未上传的运行包。
这不是重写整个旧系统，也不是已接入真实mini的声明。

三头/candidate-shared-scoring有[数据接口](training_data.py)与[train-only sanity规范](configs/fit_sanity_spec.json)，
尚无模型头/训练器。proposal失效/关键点合并已通过本地mock，
持久调用边界通过本地故障测试，模型级费用bound已核来源/本地实现；
真实完整API/应用接口与tool/episode端到端恢复未通过；
本轮规则NPC48slot上限已获独立USD50批准；最新preflight通过后真实batch首slot遇新unknown，
0完整episode，不能自动重发；此前三个unknown也不释放。
context_view仅验收保留/溢出规则，未用真实Qwen tokenizer证明6k容量。

## 指纹与未决门

[Scorer实际版本绑定](configs/scorer_binding.json)、
[预算/任务方案](configs/ceiling_pilot.json)、
[实际9fixture报告](reports/LOCAL_ACCEPTANCE.json)及
[前阶段文件指纹](reports/PUBLICATION_MANIFEST.json)（仅针对历史commit `31edc9f`）。
当前[本地适配证据](reports/LOCAL_ADAPTER_CHECK.json)与
[适配阶段字节指纹](reports/LOCAL_ADAPTER_PUBLICATION_MANIFEST.json)仅绑定历史commit `e623794`。
[持久执行前门证据](reports/DURABLE_PREFLIGHT_CHECK.json)及
[其发布字节指纹](reports/DURABLE_PUBLICATION_MANIFEST.json)绑定历史commit `aa6480a`；
其中provider bound未证明的结论由[本次有界修正](reports/MODEL_MAXIMUM_BOUND_ZH.md)更新。
[模型上界机器验收](reports/MODEL_MAXIMUM_BOUND_CHECK.json)与
[其发布字节指纹](reports/MODEL_MAXIMUM_PUBLICATION_MANIFEST.json)绑定历史commit `77f1a11`。
[当前实际停止证据](reports/CEILING50_ACTUAL_CHECK.json)、[冻结scope摘录](reports/CEILING50_FROZEN_SCOPE.json)与
[原失败发布字节指纹](reports/CEILING50_PUBLICATION_MANIFEST.json)绑定历史commit `88f1134`。
[持久诊断机器验收](reports/PERSISTENT_DIAGNOSIS_V2_CHECK.json)与
[其发布字节指纹](reports/PERSISTENT_DIAGNOSIS_V2_PUBLICATION_MANIFEST.json)绑定历史commit `0cfe45c`。
[前次单请求实际证据](reports/SINGLE_DIAGNOSTIC_ACTUAL_CHECK.json)与
[前次发布字节指纹](reports/SINGLE_DIAGNOSTIC_PUBLICATION_MANIFEST.json)绑定历史`8d10359`。
[最新prompt v2实际证据](reports/PROMPT_V2_VALIDATION_CHECK.json)与
[本轮发布字节指纹](reports/PROMPT_V2_CONTINUATION_PUBLICATION_MANIFEST.json)另列。
[零API传输诊断补丁验收](reports/TRANSPORT_STAGE_DIAGNOSIS_CHECK.json)与
[补丁发布字节指纹](reports/TRANSPORT_STAGE_PUBLICATION_MANIFEST.json)另列；
这是HTTP→ledger可诊断性修复，未发新的真实请求，也不推断旧传输原因。
[最新真实ceiling机器证据](reports/CEILING_V2_ACTUAL_PARTIAL_CHECK.json)与
[当前发布字节指纹](reports/CEILING_V2_ACTUAL_PUBLICATION_MANIFEST.json)另列。
TribalBench原MIT scorer已固定字节、复制并实际本地执行；旧fixture checker依然不是`tribalbench-1.0`。
真实ceiling未通过；新的真实请求、NPC语义/任务收益、新split/generator/模型均需后续阶段门。
