# Phase0暂停、gold reference缺陷与零API修复

2026-11-12。**问题已确认：B/D原完成检测不忠实于用户定义的gold when/whom，
不是可以只写成“保守routing局限”的正常实验结果。** 已停止付费；
本次52例不能回答Phase0训练门，更不能据负差值断言没有训练空间。
修复只在本地离线验收，没有新增POST/GET、重放、GPU或密钥读取。

## 1. 暂停的精确边界

冻结实际源码：`b36728cf74cc612a97931df4a5eebb3876cd0bae`。
完整52/240、13个四臂任务块（7 Must、6 Optional，每臂13例）。
第53个slot是`o-low-team-lunch:B:r0`，6call均已settle，但最后
`ordinary:3`返回的`post_channel`没有执行，episode不完整，不计业务0。
不发送下一个POST，也不重发该已settled结果。

| 账目 | 精确值 |
|---|---:|
| 本轮calls / settled / 新unknown / inflight | 643 / 643 / 0 / 0 |
| 包含历史的calls / settled / unknown | 1022 / 1016 / 6 |
| 本轮usage费用上界USD | 6.5190114000 |
| 历史settled上界USD | 3.962225025 |
| 原unknown继续预留USD | 5.148000 |
| 原50帽累计占用USD | 15.6292364250 |
| 剩余额度USD | 34.3707635750 |

unknown预留不是确认实付，settled值也不是供应商最终账单。
没有释放旧unknown，没有新开50帽。

冻结runner没有暂停接口。外部Windows字节区间锁仅阻断`events.jsonl`未来追加；
新请求必须先写`model_request`才能进入ledger/POST，因此下一准入被阻断。
已发送请求的HTTP与ledger结算未加锁、未终止。最后结果正常settle后，
`model_result`日志追加产生显式`PermissionError`，runner退出。
原receipt保留该原始类型：它是**操作员暂停，不是provider错误或新计费unknown**。
原journal仍是有效JSONL；最后未写入journal的结果及usage保存在ledger，
没有执行其工具。冻结计划、源、旧九个根目录及实际成绩均未改写。
屏障实际生效于23:51:22 UTC；不能将它描述成runner预先具备合作式暂停，
也不能仅凭该证据声称恰在暂停消息到达时的那个call后立即停止。
准确可核对的边界是slot52的上述已settled、未执行post，屏障后没有下一个POST。

## 2. ledger-allocation：原始规格与实际反例

公开任务原文：
> Prepare the November allocation entry for invoice INV-841. Save
> /workspace/deliverable.json with invoice_id, amount_usd, cost_center and
> ledger_period. Post a short entry summary and the file path in #engineering.

唯一gold节点原文：
```json
{"id":"mapping","admissible_recipients":["David Wong"],"information_ids":["H1"],"requires":[]}
```

H1：`facts={cost_center:CC-628,effective_date:2026-11-01}`；
`required_context=["INV-841","2026-11"]`；release_rule原文：
> Provide the November internal-tooling mapping for this invoice. You own both
> the mapping and its release; no separate authorization is needed.

节点没有另一个`completion`字段，也没有前置节点。`effective_date`是适用性记录元数据，
不是required_context、最终输出字段或下游必须传递值。公共posting-sheet确实规定按posting date
选择有效mapping，所以**不能忽略适用性**；但持有人已明确确认该invoice的November当前mapping时，
不需要机械复述`2026-11-01`才能知道应该用哪个cost center。
公开invoice提供USD2400和posting date 2026-11-02，不要求NPC重复确认公开金额。

D首次实际回复已明确：
> For **INV-841**, the November allocation entry should use:
> Ledger period: **2026-11**; Required cost center: **CC-628**.

B首次实际回复也给INV-841 / CC-628 / 2026-11，只说明自己不知道金额；
金额在公开invoice中，因此这不是mapping前置或信息缺失。
完整请求/回复、稳定message ID、SHA和原blueprint见
[原始诊断证据](REFERENCE_CONTRACT_AUDIT_20261112.json)。

冻结实现却把每个hiddenfacts的所有token都要求在**同一条**reply出现，
缺日期字面量就始终不承认mapping。B问4次、D问59次；
D的177call费用上界USD4.957084275，占本轮约76%。
第1次回复已足够，其后58次ASK不符合预定reference。
D最终仍写回错误CC-410：不能通过删联系/费用或离线改分假装得到修后反事实结果。

另一个已证实反例：backup B首次回复已给03:00 UTC / 14 days / 6 TB，
足以恢复要求的三个配置，却因没有逐字给完整maintenance日历而继续问。
`required_retention_days→retention_days`是必要输入映射，不能为修此bug把retention也删掉。

## 3. 拒绝、累积及影响范围

- 全句拒绝词不是可靠节点否定：“I cannot approve the separate requisition”
  不否定同条已确认的L5/B5；相反，实际interview回复明确不能确认certification，
  即便也出现panel size=4，不能算释放certified count=4。
- 同一来源/同一请求范围中，先确认L5、后确认B5，不能因没有一条同时包含两者而重复ASK。
  必须保留两条来源、授权前置及各自请求绑定，不能把任意跨人/跨记录字符串拼成事实。
- 此次有界检查26个B/D完整episode、13题；7题存在hidden key不直接等同输出key的结构风险，
  **不代表7题都错**：其中包括必要计算输入、别名和范围限定。明确实际误判至少ledger与backup。
  其余47题不声称已逐条做真实自然语言质量验收。
- 全token且含拒绝的实际interview例是**真正拒绝**；未发现这26例中“仅跨回复凑齐全部原token”
  的已证实实际反例。跨回复/无关拒绝机制另有明确标注的零API安全fixture，
  不冒充provider实证。

## 4. 实际修复与边界

新增私有`reference_completion.py`，通过原`reference_released`接入真实调度路径。
显式版本`study4-reference-completion-3`；只改私有完成判定及其绑定，
公共协议2的schema/prompt、executor/NPC、工具、what、限制、终止和scorer保持不变。
保留公共协议标识是为证明相同模型请求，不代表新旧私有routing可无标记混用。

全部60题/95节点已有可核对completion contract：
原node、information IDs、required_context、release_rule、字段角色及源SHA都在
[修复/保留清单](REFERENCE_REPAIR_REUSE_20261112.json)。
规则按字段语义、原输出/释放输入与适用约束编译，没有任务ID、答案或分数分支。
例如：显式当前mapping免机械复述生效日；backup仍要求window/retention/storage；
单位rate足以交给executor计算，不强迫NPC同时给派生total；不能把8%当USD0.08/word。

已实现同人/原请求绑定、**请求发出前**的DAG前置、真实上下文、
按字段的affirmative证据、跨回复逐值累积、冲突保留、数字逗号/小数/句末标点，
以及不把草稿/猜测/引用或无关数字当已释放。无关职责拒绝不再全局否定有效字段，
真实授权拒绝不放行；无法证明的引用或冲突抛`ReferenceUncertain`，不改成成功。
不把私有completion proof传入公开观察，不补答案或替executor写最终交付。

34项相关离线测试通过，包括原actual ledger/backup首回复、
95节点有序canonical fixture、缺值/错误/拒绝/草稿、跨回复与授权前置。
**canonical覆盖不是任意自然语言都已准确识别的证明，也不是新策略收益。**
这是有界确定性证明器；未证明的复杂自然语言仍需源绑定复核，
不能仅因marker通过就称完美语义oracle。正式付费入口已硬禁用，
旧revision10授权不能执行修后版本，等待协调者核验恢复边界。

## 5. 52例的严格保留判定

不是按arm名、结果或分数决定。对每例重建全部已记录模型请求并核对hash；
核对共享输入、NPC对话、工具、scorer及终止代码的冻结hash/AST；
B/D在每一个实际控制边界重放新when/whom，任何改变或不能证明均排除。
ASK之后强制ordinary一步不误当成新控制边界。没有调用模型或重新执行实际工具。
可复核脚本：`v2/tools/audit_reference_reuse.py ACTUAL_ROOT NEW_OUTPUT_JSON`；
输出采用排他创建，不能覆盖既有证据。

| 完整episode | A | B | C | D | 合计 |
|---|---:|---:|---:|---:|---:|
| 离线逐步等价、可复用候选 | 13 | 9 | 13 | 8 | **43** |
| 仅诊断，不可冒充修后轨迹 | 0 | 4 | 0 | 5 | **9** |

43例中Must24、Optional19。所有合格都列入，不择优；
候选仍需在新批准manifest逐一显式链接，并完成原有语义评分复核，
**不是43次已按新版本重新执行**。不合格slot为3/9/14/20/22/33/35/44/46；
原因和第一处分歧/未证在机器清单逐例保存。另一个partial slot52也不复用。
不能给旧B/D换decoder/删冗余ASK/改成本，来“修成”修后结果。

若协调者接受这43个候选，后续需**197个fresh slots**：
A47/B51/C47/D52＝原188个未完整slot＋9个不等价旧完整slot。
这是恢复清单，不是付费恢复；全部原52公开实际轨迹另存
`PHASE0_PAUSED52_PUBLIC.jsonl.gz`，原分数/账本/冻结源保持原样。

## 6. 下一执行范围与预算

剩USD34.370763575。按原52完整episode的全部实测均费外推197个新slot约USD24.662；
若仅去掉已证明ledger异常长loop的51例均费作敏感性情景，约USD5.998。
对应约2413/1777个模型call，**不是197个call**；两者均不是完成保证。
不能把修复推断成一定没有长对话、NPC拒绝、429或别的unknown；
64步长尾与单call .858预留仍可能提前触发预算/安全停机。

恢复必须先核验95节点解释与43例逐步等价清单，冻结新私有版本、保留/新跑映射及批准来源，
继承本次1022calls/6unknown/全部占用；不动原unknown。
此后才可在同一50帽内执行197个slots，不另发独立probe，不改指标/步数/timeout，
不挑重复，新的unknown仍停。当前不继续任何POST/GET/训练。
B−A或D−A平均R≥.10的门不变，但**目前未判，也不能用有缺陷B/D判瓶颈或H1–H5**。
