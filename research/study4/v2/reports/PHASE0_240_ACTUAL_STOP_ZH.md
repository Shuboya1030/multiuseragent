# Phase0修订240：首请求HTTP429，研究答案仍未取得

**实际执行了新的240范围，但第一条模型POST即HTTP429，0/240完成、0四臂配对、0环境工具。**
已按约定停止；没有第二call、response GET、自动重试、旧请求重放或训练/GPU。
这不是把离线验收当作完成，也不是训练门“不通过”：当前根本没有足够新数据判门。

[可审查机器证据与完整240清单](PHASE0_240_ACTUAL_STOP_CHECK.json)；
[此前25/720及两项实现修复](PHASE0_ACTUAL_STOP_AND_REPAIR_ZH.md)仅保留诊断，未混入本批。

## 本次真正执行的范围

- 用户直接“继续吧”，来源`dccf1924-a562-4335-bbca-c6f929b24f2e` revision8；
  协调者转达此前已缩减为60题×4臂×1，共240episodes。
- 源冻结`028793a`，协议`study4-formal-phase0-native-llmnpc-2`，
  run为`study4-formal-phase0-240-20261112-v1`；
  新清单按同题四臂成块、must/optional交替、轮换臂序，60题等权，单repeat不证明重复稳定性。
- 固定`gpt-5.4-mini-2026-03-17`、同一R1自然语言LLM NPC、严格单原生函数、
  相同普通工具与行动上限；B/D特权仅路由when/whom，不代填答案。
- 已修复公开事件/回复重复膨胀和同字节write使已post失效的问题。
  what只引用公开已读同事回复及请求绑定，保留否定/冲突，不凭草稿伪造NPC确认。
  公开计算仍由执行器自行形成和解释；不硬编码7800或题号。
- 全部378旧calls、373settled、5unknown在首次凭据注入前核验并绑定。
  首个完整四臂块本拟兼作实际验收，**没有另发独立probe**。
  44项冻结前离线回归通过不代表研究成功。

## 实际失败边界

| 项目 | 实际记录 |
|---|---|
| slot | `m-med-service-credit:A:r0`，第一条ordinary请求 |
| HTTP状态/阶段 | `429` / `status` |
| 请求体 | **14756 bytes**；system+user两个input item，无历史native receipts/公开历史事件 |
| 耗时 | 1625ms，`deadline_expired=false`，cleanup错误为空 |
| response/usage | 无持久response body、无JSON输出、无usage/token数 |
| 工具/任务评分 | 0工具，未完成episode；不是业务0或任务失败 |
| 行为 | unknown保留、整批停止；无第二POST/GET/retry |

这条请求不是127651token的长对话；**去重并未证明可以消除429**。
现有证据不能区分TPM/RPM速率限制、账户quota/账单限制或其它429原因。
不能把没有usage解释成未收费，也不能把unknown预留解释成实际付款。
原HTTP状态明确，不是本地action decoder、参数校验或scorer失败；
供应商是否已验证请求schema并无证据，此前根因边界未被改写。

## 同一个USD50硬帽

| 项目 | USD |
|---|---:|
| 之前settled上界 | 3.962225025 |
| 之前unknown预留 | 4.290000 |
| 本次新增unknown预留 | .858000 |
| **累计占帽** | **9.110225025** |
| **剩余额度** | **40.889774975** |

累计379calls＝373settled＋6unknown，0in-flight。
本次0settled；不结算或释放任何旧unknown。
unknown合计**5.148**是保守未决占用，不是确认实付。
此前八个root的原字节及378条历史状态在本次退出后再核一致。

## 后续有界零API诊断修订

本次冻结HTTP实现遇非200即抛出，因此没有读取错误正文或限速头。
原失败不能事后恢复或声称已知子原因；本次实际证据、账本及源冻结不变。
协调者随后明确要求补齐这一个诊断缺口，**不是再次付费授权**。

新HTTP诊断版本`study4-http-stages-2-safe-error-fields`在原`status`失败路径：

- 在相同deadline内至多读取16KiB错误正文，额外1 byte仅检测超限；
  只保存静态允许列表中的`error.type`/`error.code`，例如`insufficient_quota`、
  `rate_limit_exceeded`、`tokens`、`requests`；未知值仅记`unrecognized`。
- 仅保留校验后的`Retry-After`秒数/UTC时间、数字型rate-limit limit/remaining、
  规范duration转换的reset毫秒以及限定格式的provider request ID。
  不保存任意message、完整body/headers、Authorization、cookie或凭据。
- 非JSON、缺字段、超限及采集错误明确标记；采集失败不能掩盖原HTTP状态。
  原首失败仍为`stage=status`/429；即使读正文失败也继续unknown并停止，不变成成功或自动释放。
- 本地quota型、rate型、非JSON、缺字段、未知值及超限fixture，
  经真实loopback HTTP→ledger→关闭/重开核验；正文读取失败另用伪connection核验首失败不覆盖。
  敏感marker不落盘、无重试。
  这是离线诊断验收，**没有provider实证或新模型请求**。

最终51项离线回归通过（transport诊断、Phase0、原生接口、持久账本）；
本次实际raw文件、八个旧root原字节和冻结源commit均再核一致，用户方法原文未改。

未来若供应商确实返回受支持的结构化code/type，可区分“供应商声明的quota型”和“rate型”；
若没有字段、非JSON或值不在白名单，仍无法判断。不从头数值推断账户账单状态，
不因存在Retry-After而自动重试。改动改变runtime hash，当前旧批准不能直接启动新版。

## 研究答案与必要下一步

本批A/B/C/D的R、T、excessC、Nauth、Nwaste及交付/ASK指标均**无新完成例可计算**；
240全部缺失，H1–H5无法由本批判定，B−A或D−A≥.10训练门仍unknown。
旧25仅诊断，尤其旧C/D what与桥接bug不能作为忠实最终Phase0数据。
没有研究依据启动训练，未宣称联合策略胜出，也没有将H5跨模型对照加入本轮。

下一恢复前需要先获得账户/供应商侧429类型及相应解除条件的证据，
再有明确有界授权、更新源冻结并把本次379calls/373settled/6unknown继续计入原50。
本报告不触发该恢复，不用无目的probe替代原因分析；也不承诺余40.89能完成240。
