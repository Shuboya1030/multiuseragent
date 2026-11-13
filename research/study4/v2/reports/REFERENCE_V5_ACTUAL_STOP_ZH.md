# Phase0真实恢复后停止：NPC值冲突，不是授权门或429

**已按原revision10授权和Agent审查解除真实恢复；首fresh B出现同scope事实冲突，
按现有安全合同在下一POST前停止。** 新发18个请求均正常settled，0新unknown，
没有重试/GET/probe。214fresh尚未完成，训练门仍unknown。

来源归属已纠正：之前的暂停是协调者审查，不是新的用户限制，
因此没有再要求用户重授同一预算。原用户source和Agent解除分别记录；
最终执行源码`2955cc08d938ee92c7f8b4f29f695e37930bd1c1`，
plan fingerprint `f055257f6f16ef807f50bb8b9d6b718456e06c7e6dc966bcedd06b61ee7ef43c`，
执行源整组核验 fingerprint `4c5f69d6fa76f7078b47a9b31520c2a181632783c4271f72fc6c5e42264fdd4c`。

## 1. 精确覆盖与账目

| 项目 | 实际值 |
|---|---:|
| 原A/C整组保留并完成公开回复复核 | 26（各13） |
| 新fresh完整episode | **0/214** |
| 修后完整四臂配对块 | **0** |
| 首fresh partial | m-med-service-credit，B，slot1 |
| 新调用 question / NPC / ordinary | 6 / 6 / 6 |
| 实际普通工具步 / 联系次数 / 联系成本单位 | 6 / 6 / 18 |
| 新settled / 新unknown / inflight | 18 / 0 / 0 |
| 实际input / output tokens | 59452 / 1020 |
| 新usage费用上界USD | **0.0540969000** |
| 全历史calls / settled / unknown | 1040 / 1034 / 6 |
| 累计settled上界USD | 10.5353333250 |
| 旧unknown继续预留USD | 5.148000 |
| 原50帽占用 / 剩余USD | **15.6833333250 / 34.3166666750** |

unknown预留不是确认实付，usage上界也不是最终账单。
没有释放旧unknown或新开预算，旧十个根目录/ledger字节核验通过。
全部26保留文件在首POST前已整组复制，不按结果保留或重抽B/D。

## 2. 实际冲突与停止位置

原规格h1要求Northwind信用比例**10%**；h2要求先取得h1，
且引用**10与800**才能授予`CR-APR-902`。
完整原node、release_rule、required_context及六条实际问答见
[机器证据](REFERENCE_V5_ACTUAL_STOP_20261112.json)，不发布private NPC system/journal。

| 联系序号（从0计） | 实际请求/回复要点 | 完成判定 |
|---|---|---|
| 0 | executor问reference；Mark明确给10%，因缺percent/amount暂不授予 | h1正确释放 |
| 1 | executor仍引用公开draft的5%与monthly fee8000；Mark要求具体credit amount | h1保持；h2不释放 |
| 2 | executor引用5%/400；Mark却给CR-APR-902 | h2前置context未满足，不把裸code当合法grant |
| 3 | executor再确认code，未补10/800；Mark确认code | 同上 |
| 4 | executor问5%/400是否正确；Mark确认5%/400和code | 未满足h2；不是新批准的合法替代条件 |
| 5 | executor列完整5%/400 draft；Mark明确逐字段确认`Credit percent: 5%` | 与已释放10%冲突，h1转unresolved |

逐回复重建的released集合确为：
`{h1}, {h1}, {h1}, {h1}, {h1}, {}`。
所以**不是又因缺少某个隐藏元数据而从未承认首个10%回复**；
它已承认，后续卡在h2真实缺失的10/800，
最后检测到另一个明确权威值5%而触发`ReferenceUncertain`。
停止发生在18次响应全部settle、6次ordinary动作完成后，
下一个控制决策尚未发送请求，没有第19次POST。

最终草稿为：

```json
{"customer":"Northwind","credit_percent":5,"credit_usd":400,"authorization_ref":"CR-APR-902"}
```

shape合法不代表内容正确：5/400与原10/800不符；未post、未submit、未交付。
该episode不完整，**T/R及终局Nauth/Nwaste保持unknown，而不是业务0**。
可以确认的是NPC在请求缺少原required_context时提前给code，
并在后续反向确认了与自己首答冲突的比例；不能用其code字符串假装合法授权已完成。
不能为了继续而删首答、挑末答、覆盖gold、放松context或自动再抽一次B。

## 3. 已保留26例的描述性结果

对既有绑定复核只补6条原公开问答的显式非盲AI裁决；
原文件/原raw分数不改写，新复核另存。26例证据均已resolved。
以下只是原13题的A/C，不是新的完整四臂Phase0：

| 范围 | 臂/例数 | T | 官方R | excess_C均值 | Nauth/Nwaste均值 |
|---|---|---:|---:|---:|---:|
| 全部13题 | A/13 | .4500 | .4038 | .4615 | .0769/.0769 |
| 全部13题 | C/13 | .4269 | .4115 | .3077 | 0/0 |
| Must | A/7 | .5500 | .4929 | .2857 | .1429/.1429 |
| Must | C/7 | .5786 | .5786 | 0 | 0/0 |
| Optional | A/6 | .3333 | .3000 | .6667 | 0/0 |
| Optional | C/6 | .2500 | .2167 | .6667 | 0/0 |

A/C均13/13交付及submit，但各仅1例full-information内容全匹配；
官方base pass为A5/13、C4/13，不能把交付、pass、T1混为一谈。
ASK episode率A8/13、C7/13；Must分别6/7、5/7。
首次联系正确率在实际ASK者中A7/8、C6/7；拒绝总数均4，repaired nodes均0。
因此论文中“mini几乎不问”的先验不能直接当作此环境已验证事实。

C−A的R差为**+.00769**，13题配对bootstrap95%区间
**[-.18462, +.18462]**；Must为+.08571，Optional为−.08333。
这些只描述已保留子集，不是60题结果，更不是跨组织或重复稳定性证据。
B/D没有修后完整例，B−A、D−B、D−A和0.10门都无法计算；不填0、不用旧B/D补洞。

## 4. H1–H5与当前研究答案

| 假设 | 判定 | 当前证据边界 |
|---|---|---|
| H1：Must B−A大，主要来自when | 无法判断 | 无修后B；A在本7题已问6题。2×2本来也不能单独因果识别when/whom |
| H2：C−A小 | 无法判断 | 13题描述性差接近0，但区间很宽且仅子集 |
| H3：D−B>0 | 无法判断 | B/D均无修后完整配对 |
| H4：Optional B−A≈0或负 | 无法判断 | 无修后B，不能以C−A替代 |
| H5：门通过且GPT5.4差值更小 | 无法判断 | 门未判，跨执行器对照未运行且不在本范围 |

**现在能确定的瓶颈线索**：即便whom固定正确，executor仍可能坚持错误draft、
不把已读10%放进下一请求；固定LLM NPC也会提前授权并回头附和错误值。
这是实际行为，不是已证明“只训练when/whom就能解决”的结论。
不启动SFT/RL/GPU，也不把ReferenceUncertain改成已完成/业务失败。

当前阻塞不是授权或余额，而是原冲突策略下**不能安全续接的真实partial**。
维持停机，交协调者核验该矛盾在原合同中的后续处理：
回问、局部任务失败或证据仲裁不能由本session为了得到完整集而临时挑选。
不据单例继续扩分类器、换NPC/prompt/步数或自动重跑；若后续采用新处理版本，
必须保留这18call/partial及全部预算，不冒充同一冻结协议已经完成。
