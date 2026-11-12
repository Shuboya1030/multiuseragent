# 响应失败诊断v2：已接入持久路径，未发第二call

2026-11-11。**已修复“失败只剩ValueError、无法定位”的日志工程缺陷；没有证实原请求的具体根因，
也没有放宽响应/动作校验。** 原真实批次仍是capUSD50、1call unknownUSD.858、0settled、0tools、
0完整episode。没有第二call/response GET/重放/settle或释放unknown。

原失败源码与证据先固化在commit `88f1134`，例如
[原decoder](https://github.com/Shuboya1030/multiuseragent/blob/88f1134/research/study4/v2/admission.py)。
后续变更另立runtime/plan schema3、ledger metadata `study4-v2-durable-2-diagnostics`，
新runtime绑定诊断及恢复guard源码，不重新解释旧metadata/旧诊断。
原批次文件和旧SFT87/32评测/closed ledger的hash均未改。

## 不是独立helper，而是实际失败持久化路径

`HTTPTransport → DurableLedger.call → decode_response`中逐阶段标注：

| 阶段 | 失败边界 |
|---|---|
| response_json | 完整provider body的strict JSON解析 |
| response_envelope | root、model/tier/status/id/error/incomplete与output入口 |
| output_items | output item的数量、type、role |
| output_content | content数量、output_text type/string |
| usage | input/output整数、存在性与保守/请求上界 |
| application_json | output_text中的strict JSON解析 |
| application_validation | 固定动作/schema、工具arguments JSON及精确合法字段/值 |

`ResponseStageError`只带白名单阶段、cause类型、repo相对validator函数/源码行；
不携带任意异常正文。`DurableLedger`在unknown事务中原子保存这些字段、
原response SHA/长度及`response_shape`，仍全额占帽并整批停。
普通HTTP/socket无raw时仍没有伪造response或成功形状。

shape保留顶层/嵌套白名单key集合、值类型、item/content计数以及允许的type/tool枚举，
未知key仅计数，不保存名字；不留模型任务正文、参数值、路径、refusal文本、header/key。
能够描述空output、reasoning item、多item、message/output_text、refusal及function_call等形状，
**描述合法provider envelope的形状不等于放行它**：
现有单assistant message/单output_text/固定tool/action规则仍原样拒绝不符合本协议的输出。
函数/行号能进一步区分JSON解析、`validate_output`和`parse_tool`，不改业务schema来绕门。

## 实测不是原响应重建

新增4项[持久诊断测试](../test_persistent_diagnosis.py)，加此前95项共99项通过。
其中一个测试为7个阶段各启动真实子进程：模拟响应失败、commit unknown、进程退出，
由父进程重开**临时测试账本**，逐个核验阶段、函数/行号、shape和USD.858保留。
另验证多种envelope形状可安全描述、旧metadata拒绝被新版本重解释、
恢复申请缺批准时文件创建前阻断。

[机器证据](PERSISTENT_DIAGNOSIS_V2_CHECK.json)含这7个**合成provider**的实际持久读回值。
它们不是原真实response；原raw和traceback已随原进程退出丢失，无法补回。
原实际model/default/completed与reported1101/133只证明[原报告](CEILING50_ACTUAL_STOP_ZH.md)列出的边界，
不能据mock的extra reasoning/参数错误候选擅定根因。

## 恢复只能是另行批准的单请求诊断，不是重开48批次

[默认禁用候选](../configs/ceiling50_diagnostic_recovery_PENDING.json)显式继承原ledger SHA、
原unknown1/.858及原settled0，仍是**同一总capUSD50**。新一次诊断最多再reserve .858，
若也unknown累计占帽1.716，而不是换root后重新获得50。
待批source为null；旧48scope/50金额批准不能替代新的诊断例外授权。

[recovery_guard.py](../recovery_guard.py)在文件/网络之前核验新来源和精确recovery绑定；
新provider恢复dispatcher本轮仍硬禁用，即使模拟一个格式匹配的批准也不会联网。
仅在LOCAL_TEST中模拟显式诊断例外：旧.858先计入exposure，再reserve新.858并unknown后保持1.716，
max_calls1阻止第二次；这是门与记账测试，不是正式账/额度变更。
原fresh driver只接受精确48-slot计划，不能把这个单请求候选误作可执行批次或应用工具。

新候选不是实际批准/正式账本，也没有把原unknown转settled。
后续只有父协调线程拿到具体新授权、核对旧占用并冻结真实诊断执行域后，才可实现/启动
**0环境工具**的单请求路径；本轮不默认继续，更不因API接口失败进入重训或涨预算。

[原真实停止证据](CEILING50_ACTUAL_CHECK.json) ·
[本次公开字节指纹](PERSISTENT_DIAGNOSIS_V2_PUBLICATION_MANIFEST.json)
