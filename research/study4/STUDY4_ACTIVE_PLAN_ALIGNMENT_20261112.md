# Study4有效下一计划：对齐Phase 0、假设与条件训练

2026-11-12。**本文件是现在的执行入口，不是训练启动或新付费授权。**
依据用户的[新文档](PHASE0_ARMS_HYPOTHESES_TRAINING_20261112.md)
（提交`9dc95bc165827043dd2ffa969dfb12fb1ff24b16`，blob
`f1061e1bffc4a8ad54d6d08eae0aab042e911ada`）。
不改作者原文、历史计划、模型、结果或账本；以下明确列出兼容修订。

**最新零API核验：[reference-v5签发字段补齐与26＋214恢复边界](v2/reports/REFERENCE_V5_ISSUED_FIELDS_ZH.md)。**
用户要求在inflight settle后暂停；本轮643call全settled、0新unknown/0inflight，
完整52/240（13块），累计占原50帽15.629236425，余34.370763575，旧6unknown5.148不动。
已确认all-hiddenfacts单条字面匹配不是预定gold when/whom；不能把这52当Phase0门答案。
私有reference-v5在v4基础上补齐readiness/release/publication_reference签发角色，
沿用条件授权与撤回机制；60题/95节点源合同不变，40项相关离线回归通过。
原13题全部A/C共26例整体通过共享合同及153请求核验，
只整体保留这组，B/D全部fresh，需214个slots（A47/B60/C47/D60），partial52不续接。
原43等价候选/197fresh建议已被明确替代：按B/D随机回复等价筛选仍有选择偏差；
旧52事实、43候选审计及原报告原样保留，不再筛选B/D，不是修后新执行结果。
付费恢复入口硬禁用，等待协调者核验新版本/清单/批准边界；不启动POST/GET/probe/训练。
解禁仍必须有新的直接用户授权，并在首个正式请求前绑定、重冻和核验新准入计划；
本轮coordinator修复指令不构成付费批准。
下列scope与旧停止记录按时间保留，不把先前“继续”解释为本次修后付费批准。

**当前执行修订（2026-11-12，用户来源`dccf1924-a562-4335-bbca-c6f929b24f2e` revision8）：**
协调者转达用户已缩减为**60题×4臂×1次，共240episodes**，并直接回复“继续吧”。
修后统一协议2从头运行240；旧25次仅诊断，不补215混协议，也不继续旧720清单。
沿用固定mini、同一LLM NPC、普通工具和64步等限制；不新增独立probe，首个四臂配对块兼作真实验收。
60题等权、must/optional分列，B−A或D−A平均R≥.10门不变，CI不附加门；
单repeat不证明重复稳定性，H5跨模型未测。此修订不改作者方法原文或旧证据。

**该新240 run实际首请求即HTTP429，0/240完成、0工具；已停，未发第二call。**
[最新实际停止与安全诊断修订](v2/reports/PHASE0_240_ACTUAL_STOP_ZH.md)：
请求仅14756bytes，不能将429归因长历史；累计379calls/373settled/6unknown，
占原50帽9.110225025，余40.889774975，unknown5.148不释放。训练门仍unknown。
后续仅补HTTP错误code/type和受限rate元数据留存，不发付费验证，恢复需要新的有界授权。

**更新恢复授权（来源`1babf0c9-1a8f-4242-8816-e8872fda2c22` revision10）：**
用户“我已经续费你继续吧”。保留上述240范围、同mini/NPC/研究协议及原累计USD50，
用已补安全错误字段诊断的新冻结源开始新批次，首个正式四臂块兼作验收，不独立probe。
显式关联上次首slot unknown尝试，保留其缺失状态，不透明重放；继承379calls/373settled/6unknown，
settled上界3.962225025＋unknown5.148，占9.110225025，剩40.889774975。
用户报告续费不是已证实此前429为quota，也不是额外实验预算；新unknown仍停批。
0训练/GPU/额外模型对照。旧25仅诊断，不混入统一新批240。

累计承接378calls/373settled/5unknown，settled上界USD3.962225025＋unknown预留4.29，
占原50帽8.252225025，余41.747774975。新scope不是新增预算；新unknown即停，无retry/GET。
协议2保留修后的单份公开事件/消息来源以及same-byte write规则。
公开what只引用已读同事原文的值/来源及原请求上下文，不凭草稿断言事实、自动推算或伪造NPC确认；
执行器仍可自行基于公开文档计算并在实际问题里说明来源。未自动构造计算值是当前公开规则的能力限制，
不是将私有要求漏传的实现bug；不针对7800或某题补丁。历史NPC公开解释/过拒等局限继续报告。
基于旧24完成episode均值，240约USD12.31；每26包含一个旧截尾partial量级的情景约36.07，
均非修后实测或完成保证。不训练/RL/GPU/额外模型对照。

**历史实际状态（同日21:58 UTC）：** 用户此前授权正式720 scope，但实际完成25/720后遇NPC HTTP429停机。
[实际六块、H1–H5限制、费用和协议2修复](v2/reports/PHASE0_ACTUAL_STOP_AND_REPAIR_ZH.md)是最新入口；
mean R训练门仍未判，旧C/D重附历史与相同write失效已证明并零API修复。
新版按上述新来源绑定累计费用后启动，旧run不可重放；实际终态以新run receipt为准。
下文保留最初纠偏时的诊断和条件训练路线，不把旧smoke冒充正式结果。

## 先给结论：确实没有对齐

我把接口失败、持久化和控制职责修复逐渐当成了研究主线，
又把缩小且改变NPC/what定义的工程实验作为“ceiling”推进。
这些工程问题真实存在，但解决它们不是回答H1–H5，也不该不断替代正式Phase 0。
此前还把用户的平均R差值门改成待签统计门，并默认保留三头方向；
这两处也应纠正。时间花在工程排障上，**没有完成用户定义的Phase 0或新训练**。

已经能说的只有：

- **旧SFT87没有体现收益**：16 dev题内容pass仍5/16，完整交付4/16→0/16，
  控制决策124/124为NO_ASK；不建议继续修补它，不能用多数类准确率当能力证明。
- **新工程smoke只有一个题的A/B完成**：Optional lunch中A的T/R=.5/.5，
  特权B为1/.9，联系成本0→2。这是局部反例线索，不是平均收益或训练门通过。
- **控制职责缺陷已证明并修复**：C的7次controller SUBMIT阻断write。
  新版仅SELF/ASK；缺文件读取恢复未改。接口验收不等于研究效果。

证据：[旧SFT87结果](results/TEACHER87_NATIVE_MINI_DEV16_RESULTS_ZH.md)、
[历史smoke实际结果](v2/reports/NATIVE_FUNCTION_ACTUAL_ZH.md)、
[二态修复](v2/reports/HELP_ONLY_REPAIR_ZH.md)。

## 对齐表：要求、差异、修正与验收

本表“验收”是正式运行前要满足的条件，**不表示已经完成适配**。

| 新文档要求 | 当前实质差异 | 有效修正 | 验收 |
|---|---|---|---|
| Phase 0：60题×4臂×3，同一mini、同一LLM NPC | 6题×4×2 scoped规则NPC；实际只完成2 episode | 旧48计划仅历史engineering smoke，不作为正式Phase 0或训练门 | 冻结完整60题/四臂/3重复、执行器与NPC snapshot/prompt、调用/机会预算 |
| C/D what规则只读公开历史 | 当前`BenchmarkReference.what`用gold DAG/required_context选相关已获值 | 正式C/D不得复用该选择器；规则仅处理公开任务/请求、已读回复和值来源 | 保持公开输入不变、改变gold/required_context时，what选择与附加值不变；无未读值 |
| gold只用于B/D when/whom | 当前C也有what特权，且人工intent grammar限定请求 | C不再是privileged辅助；不以私有节点选intent，不把人工前缀/key=value grammar当论文协议 | 私有读取点限定在B/D求助路由；公开规则保留实际来源、拒绝及冲突，不伪造grant |
| A为原生mini自主when/whom/what | 当前A先ordinary proposal，再独立control决策调用 | 当前A只能叫模块化prompt基线，不能直接等同论文native | 冻结A自主ASK/普通行动接口及与论文差异；四臂普通能力、公开信息、机会预算一致，不默认添第五臂 |
| B−A或D−A平均R≥.10进入训练 | 旧pilot把.10改成待签门 | 恢复用户定义的点估计门，CI报告但不额外要求Phase 0 CI排除0 | 运行前冻结统计/缺失口径；must/optional分列，不挑题/重复 |
| Phase 0结果决定H1–H5与训练 | 默认三头接口/工程小sanity容易变成训练主线 | 先H表，再条件化when核心、whom SFT、公开what规则 | 不把8–16状态替代200状态，不把接口通过当假设成立 |
| 新组织终测与既有60基准 | 60题已有训练、选择、诊断暴露 | 新组织封存终测与60题benchmark回归分开 | 组织/家族/知识权限映射、去重与seed先冻结；终测不参与选择 |

现有单工具、public-only、ASK自动收读、持久预算保护可复用，
**不重写框架，不继续缺文件协议工程，也不先把旧48跑完作为新的研究必经门**。

## 正式Phase 0与决策口径

四臂保持新文档定义：A=mini自主求助＋自己写请求；B=gold when/whom＋mini写请求；
C=mini自主求助＋公开历史规则补全；D=gold when/whom＋同一公开规则补全。
执行器沿用`gpt-5.4-mini-2026-03-17`；同一LLM NPC及普通工具、信息条件固定，
NPC的模型/snapshot/prompt/费用仍须单列冻结；B/D不得代写最终答案。
“oracle”指固定DAG特权参考，未证明全局最优；D是该设置的经验参考，不是理论最优保证。

**范围为720 episodes，不是720 calls。** 60题均为已曝光benchmark。
冻结`tribalbench-1.0`实际源码绑定（现有
`4260bdc626548f59042f318cdf0566490e91b9d5`），报告R、T、C/C_star/excess C、
N_auth、N_waste，并另列内容成功、用户交付、桥接submit、ASK/拒绝/补救及API成本。
旧SFT87的旧R不与新R混算；自然语言证据未决仍为unknown，不自动按业务0或成功处理。

运行前冻结：每题先对3重复求均值，再对60题等权，四臂按同题/同重复配对；
同时分别报must/optional。主要训练门是
**mean(R_B−R_A)≥.10 或 mean(R_D−R_A)≥.10**。
报告任务配对不确定性；真正组织泛化用组织级/层级bootstrap。
不追加“所有H成立”“Phase 0 CI下界≥.10”等更严门。
未完成/unknown须报告覆盖与缺失，不能填0或只挑完整高分子集宣称通过。
门未过则停止训练并诊断，但低差值可能涉及参考、what、NPC、接口或评分，
**不能自动断言唯一根因就是执行器**，也不能降低门槛或测试到胜出。

## H1–H5：目前逐项判定

| 假设 | 当前判定 | 现有证据与限制／正式需要什么 |
|---|---|---|
| H1：must的B−A大，主要来自when而非whom | **无法判断** | 无新正式must配对。旧SFT不问不等于此假设成立；2×2同时替换when/whom，不能单独识别其因果贡献。正式需R差及ASK率、首次正确联系、拒绝/补救诊断 |
| H2：C−A小 | **无法判断** | C未完成且没有ASK，what规则未触发；现C还不是公开what规则。需正式A/C配对 |
| H3：D−B>0 | **无法判断** | D未运行，无B/D配对；需同一公开what规则及LLM NPC下的差值、缺值拒绝/修复记录 |
| H4：optional的B−A约0或负 | **无法判断** | 单题B−A=+.4是局部反例线索，不能判定optional总体均值，也不能据此调整成本权重 |
| H5：门会过且换GPT-5.4后B−A更小 | **无法判断** | mini-only四臂不能验证跨执行器差异，也不能预言门会过。匹配GPT-5.4对照是额外范围/费用，待单独审批，不自动加入720 |

论文统计是提出假设的依据，不是本研究实测。H表用于解释与选择后续训练，
**不是强迫所有H都证实才允许通过已定义训练门**。

## 通过门后的条件训练路线（尚未开始）

1. **先根据H表选方案。** 若H1/H2/H3支持：when为核心、样本/loss权重最大；
   whom用公开职责候选共享打分SFT，选稳定候选ID，不靠生成姓名token分类；
   what先用公开规则，不默认三头齐训或whom单独RL。若结果不支持，明确报告哪项配置需调整，
   不预设联合一定赢，也不把“when＋固定规则whom”冒称学习型两阶段对照。
2. **生成/监督。** 按组织及模板/角色/知识权限映射预分train/dev/test，
   用oracle＋扰动/补救轨迹（错人、漏步骤、缺值、拒绝后补救）与类别权重。
   私有gold只做离线环境/标签；部署输入仍公开。保留SELF/ASK兼容修订，
   ordinary submit不作controller标签。先做**200个train-only状态过拟合sanity**，
   报ASK P/R/F1、whom top-1≥.85，不用总体多数类准确率替代；不另造未经批准的小样本门。
3. **条件RL。** 从上述SFT初始化，按用户方案准备GRPO group=8、KL β=.02、
   70% must/30% optional、终局官方R、无额外shaping；这是待执行方案。
   它需要新policy rollout，不能把无行为概率的异质R0/R1冒充有效offline RL数据。
   Dev-new-org相对SFT的R提升配对CI整体高于0且N_auth不增加，再按预定规则选择；
   这一dev训练门与Phase 0的.10点估计门不同。
4. **冻结后评测。** 封存新组织终测一次（预声明3重复），原60题另作benchmark回归。
   按新文档准备原生/prompt、when-only、when+whom、oracle对照；GPT-5.4另列待批范围。
   普通执行器/NPC及执行机会匹配，报告任务成功与质量—成本权衡，不只单reward。
   不用终测修模型；未过dev门不靠挑终测重复获得正结果。

## 两项透明兼容修订与费用边界

**SUBMIT：** 新文档仍写controller三态，但这与持久的“只决定求助、executor自然继续”
及实际C七次阻断write冲突。建议保留已修SELF/ASK，submit只由ordinary executor产生。
这是显式兼容修订，不擅改作者原文，也不是把历史C输出改成SELF。

**“步骤1–3零API／2–3天”：** 规则NPC和程序化标签可本地免费，
但固定mini executor rollout仍付费，RL group8也产生执行器调用。
只有已有可运行的完整本地执行器/模拟训练环境时才可能零API；当前未有此证据。
免费Colab GPU曾被选择，不代表当前GPU、模型/依赖或2–3天工期已核验。
LLM NPC episode或10%混入同样付费；不能沿用文档USD30–60估计当承诺。

**本轮只剩三类真正必要的下一事项，不启动它们的付费部分：**
公开what规则与来源边界；同LLM NPC和原生A的兼容范围；
正式60×4×3任务/统计/全部模型调用及独立预算确认。
费用表须分executor、control/question、NPC、预验，列snapshot/tier/价格来源、
turn/call/token上界与估算假设；没有这些绑定就没有可靠的720总价。
不因规则NPC免费而漏计executor，不把720当call数。

既有授权只有原六题规则NPC48范围、原USD50；
旧unknown USD3.432和settled上界USD.069303300保持原账。
本次计划对齐**不是720、LLM NPC、新采集、训练、GPU或预验的授权**，
不取key、不建新paid ledger、不发请求。当前停在计划纠偏，不再循环扩展工程准备。
