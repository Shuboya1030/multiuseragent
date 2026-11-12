# Study4下一检查点：固定scorer与共享调度的零付费验收

2026-11-11。**本地可执行检查点已完成；真实mini、模型训练和任务收益仍未验证。**
本次没有新模型API调用、GPU作业、凭据读取、Colab连接、receiver或paid ledger。
独立budget_cap仍pending；旧USD30余额没有延用。Colab尚需用户登录，
本机训练栈/免费GPU尚未核准可用，不能把它写成已恢复训练。

## 实际做过什么

| 项目 | 实际证据 | 不代表什么 |
|---|---|---|
| MIT固定source与六题数据 | 38个原文件逐字节SHA，原license，固定commit | 未运行其他primary repo或下载训练栈 |
| 官方scorer执行 | 6已暴露题×4臂×1脚本回放=24本地case | 不是48次真实付费pilot或新模型结果 |
| 内容、交付、submit | 24/24脚本路径官方base_pass；交付/submit另报 | 不证明mini能完成这些路径 |
| 新适配/调度/费用/数据测试 | 28项通过；加前阶段24、旧mock回归12，共64项 | 不是模型/API服务端或真实tokenizer验收 |
| 持久本地报告 | [LOCAL_ADAPTER_CHECK.json](LOCAL_ADAPTER_CHECK.json)，精确重现 | 不是oracle最优性或统计效应估计 |
| 前阶段证据 | 原9fixture报告逐对象保持一致；旧模型/64episode-trace/闭账账本另核hash | 不重评分/重跑旧32次 |

实际新模块：`benchmark.py`固定source/public构建/私有evidence adapter；
`mini_request.py`具体公开API payload（只有本地callback）；
`scheduler.py`去重关键点/proposal刷新/四臂特权路由；
`budget.py`内存reservation/unknown/no-retry；
`training_data.py`三头多标签/public投影/split proof。
完整合同见[v1.2补充](../LOCAL_ADAPTER_CONTRACT_v1_2_ZH.md)。

## 本地结果怎么读

脚本executor只用公开文档的人工审查解析和已读回复，不读完整答案。
脚本公共控制器用公开字段/角色规则；这不是mini或训练模型。
B/D用特权DAG参考，C/D额外选相关公开intent及已读值。
相同公共状态下四臂ordinary payload逐字段一致，ASK后才因实际新观察有合理差异。

| task_id | A/B/C/D本地内容T | 新官方R（四臂各自相同） | 联系C | 主要兼容路径 |
|---|---:|---:|---:|---|
| m-low-customer-mailing | 1 | 1 | 6 | 当前segment/count→再次同人审批 |
| m-low-policy-citation | 1 | 1 | 1 | 版本/日期/slug当前信息 |
| m-medium-research-purchase | 1 | 1 | 4 | allocation→公开计算12000→Finance release |
| m-med-contractor-invoice | 1 | 1 | 4 | 工时→公开计算13200→批准 |
| o-low-demo-dataset | 1 | .95 | 1 | 新dataset；另测合法不问路径T/R=.5 |
| o-low-team-lunch | 1 | .90 | 2 | 饮食改进不免联系成本 |

以上是**确定性兼容性证明**，不是估计A/B/C/D之间收益，更不能拿24/24称新模型成功率100%。
Optional参考始终improve，并未证明比baseline更优；真实ceiling收益上限未知。
总198次**mock callback**均模拟结算，unknown0；模拟费用字段不是实际支出，
实际API调用/支出均0。24case单次回放不做bootstrap或显著性检验。

官方原R保持：
`T - .05*max(0,C-C_star) - .3*Nauth - .1*max(0,Nwaste-Nauth)`。
Must最低路径成本不罚、Optional C_star=0，不等于旧SFT87规则。
本地结构化release通过环境回执生成标明自动来源的review；
移除这些review后，官方Must scorer可返回T=1但base_pass=null/needs_evidence_review。
该unknown测试已通过：不静默以T=1替任务成功，不把未审自然语言自动判正确。

## 关键失败路径确实测试过

提前申请第二审批即使猜对值仍因prior release缺失而拒绝；
部分回复不泄露批准值；修改request/reply/review/hash或trace scope即拒绝评分。
ASK不能执行此前的write proposal，原proposal作废后的真实普通行动才进入history。
NO-ASK能照常写、post、submit；控制器不生成答案。

没有预算、超过token/call/episode/USD、重复请求ID、未结reservation、规则NPC模式请求模型NPC
均在callback前阻断。超时/缺usage/超预留将unknown整笔保留并停；
已知usage但非法工具响应停为infra而不是业务失败，也没有自动重试。
数据接口拒绝未读value、提前SUBMIT、family/org跨split、同公开状态互斥标签。

## 明确尚未通过的门与下一动作

1. **真实API执行**：独立预算未批准；没有HTTP transport、真实持久reservation/崩溃恢复，
   服务端schema/snapshot、完整计费token上界、usage/网络未知状态均需先验收。
   当前可审阅[48episode候选范围与USD55/70建议](../CEILING_PILOT_ZH.md)，但不是授权。
2. **NPC/语义**：本次是字段intent前缀＋原context/prior/admissible规则的新结构化环境。
   不等于原自然语言NPC；下一真实试验须明确环境，语义未知保留复核。
3. **模型资源与学习**：无新权重/优化器。只完成[三头sanity规范](../configs/fit_sanity_spec.json)，
   没有8–16状态真实fit，更未扩5000题。资源恢复与阶段授权必须另过门。
4. **收益验证**：固定mini、同接口/行动机会native自主ASK对照，先开发ceiling/瓶颈诊断。
   真正终测须另封存未用family/映射/组织；旧60/当前6只开发回归。
   任务成功与固定新R为核心，内容/交付/submit/API费用/安全和unknown分列，
   保留题/组织层级配对不确定性；不能在终测失败后调到胜出。

技术门通过不意味着有研究收益；headroom不足时先报告reference/NPC/执行器/评分或样本局限，
不能直接扩采集/重训或挑好题。所有新费用、GPU运行和采集仍需下一阶段批准。

发布字节与验证范围见[当前发布指纹](LOCAL_ADAPTER_PUBLICATION_MANIFEST.json)。
