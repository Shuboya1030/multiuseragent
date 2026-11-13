# Phase0真实进展、token-rate停点与v8零API修复

2026-11-13。**没有完成240例，训练门仍未判；没有启动训练。**
v7确实执行了新续接，不是停在准备：原41完整路径之外又完成26例，合计67例、16个四臂块。
随后新增一次token-rate型429，按原安全门停止；本报告之后没有POST/GET、重试或付费恢复。

## 1. 实际停止原因与精确账目

执行源码为冻结计划中的`98af649`提交，研究范围仍为60×4×1及原累计USD50。
新624 calls＝623 settled＋1 unknown；累计1964 calls＝1957 settled＋7 unknown，无inflight。
累计usage保守上界22.1899095000，加unknown预留6.006000，
**占帽28.1959095000，剩21.8040905000**。预留不是确认实付，也没有释放旧unknown。

本次失败是`conference-travel D / ordinary62`：
HTTP429、`error.type=tokens`、`error.code=rate_limit_exceeded`；
token limit=2,000,000、remaining=91,660、reset=57,250ms；
request limit=5,000、remaining=4,999、reset=12ms；Retry-After=2s。
request-id及全部白名单字段保存在[审计证据](REFERENCE_V8_CONTEXT_RATE_BOUNDARY_20261113.json)。
响应正文只保存安全字段，不保存密钥、完整headers/body；不能据此改写旧429为quota型。

**不是操作暂停制造的unknown。** unknown在05:06:27 UTC入账、05:06:31写终端receipt；
未来journal追加锁05:06:36才创建。没有终止inflight或阻止settlement。
此次已知rate类型并不表示可以释放预留、自动重试或保证节流后永不429。

## 2. 长请求与实际费用：不是只报429

该partial已有62个ordinary动作、63次ASK，188个已settled调用；
其已付usage上界7.6788500250，ordinary62尚未执行工具。
前三轮真实证据显示：Wang已给3人/9100/AI-TR-26；之后Chen反复不肯确认自己的acting-finance职责或签发引用。
这是保留在公开历史中的实际NPC拒绝/环境错误，不是portal短语缺陷，不能删掉、重抽或增加64步。

| ordinary索引 | 实际请求bytes | native历史items | settled input/output tokens |
|---|---:|---:|---:|
| 0 | 11,317 | 2 | 2,226 / 78 |
| 20 | 141,277 | 82 | 33,407 / 24 |
| 40 | 305,137 | 162 | 73,370 / 24 |
| 60 | 505,040 | 242 | 122,344 / 80 |
| 61 | 516,189 | 246 | 125,085 / 80 |
| 62 | 527,440 | 250 | unknown / unknown |

最后一分钟本run有31次settled调用，合计3,068,511 input＋2,702 output tokens。
最后七次settled分别为npc60、ordinary60、question61、npc61、ordinary61、question62、npc62，
input为78,756、122,344、122,518、80,778、125,085、125,259、82,827；
相邻创建时刻约隔1.34–2.45秒，完整时间与output见证据`last8_calls`。
这支持“长历史＋密集连续调用造成token吞吐压力”，不把本地60秒统计等同于服务端bucket算法或排除账户其他流量。
失败请求的精确token数未保存，不能拿其他事故的127651冒充本次实测。
当前公开state约6.4KB而native历史持续增加；没有为省钱截断历史、改what/输出上限或减少步骤。

## 3. v8最小修复：公开实体全称，不是放宽事实/授权

portal B首次真实提问是“API v3 documentation portal”，Priya已给DB-318及2026-11-17。
v7却把required_context“API v3 portal”作连续短语匹配，判h1未完成，随后仍找Priya。
这是已确认原合同实现偏差，不包装成NPC拒绝或gold上限的适用范围。

只修改私有`reference_completion.py`：
从当前**公开任务/文档实际出现的文本**提取有序、至多增加两个描述词的实体展开；
保留所有原实体词、版本和编号，不用私有答案生成别名或补请求。
否定/不确定措辞、同族冲突ID或版本不能通过；数值须实质相同，3.1不是3，9,100可表达9100但否定金额不算提供。
别名及公开文本/hash逐项留在95节点审计中。它是有界规则，不宣称理解任意自然语言。
缺少launch date仍不完成；只认真实回复，授权仍须实际前置/context/明确授予，不能从实体别名推导grant。
executor/NPC/public what、历史、工具、64步、scorer、模型和0.10门均未改。

45项相关回归通过，包括真实portal首问、安全泛化实体fixture、v2/v30式错误版本、
其他实体、否定、冲突提及、缺事实以及原条件授权/撤回/重新授权。
旧v7 admission现在拒绝用旧审计直接运行新reference源码，不能悄悄混协议。

## 4. 整批无择优保留与恢复边界

[全240清单、源hash、前缀及预算证书](REFERENCE_V8_CONTEXT_RATE_BOUNDARY_20261113.json)；
[原26A/C全组153请求复核](REFERENCE_V8_AC26_CERTIFIED_20261113.json)。
后者所含老预算是历史52例cohort审计的原字段，不是当前余额；当前账以本报告第1节为准。

全部67完整路径在v8规则下逐步核验，不看分数筛选：
**66完整路径可保留（含全部34例A/C）；只有portal B须在原随机前缀分支。**
其第一次充分回复后、第一次错误路由前已有3个settled calls和ordinary0的真实read_file。
完整publicstate/native history/messages/seen/NPC对话、空B source cache与1/1/1 indices均已还原，
请求/结果逐一绑定原ledger hash；下一人应为Liu，不重问Priya、不重放ordinary0。
旧错误尾部仅诊断但全额计预算，原文件/分数不改。

因此不是重跑174个episode：**66完整＋1原portal前缀分支＋1conference partial＋172未开始＝240**；
待完成目标174（A43/B44/C43/D44），现有v8一致的完整四臂块15个。
conference D的全部188个settled请求/结果、public/native/NPC对话/cache/工作区/revision均可无工具重放地还原，
其所有控制决策v7/v8一致。唯一无法自动跨越的是**ordinary62的新unknown**；
必须保留unknown、明确授权一个新尝试，而不是把它透明重发或把partial当0。
这些是零API恢复证明，不是v8已经实际运行或新的执行admission。

## 5. 已有研究信息：诊断，不是Phase0门结论

67例全部完成content/request-hash绑定的显式非盲AI复核，待复核队列0；
不是独立人工裁决器、可扩展准确自动奖励或未曝光终测。
[原始公开实际记录](REFERENCE_V7_STOP_ACTUAL_20261113.public.jsonl.gz)、
[元数据](REFERENCE_V7_STOP_ACTUAL_20261113.json)及
[非盲复核overlay](REFERENCE_V7_STOP_REVIEWS_20261113.json)保留原始分数，另列复核结果。

下面是**旧v7、不均衡可用样本描述**，含已知portal B偏差，不能冒充修后主结果：

| 臂 | n | 平均T | 平均R | excessC | Nauth | Nwaste |
|---|---:|---:|---:|---:|---:|---:|
| A | 17 | .4294 | .3735 | .4118 | .1176 | .1176 |
| B | 17 | .6206 | .1441 | 7.5294 | 0 | 1 |
| C | 17 | .4647 | .4206 | .5294 | .0588 | .0588 |
| D | 16 | .5875 | .2375 | 7.0000 | 0 | 0 |

Must/Optional、内容/交付/submit、ASK/首联/拒绝/补救及配对CI均在证据`v7_analysis.aggregates`中。
Must平均R：A .3944、B .1833、C .5500、D .3438；
Optional：A .3500、B .1000、C .2750、D .1313。
可用配对B−A＝−.2294（17题，CI[−.6176,.1324]），D−A＝−.1469（16题，CI[−.4688,.1250]）。
没有把unknown填0，没有complete-case过门，正式0.10门仍为`null`而不是失败。

| 假设 | 当前可判边界 |
|---|---|
| H1 Must收益来自更愿意问 | 整体无法判断；实际A在9道Must中8道问过，不能预设mini“不愿问”；2×2也不能单独识别when/whom因果 |
| H2 C−A很小 | 整体无法判断；局部+.0471，17题CI[−.1353,.2324]，不足证实小效应 |
| H3 D−B为正 | 整体无法判断；局部+.1406，16题CI[−.2969,.6469]，且含已知B偏差 |
| H4 Optional B−A不正 | 局部方向一致（−.25，8题CI[−.6563,.15]），整体仍无法判断 |
| H5 换GPT5.4差距更小 | 无法判断，未做跨模型对照，不扩scope |

因此不能启动SFT/RL或宣称joint已胜出/训练必然复制gold辅助收益。
若完整修后门通过，再依据H诊断决定when为主、whom评分SFT与公开what；不默认三头齐训。
原60已曝光、单repeat、非盲复核、分阶段修复与前缀续接均须随最终研究结论披露。

## 6. 剩余预算与一次清楚的恢复选择

不能再保证原50一定完成。v7新完成样本实际均费：A .10973（4例）、B .03818（9例）、
C .02352（4例）、D .17874（9例）。
按174目标分臂外推约**15.2743**，看似落在剩21.8041内；
但它排除了尚未终局、已耗7.67885的长尾，存在停止删失偏差。
将此partial已发生的成本并入D的10例发生均值，外推43个未开始D，
其余臂按原均值，则还需约**47.3461＋当前partial后续**；
这不是重复支付已花partial，而是未来长尾频率敏感性，已超过剩余约25.5420。
完整样本均费双倍情景30.5487也不够。样本少、修复后成本未实测，三者都不是保证或新预算批准。
没有删掉长尾、降低64步/门或通过换模型凑成本。

**预节流候选，尚未接入实际runner：**若恢复获批，首次等待至少60s（覆盖已知57.25s reset/2s Retry-After），
未来逻辑请求间隔至少20s；以原模型400k总上下文上界保守计，闭60秒窗口最多4次、自己至多1.6M tokens。
本地假时钟＋429 fixture验证：只“发送”1次，429后即使推进时钟或给普通继续标志也不自动重试。
fixture与“未接入runtime”标记已入证据；共享账户其他流量、限额变化、无本地精确tokenizer均限制保证，不能承诺不再429。
该方案不改prompt、history、输出上限、模型、64步或评分；不能把节流和重试unknown混为一件事。

**需要协调者向用户一次性确认的恢复选择：**
维持原USD50，明确授权对ordinary62建立一次新attempt、保留全部unknown并接入预节流，
在新namespace绑定66＋174/最终源码/原rev13及该恢复来源，接受可能预算用尽仍未完成；
或者继续停付费，若必须争取完成240，再明确选择新的总帽。
尾部发生均值情景对应总占约75.5420＋partial后续，80也只是候选上限而非完成保证，未经批准不能采用。
不需要为这个内部语义bug再索用户批准；**真正新增的恢复决定是新unknown尝试与预算风险**。
本报告不包含付费恢复授权，旧run也不能直接restart。
