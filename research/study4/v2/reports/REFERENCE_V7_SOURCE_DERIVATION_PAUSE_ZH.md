# Phase0：v6安全暂停与v7原规格完成合同核对

## 结论与当前边界

**确认是完成合同实现残留，已作最小零API修复；不是再次把NPC矛盾当停批条件。**
v6真实完成42例（26原A/C＋16新B/D）、8个四臂块，300新增calls全部settled；
0新增unknown、0inflight。末次ledger-allocation B的question已付且有完整结果，
只是协调者安排的append guard在settle后阻止journal追加；尚未send/NPC/执行工具。
`PermissionError`是这次操作性暂停，不是provider错误或计费未知。

暂停来自**Agent协调者**`call_1I0aGDbGI6AKSBWCsDLwXBKX`。
用户revision13「同意你的决策，请你按照这个来继续」仍覆盖原60×4×1及累计50；
不把Agent审查暂停写成用户新限制，也不要求每个内部修复重新购买/授权。
当前仍待协调者核对并解除自身暂停；**本修订没有发POST/GET/probe、读key或启动训练。**

实际执行源码为`babb69092b8d745410595948c9f40203413217f0`，不是下述v7源码。
[实际暂停/费用/指纹](REFERENCE_V6_PAUSED_ACTUAL_20261112.json)、
[42例公开轨迹与原始成绩](REFERENCE_V6_PAUSED_ACTUAL_20261112.public.jsonl.gz)均单独保存；
原run、分数、源规格、已付前缀及全部ledger不改。

## 95节点：直取、公开可推导、附属信息分开

逐一核对60题95节点的`release_rule`、公开政策、输出和下游`required_context`，
完整原文、字段角色和来源指纹见[95节点与整批路径审计](REFERENCE_V7_SOURCE_PATH_AUDIT_20261112.json)。
171个字段角色为：121直取事实、30实际签发记录、6直取或公开可推导、
11适用性/解释性元数据、3完整报价或单位输入替代。没有按实际成绩决定规则。

model-release H1原文：
> Provide the current evaluation report ID and note that it includes external benchmark claims.

公开`release-tiers.md`原文：
> A checkpoint is public tier when its current evaluation report includes external benchmark claims.

实际D第一条回复已明确给出EV-19和external benchmark claims，
同时说不知道tier/attestation等其他项。H1已经充分：public来自公开规则，
不要求NPC再逐字说public；不知道attestation不否认已给出的两个H1事实。
**H2仍须对EV-19实际attest；H3仍须真实attestation＋public上下文及实际mandate签发。**

本次确定的同根核对结果：

| 类别 | 完成依据 |
|---|---|
| release tier | 实际当前eval ID＋external claims＋上述公开规则 |
| stream monthly cost | 实际new-node count×公开每node月价；cluster仍须实际取得 |
| renewal total | 实际annual quote×实际term years |
| cloud annual quote | 实际count、1-year commitment、discount＋公开月价；原完整报价替代保留 |
| batch monthly price | 实际discount＋公开baseline月价；实际window仍须取得 |
| brochure total | 实际framework rate×公开words×languages；原完整报价替代保留 |
| browser/event附属信息 | 当前browser事实不必复述淘汰名称理由；event purpose/services只在公开packet已明确相同scope时不作额外私有事实 |
| 签发角色 | 原文Sign off/Verify only/Run margin check要求的root_cause_code、hr_verification_id、margin_check_id进入既有条件/撤回机制，不当普通编号事实 |

其他必要约束（如培训eligibility/outcomes）没有推测或放宽。
qualifier若被输出或下游授权context使用仍必需，不因归类为metadata而删除。
公开推导仅在实际合格回复取得全部前提后成立，证明保存公开文本/hash及每个前提的message ID；
缺规则、缺eval ID、提前/条件授权均不能补成完成。**任何签发不得由公开推导产生。**
固定真值下的已取得正确事实保留规则不变；真实撤回仍有效。

改动限于私有`reference_completion.py`、直接回归和有界审计脚本。
无题号/具体答案分支，没有改public what、模型/NPC输入、普通工具、64步或scorer。
计算结果与证明不注入executor，不替它计算/修改草稿；也不把计算冒充NPC确认。

## 整批路径证明：不是保留通过者、重抽失败者

原26A/C作为一个整组再次通过共享源码AST、资产/scorer和153个实际请求核验：
[v7全组证明](REFERENCE_V7_AC26_AUDIT_20261112.json)。
另外逐个重建全部16个v6 B/D完整episode的每次控制前缀，
先复现冻结v6的实际决策，再比较v7；公开请求/工具/终止合同未变。
**15条B/D路径完全相同，1条在首次控制差异处原轨迹分支，不重抽此前随机回复。**
例如错误提交5%/400的service-credit B也整条保留，不因低分剔除。

240个slot的逐项建议清单已在95节点审计JSON中固化：

| 处理 | 数量 |
|---|---:|
| 原26A/C整组 | 26 |
| 新B/D全路径不变 | 15 |
| model-release D原前缀分支 | 1 |
| ledger-allocation B已付proposal接续 | 1 |
| 尚未开始的fresh | 197 |

因此**41个完整路径候选＋199个待完成slot**，不是声称已执行41个v7 episode。
这是覆盖全批的保留/分支政策，不是旧43等价候选那种“留等价者、重抽其余者”。
所有原错误尾部仍保留为诊断并全额占帽；不挑成绩、不删任务。

model-release D：最早差异在history index4、question index1之前。
保留第一轮**3个已settled calls**及已实际执行的ordinary0；
从持久第二question请求恢复完整public state和native receipts，canonical hash完全相同。
三组原请求/结果逐一匹配settled ledger双指纹；messages/seen、完整同人NPC对话、
D的当时source cache、event cursor与question/NPC/ordinary下标1/1/1也已离线恢复核对。
只保存NPC对话指纹，不发布其私有system prompt。
旧下一目标Wang，修后Liu；只改变私有路由选择。
public state指纹`513ca4616b6baa07a12c7bf0b56a5b98fc1af83cf12b25ceaf561783d0de4b76`，
native history指纹`82528ddfa004613e469413b7d63077c392383bb1e7728a3a7886d87204210e18`。
不重发前三call、不重执行ordinary0，不把此前错误多问带进修后有效路径。

ledger B：已settled question结果指纹
`4f219046a3465a0ad187874c40d11df798f6227f190fdb41d7236dc53b73ff41`；
新路由仍认可其person，原消息从未应用。恢复时须直接应用该结果**一次**，
再NPC0及ordinary0，不能重新POST question0。
上述是离线续接证明；**新的执行namespace/ledger继承/最终源码准入仍须在审查解除后冻结并验证，
现有v6 runner不能直接当v7恢复入口。**

## 费用、验收与下一步

累计1340calls＝1334settled＋6unknown；settled上界12.0257659500，
旧unknown预留5.148不释放。占原50帽**17.1737659500**，余**32.8262340500**。
本轮v6的300calls＝93question＋92NPC＋115ordinary，费用上界1.4904326250。
held不是已确认实付，usage上界也不是最终发票。

剩A47/B52/C47/D53：按原13个A/C各自均价与全部8个新B/8个新D均价加权，
估计**11.351872403美元**；两倍情景**22.703744805美元**。
B均价含旧18call前缀一次，D含本次已证明有偏差的完整尾部，没有去掉昂贵例；
也未扣已付branch3/pending1，因此这两处保守重复估计。
这不是v7实测或完成保证：剩题分布、NPC拒绝/长尾和新路由可改变成本；
64步最坏情况不能保证入帽，逐call .858预留/原50硬帽/新unknown停批继续有效。
不降步数、截历史或改重复数来“保证”完成。

本地50项相关测试通过：
```
python -m unittest research.study4.v2.test_reference_completion research.study4.v2.test_phase0 research.study4.v2.test_phase0_recovery research.study4.v2.test_transport_diagnosis research.study4.v2.test_response_diagnosis -q
```
包含实际首回复而非全hiddenfacts的tier反例、无规则/无前提、5种公开算术、
scope/metadata、条件/撤回/重新授权和既有冲突回归。
三种新增签发角色的条件grant已对冻结v6源码复现错误释放、对v7确认不释放；
同一table还覆盖Once、revoked、not authorized、重新授权与否定撤回。
95节点审计、42条完整路径、待应用已付结果及26A/C全组另作实际证据核验。

**下一步只等协调者核对解除其本次暂停**，再做必要的独立namespace/前缀及累计账准入绑定，
继续同240任务而非另开实验。用户rev13范围不变；不把本报告当新批准或解除unknown门。
尚无完整、统一忠实实现的Phase0终结论；不以当前42例、非盲复核或可用case过.10门。
H1–H5不因工程修复判成立，H5跨执行器仍未测；不启动训练。
