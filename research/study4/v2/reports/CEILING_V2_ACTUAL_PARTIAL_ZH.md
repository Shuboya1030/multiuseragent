# 一次验证通过，真实ceiling首slot因双动作停止

**2026-11-12：新验证通过，随后确实启动原定四臂ceiling；首slot尚未完成就遇到新的
双message动作，按约定整批停止。0完整episode、0四臂配对，不能判断特权参考headroom或训练收益。**
这次不是传输错误：provider返回completed/default及usage，严格`output_items`门拒绝。
未挑选第一条、未合并动作、未重试，失败输出没有执行。

[机器证据和7cycle索引](CEILING_V2_ACTUAL_PARTIAL_CHECK.json)；
[当前发布字节指纹](CEILING_V2_ACTUAL_PUBLICATION_MANIFEST.json)；
[此前传输停止与零API修复](PROMPT_V2_VALIDATION_STOP_ZH.md)保留为历史。

## 冻结范围与实际进度

本轮直接来源`137aeefe-fc9f-49ba-9565-951bc6e77dcf` revision 2，
用户原话“那你继续啊”。限定授权：再验证一次，合法通过后直接继续原六曝光开发题×四臂×两次，
最多48episode；同原USD50，旧三个unknown共USD2.574继续占帽。
没有新采集/RL/终测/GPU授权。

运行源码独立保存在commit **`34b0447481e3328295dac13e7b619ed6ae99a447`**，
仅对已验证恢复路径更新新source/version、三个旧unknown和对应上限，
没有改变普通工具、prompt、strict decoder、endpoint、timeout或proxy。
共享prompt仍为`study4-ordinary-single-action-v2`，
executor固定`gpt-5.4-mini-2026-03-17`，NPC为结构化规则NPC。
原48slot的相邻四臂均衡轮换顺序、题目/重复和24普通动作上限均未变。

| 阶段 | 真实结果 |
|---|---|
| 单请求preflight | 1调用，1275input/31output，单一assistant JSON，合同解析通过并settle USD0.001205325 |
| preflight动作 | `read_file("/workspace/deliverable.json")`；**未执行**，不计工具/episode |
| 条件batch | 实际启动；仅slot 00，`o-low-team-lunch / A / r0` |
| batch调用 | 10次：9settled、1unknown；7个成功ordinary输出、2个成功control输出 |
| 实际已用工具 | 写artifact 1次、读同一artifact 6次；共7普通动作 |
| 求助/交付 | 0ASK、0NPC、0post、0submit；联系成本0 |
| 停止 | 第10call，即`ordinary:7`，返回两个assistant消息，各包含一个`read_file`动作 |
| 未执行 | 被拒双动作；B/C/D及其余47slot；评分、训练、GPU或额外验证 |

preflight只验收HTTP、响应/应用schema和usage，不是环境执行测试：
初始workspace尚无deliverable，该合法格式的`read_file`若执行会被“文件不存在”门拒绝。
本次按原no-tools合同不执行它，不能说完整任务接口因此已获验收。
真实batch重新请求同一初态，得到`write_file`，没有重放preflight动作或其缓存。

## 实际trace：写完后重复读，没有完成交付

公开任务要求：22人的午餐订单，写`/workspace/deliverable.json`并在`#engineering`发布摘要和路径。
初始公开`order.md`已给22人、标准M1每人USD25、默认普通餐，
并明确HR持有饮食需求列表。公开目录含HR联系人。
这些信息都在模型公开观察；模型没有读取gold/未读NPC事实。

| cycle | 可见状态/缺口 | 实际ordinary动作 | when/whom与变化 |
|---|---|---|---|
| 0 | 初始无artifact；公开默认可得22/M1/普通餐/550，饮食改进信息未取得 | `write_file`：`{"headcount":22,"menu":"M1","vegetarian_meals":0,"total_usd":550}` | 调用公开control：SELF；artifact revision=1、公开shape有效，但未post/submit |
| 1 | 已有完整artifact原文和历史，delivery=false | `read_file`同一artifact | 非边界，调度合并为SELF；内容不变，增加tool_result |
| 2 | 同上，另有上次读取结果 | `read_file`同一artifact | 合并SELF；无新事实或交付 |
| 3 | 同上 | `read_file`同一artifact | 合并SELF；无新事实或交付 |
| 4 | 同上，触发“四个普通动作”边界 | `read_file`同一artifact | 第二次公开control仍SELF；无ASK |
| 5 | 同上，公开progress仍未post | `read_file`同一artifact | 合并SELF |
| 6 | 同上，remaining=17，仍未post/submit | `read_file`同一artifact | 合并SELF |
| 7未完成 | 请求前历史包含上述7动作，公开progress仍delivery=false | provider输出两条`read_file` JSON消息 | `output_items`拒绝，未产生controller决策/普通动作；technical_failure，整批停 |

七次SELF中**只有2次是实际模型control决策**，其余5次是既定边界合并的默认SELF，
不能说“控制器被问7次都拒绝求助”。没有ASK，所以没有NPC回复或权限grant。
也没有post，不是“内容已经交付但只缺bridge submit”。
文件存在、字段shape有效不等于业务/T/官方R达标。

可追溯机器索引逐cycle给出私有原始`events.jsonl`的0-based事件索引、1-based行号、
观察/请求指纹、记录指纹及摘要；原始日志保存在session，未上传完整请求/模型正文或本机路径。
摘录/索引不冒充原字节文件；原文件SHA另列。

## 停止证据与能确定的原因

失败call：`slot-00:o-low-team-lunch:A:r0:ordinary:7`。
HTTP已成功返回，固定model匹配、status completed、tier default；
reported usage **1990input/65output**仅作为未结算参考。
原响应3278bytes，SHA256
`85279fdc563655e259c78a3bdd727655ac20f7ba480bb43def51e7de05f33e03`。
白名单shape显示output_count=2，两项都为assistant message/output_text，
各有`tool=read_file`和`arguments`字符串、参数键`path`。
坏响应原文未保留，不能从shape恢复两次path值，不能说两条一定读相同path。

持久validator阶段为`output_items`，`admission.message:145`→`contracts.require:33`
（精确行号绑定运行源码commit）。不是reasoning元数据，不是transport/usage/参数解析失败；
门在解析两个动作之前拒绝，不能声称其参数内容均有效。
原账本将本次reserve USD0.858转unknown并停批，未用reported usage释放占用。

**已证实**：澄清prompt后有单动作成功，也仍出现双message，不能保证每次都单动作；
真实ordinary执行存在写后重复读取；公开progress已经明确未交付。
**未证实**：多message的完整因果根因、为何模型反复读、哪种协议/训练修复能提升成功率。
未修改schema、选首条、合并两动作、扩SELF或缩短上限强行产出结果。

## 同一个USD50费用与例数

| 项目 | dispatch尝试 | settled调用 | unknown保留 | settled保守上界 |
|---|---:|---:|---:|---:|
| 原三次历史 | 3 | 0 | USD2.574 | USD0 |
| 本轮preflight | 1 | 1 | USD0 | USD0.001205325 |
| 本轮batch | 10 | 9 | USD0.858 | USD0.012557325 |
| 累计 | **14** | **10** | **USD3.432** | **USD0.013762650** |

总occupied上界 **USD3.445762650**，原cap **USD50**。
unknown不是实付；settled金额按实际usage、公布单价及10%保守uplift计算，也不是含税费的最终发票。
本轮preflight与所有batch调用累计同一帽，无新50、无释放/改写旧unknown。
旧一次transport尝试是否到达provider仍未知，因此14是本地dispatch尝试数，不保证14次provider推理。

| 研究指标 | 当前可报告范围 |
|---|---|
| 真实完成/配对 | 0/48完整episode，0/12完整四臂block；A部分轨迹1，其余未执行 |
| 内容pass / T / 官方R | **unknown/未评分**，没有调用scorer给incomplete硬判0 |
| 用户交付 / bridge submit | 此部分轨迹均未达成；不作为完整episode成功率样本 |
| 联系成本 / 权限 | 观察到联系0、加权成本0、无grant；不泛化为跨臂安全结论 |
| 配对/组织不确定性 | 没有完整配对，不能计算；六题本就已曝光，不是独立终测 |
| 特权参考headroom | B/C/D均未运行，**未测得**；不由scripted perfect或A片段推论 |

## 下一步的最小方向，不在本轮实施

实际阻塞仍是**普通执行输出/推进协议可靠性**，还不是可以证明joint训练优劣的实验。
最小后续应先在训练/开发任务上隔离：
单动作输出契约的provider可实现形式，以及写后读结果到post/submit的进度控制；
匹配四臂共同接口、保留严格拒绝、公开输入和完整历史，不用gold暗示下一步、不偷偷强制post或代写答案。
如果改变为单次原生工具调用等候选，必须显式新协议、先mock验收再独立批准真实小样本，
不能把本次失败自动变成再次API授权。

待接口gate稳定并取得完整开发配对后，才按实测headroom决定是否准备when/whom/what监督、
train-only拟合sanity或任务收益优化；目前没有依据选择新超参、宣称oracle提升、
扩大采集或启动SFT/RL。当前阶段无需GPU，也未连接Colab。
本轮停止全部付费；没有第二probe、GET、重放或换ID绕unknown。
