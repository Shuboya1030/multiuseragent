# 单请求恢复诊断：实际返回两个动作，已停且未执行工具

2026-11-12。用户在“原USD50内一次诊断、旧USD.858继续占用”的明确请求后回复continue，
本轮按该限定执行了**恰好1次**真实请求，没有恢复48episode实验。
结果：snapshot/default/completed与顶层JSON正常，**两个assistant消息各含一个工具动作候选**，
在`output_items`阶段拒绝；0工具、0完整episode。没有第二诊断call/response GET/retry。

## 本次实际证据，不是候选模拟

请求复用原slot `o-low-team-lunch A r0` 第一次ordinary的完整payload，
SHA `977150bed8a4c3477abbee2fa260b5e782925770747b2cd2a626e91acbacd8c9`。
原公开任务/历史/mini snapshot/规则NPC配置、max_output_tokens1024和普通工具权限均不变。
NPC没有被联系。没有用本次调用补齐原raw，原失败响应仍不可恢复。

实际诊断在UTC `2026-11-12T18:22:55`结束。response为3531bytes，
SHA `8771ed5e7e505d482885843e044636de7c168488efc7ed1c57484f2c19f3de04`。
新账本和独立shape文件都持久化了下列白名单信息：

| 层 | 实际值/形状 |
|---|---|
| model/tier/status | 固定snapshot完全匹配、default、completed |
| reported usage（NOT settlement） | input1101、output134 |
| output | list，2items，均type message、role assistant |
| 第1item content | 单output_text；应用JSON key为tool/arguments，均str；tool=write_file；参数key content/path、均str |
| 第2item content | 单output_text；应用JSON key为tool/arguments，均str；tool=post_channel；参数key channel/content、均str |
| 精确失败阶段 | output_items；cause ValueError，外层ResponseStageError |
| 实际validator frames | response_diagnosis.at_stage:35 → admission.message:145 → contracts.require:33 |
| 执行 | 0环境工具、0contact、0完整episode，停止 |

行号绑定本次冻结source，不代表未来修改后的行号。
[机器实际证据](SINGLE_DIAGNOSTIC_ACTUAL_CHECK.json)含原shape、阶段和源码指纹，
不含任意模型正文、任务值、API key/header、原请求或数据库。
没有读取/公布两个消息的任务值，也没有声称这些参数值业务正确。

## 能定什么因，不能定什么因

**本次已证实的直接原因是单动作协议与多消息动作输出冲突**：
decoder要求output恰好一个assistant message，实际为两个。
这次不是reasoning metadata加一个message，不是SDK的output_text convenience缺失，
也不是usage或output_text JSON解析错误。typed shape独立解析了两个候选的JSON和参数形状，
但主decoder在output_items已停，并未执行应用合法性或参数值校验。

不能把该结论倒推为昨天首call必然同因：相同请求不保证相同响应，
首call的raw/traceback缺失，其具体分支依然未知。
这是模型输出契约违例/适配机会，**没有证明需要放宽schema，也没有发现“只取第一条”可安全成立**。
两个动作不能在一个SELF中一起执行；不能默默丢第2消息，也不能把业务post视为无害旁白。
本次失败不是业务/T/R=0，更不是controller训练能力测量。

## 总cap50：旧unknown不动，新unknown继续占帽

| 费用记录 | calls | settled | unknown保留 |
|---|---:|---:|---:|
| 原ceiling首call | 1 | 0 | USD.858000 |
| 本次单诊断 | 1 | 0 | USD.858000 |
| 同一USD50总范围累计 | 2 | 0 | **USD1.716000** |

USD1.716是未决保守占帽，不是已认证实际花费。
本次reported1101/134按冻结保守单价推导为USD.001571625，
仅是**未settle参考**，不用于释放.858、不改原账本。
余额看似足够也不允许下一call：单请求授权已经用完，unknown门仍关闭。

## 真实执行前工程门与安全边界

[diagnostic_dispatch.py](../diagnostic_dispatch.py)只调用一次ledger，不导入/运行任务环境进行工具应用，
没有循环、resume或response GET；仅复用原请求作输出契约诊断。
新source/plan/批准/root/原requestSHA绑定后才建全新记录，原.858先计入同50exposure，
并持有原批次mutex避免并行占用；每次permit前也重核旧证据与当前来源。
真实密钥仅沿用User→当前Process注入，未打印/落盘/传Colab。

两个本地前置门先于网络阻断过，没有因此多发模型请求：
原保留的WAL为0bytes、shm也在原hash清单内；现在允许immutable主DB读取，
但任何非空WAL帧仍拒绝，绝不删除/修改sidecar。
Windows自持byte-range mutex不允许再读该锁字节；锁内跳过**仅mutex文件**的hash读取，
所有研究/账本文件仍逐字节核验，锁外再实核完整清单（含mutex）。
两次阻断均在START/新DB/网络前；冻结前置配置及更正原因已另存，不冒充付费retry。

新增4项dispatcher测试（此前99项，合计103项）涵盖：
恰好一个成功调用只settle新费用、旧.858仍占用且0tools；
多item失败累计1.716、禁止再启动；
原证据/请求漂移在调用前挡住；
原冻结空WAL允许但非空帧拒绝。真实发出前，Windows锁修正后的34项直接相关测试也已通过。
后续同源验证与远端复现另见[发布验收](SINGLE_DIAGNOSTIC_PUBLICATION_MANIFEST.json)。

## 后续ceiling条件

**尚不具备恢复ceiling的完整接口验收条件。** 单消息/单动作的provider实测门仍失败，
没有真实完整episode或四臂配对收益；privileged参考也没有变成trained-controller能力。
已按随后限定的零API修正，将[共享ordinary prompt](../executor.py)版本明确为
`study4-ordinary-single-action-v2`：当前回合只选一个动作，一个final assistant消息后停止等工具结果；
禁止commentary/第二个JSON/当前响应中的后续post或submit，
write→post→submit只作为多个未来交互回合的总目标。四臂共用同版，action/tool/参数门原样不放宽。
原实际发送源码先固化在commit `0f88f231f962f41566bd3e9f7e3a8638d1f4fdc7`，
原请求与两个unknown账本不改，新prompt另有source/prompt_version binding。
这只是消除潜在请求歧义的缓解；**没有证明旧多步措辞是本次双消息的因果根因，
也没有真实验证新prompt一定单条。** 多动作仍拒绝，不取第一条、不合并执行、不扩大SELF。
新增[2项离线回归](../test_prompt_single_action.py)验证四臂同请求、单合法动作接受、
双message及坏参数仍拒绝。零额外API，完整验收105项。
旧24脚本适配报告文件保留；新prompt改变mock请求token成本，
[新版本脚本适配报告](LOCAL_ADAPTER_PROMPT_V2_CHECK.json)单列，不冒充原字节复现或新模型收益。
任何再验证或恢复48slot均需新的明确范围/费用处置批准；本轮不再付费。
不连接GPU、不恢复旧训练、不扩题或调reward。
