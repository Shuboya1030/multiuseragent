# v1.2补充合同：真实题包适配不等于真实模型ceiling

2026-11-11。[v1.1](DESIGN_v1_1_ZH.md)的public-only、共享普通工具、交付与submit分列、
历史证据保全、数据和费用边界不变。本文更新其中“尚未接入”的本地工程状态，
不覆盖旧SFT87/旧32episode/旧R，也不授权新模型调用。

## 固定来源与证据边界

按MIT许可证保留[原许可证](vendor/tribalbench/LICENSE)、38个原始源码/数据文件和
[源指纹](vendor/tribalbench/SOURCE_MANIFEST.json)；commit仍为
`4260bdc626548f59042f318cdf0566490e91b9d5`。
源码人工审读后按SHA验证再由标准库加载，未安装依赖/clone或执行另一primary repo。
vendored文件禁用Git换行转换，不能为了hash匹配改写原源码。

官方`score_bundle`已实际在本地结构化规则环境执行。输入绑定包括原blueprint、实际artifact、
完整episode-scoped消息、实际消息ID/关联请求、时区时间戳、成本表与私有evidence review；
再计算统一输入指纹。export与runtime实际history不一致、消息内容/review hash过期、缺时间戳、
不完整/infra失败均显式拒绝，不转成空trace或业务0分。

**三类结果分开**：
- 官方内容/过程：保留原`base_pass/T/R/evaluation_status`，不改公式、不改分。
- 用户交付、桥接submit：来自公开progress，不能用任一项代替业务内容pass。
- infra或未知：infra不评分；官方自然语言evidence待审时保留unknown并排除确认性汇总。
  特别是Must-help可出现`T=1`但`base_pass=null`，并不矛盾，也不能拿T伪称任务成功。

规则NPC回执自动review的依据是本地确定性环境实际释放节点与原始request/reply哈希，
reviewer明确标`NOT-human-NL-review`。它不是人工裁决，更不能套用到任意自然语言回复。
无结构化回执时不自动创建accept，即便文本含正确数字。
原scorer的字段等价、evidence启发式等实现限制原样保留；未补写“更聪明”的同名grader。

## 六题适配范围与公开输入

只适配[既定六题](configs/ceiling_pilot.json)，不是全60/新终测或完整生成器。
公开instruction、文档目录与角色、字段和成本从`public/`文件构建；
成本按公开title的3/2/1规则算出后私下校验，不从gold候选人集合选人。
已得值来自实际回复；席位×公开年单价、工时×公开时薪有明确public calculation来源。

公开intent是`request <公开输出字段>`，不含私有DAG节点、类别、隐藏值或required_context。
私有blueprint只由参考策略、NPC与scorer持有。已读事实可进入后续公开状态；
任何future reply、gold目标或评分不能进入mini请求。

当前`BenchmarkNPC`是**新定义的scoped structured rule环境**：
由明确intent前缀选择请求字段，并检查原任务admissible、prior release及required_context。
未满足时返回泛化拒绝，不泄露缺失值。它不是原LLM NPC、不是自然语言语义匹配器；
正文否定/模糊请求、权限表达、原scenario自由回复的等价性未通过。
因此选择该规则环境本身也必须在真实pilot前明确，不得拿本地兼容检查替代NPC迁移验收。

## 统一mini wire与关键点调度

构建拟用Responses API的严格JSON payload，固定候选snapshot与reasoning none，
普通工具参数在wire中编码为JSON string后经同一parse_tool复核。
这是新wire表示，尚无服务端schema/模型可用性验收；没有HTTP/key/重试实现。
`LocalMini`当前仅注入脚本callback，不是已运行mini。

每个普通行动机会先生成一个proposal，再合并start、reply、交付物write/submit、
每4步原因，**最多一次**when/whom决策。没有触发点就允许SELF，不额外调用控制器。
SELF复用proposal；ASK作废该proposal、一次生成问题、自动收读回复后再生成普通动作。
所以每步最坏1control+1question+2ordinary，不能漏算被作废的第一次ordinary。
两次ordinary中只有最终实际工具执行计入24行动机会。
消息时间由事件observer在send/read时刻采集；本地证明明确使用合成时钟，不伪装实际API时钟。

四臂普通request、工具、progress、行动机会和mini候选完全相同。
A/C公共when-whom；B/D由私有DAG参考提供when-whom，不称理论最优。
C/D私有what辅助可以选**公开intent及已读value IDs**，不能传入节点/条件/未读值；
该辅助是特权，不作为部署baseline。若公开策略选错联系人且无ready私有节点，
记录`no_ready_node_public_fallback`，不偷偷换联系人替它纠错。
当前参考策略的Optional路径声明为improve，**未优化全局收益或选择baseline**。

## 调用与费用硬门

`LocalBudget`是内存mock，不是付费ledger；默认`usd_cap=None`，派发前阻断。
独立金额尚未批准，示例中数值55只用于本地模拟。它不读取旧USD30或任何其他Project账本。

逐请求唯一ID、全请求计数、输入/输出token、全局调用/episode/操作次数与Decimal费用reservation
在callback前检查。按保守普通价和10%候选附加费预留最大输出；只有usage完整、未超预留才结算。
超时、partial或usage缺失/超额保留整笔unknown exposure，并阻止后续调用，不能释放再试。
已有settled usage但工具JSON不合法则是已知费用的infra失败，也停，不谎称unknown美元或业务失败。
规则NPC模式不能派发LLM-NPC调用。

当前token counter只是假tokenizer，数值费用也是模拟，不是实际计费。
真实端仍需：服务端计费token的安全上界、隐藏开销/输出限制、价格/地区、实际usage、
持久reservation/崩溃恢复及单实例准入，才能声称真实费用硬帽已通过。
本次未开新paid ledger，也没有真实API transport去绕过未批准金额。

## 三头监督与训练前sanity

[接口](training_data.py)把公开input与私有acceptable tuple/mask/split metadata分开。
when为SELF/ASK/已完成交付后的SUBMIT；whom与what仅在ASK有loss。
多合法标签保持**相关的整tuple**，不能分别取when/whom/what并拼出不合法组合。
同公开状态无共同可接受tuple必须排除/复核，不能伪造唯一标签。
无behavior probabilities的这些参考/SFT行明确不是offline RL数据。

当前proof审计采用严格family与organization均不跨split的cross-group模式；
不能把它冒充已经冻结的50org或dev-in-org方案，后者需显式新split-regime合同。
尚无新生成器任务、真实模型头/LoRA更新或fit结果。
[8–16个train-only状态的sanity规范](configs/fit_sanity_spec.json)只定义下一门，
不为lr/rank或GPU预算背书，也不使用dev/test修到可拟合。

### 小生成器下一门的输入/输出设计（未实现扩展）

复用已有9个proof模板，仅在下一阶段批准后参数化：
输入为独立的family/organization/role-map seed与显式依赖结构，不使用当前六题成绩筛选seed。
产物分成public instruction/documents/roster/intent目录、private facts/DAG/release/参考、
独立scorer绑定和group/去重指纹四部分；public投影禁止携带生成器私有标签。
先审每一种依赖结构的可解路径、错误/拒绝路径与同公开状态多解/不可辨识，
再对train-only少数状态产出上述三头接口，不能按“名字换了”算新family/组织。
生成器局部proof和真实fixed-mini ceiling都过门、数量/资源另获批准前，不扩到5000题。
