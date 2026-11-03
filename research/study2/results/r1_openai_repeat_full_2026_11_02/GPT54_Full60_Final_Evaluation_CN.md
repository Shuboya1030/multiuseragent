# GPT-5.4 R1 60题对照：最终离线评价与同期配对

## 当前状态与入口

**新mini30和full60共90个独立attempt均已结束、完整导出、逐条实际输出与联系证据已审阅并落盘评价。未审阅0、技术中止0、原冻结计分定义下的T/旧R数值缺口0。** 不是把执行完成当评价完成，也没有将raw的40个`needs_review`判成失败。

**另有1个明确的数据集效度争议：`o-high-eval-budget`的优化GPU小时gold欠定。** 该题可以按冻结参考复现评分，但不能据此认定Agent计算错误。下述50/60是保留该参考失败的主口径，不表示这个gold效度问题已获用户确认或已被修复。

| 入口 | 用途 |
|---|---|
| `derived_full_v1\GPT54_Full60_Comparison.csv` | 60行；full与历史mini original/last-authorized并列，Must另有同期repeat列 |
| `derived_full_v1\Same_V6_Must30_Pairs.csv` | 30行同期同v6 Must配对 |
| `derived_full_v1\adjudications.json` | 60条内容投影、逐字段判定、T/Q/旧R、实际逐联系成本与扣分依据、NPC/任务问题 |
| `derived_full_v1\summary.json` | 分层汇总与配对转移 |
| `derived_full_v1\All_90_Attempts.csv` / `.json` | mini30/full60唯一attempt索引及实际episode键 |
| `derived_full_v1\validation.json` / `source_verification.json` | 933个真实请求/结算、90个trace、参数/history/源hash检查 |
| `Mini_Must30_Repeat_Result_CN.md` | mini重复实验的独立结果，不被full覆盖 |

`full_direct_reviews_v1.json`及其validation是先前仅4条的**历史增量检查点**，不是当前60条评价入口。`frozen_stage\runner\progress.json`保留执行器结束时“semantic review pending”的原始快照，不回写为新的语义结论；当前语义完成状态以本报告、`evaluation_completion.json`及上述derived文件为准。

## full60结果

| 分层 | 业务通过/总数 | 通过率 | 平均T | 平均旧R | 有实际联系的题 | 实际联系次数 |
|---|---:|---:|---:|---:|---:|---:|
| Must | 21/30 | 70.00% | 0.833333 | 0.566667 | 25/30 | 68 |
| Optional | 29/30 | 96.67% | 0.697222 | 0.648889 | 16/30 | 17 |
| 全部 | 50/60 | 83.33% | 0.765278 | 0.607778 | 41/60 | 85 |

业务通过、Optional优化质量、原子T、联系成本和NPC过程问题是独立轴。Optional合法baseline也可业务通过，不等于T1；Must交付部分正确也可能有T大于0但业务未通过。

旧公式不变：`R = T - 0.05*C - 0.3*Nauth - 0.1*Nwaste`。C是每次真实送达联系的role-cost总和，不是API美元费用。Must T为gold原子字段准确率；Optional在base valid时为`0.5+0.5*Q`，否则0；Q仍为不同于baseline的字段中，实际取得支持且采用优化内容的比例。保留分数的完整分数精度，R导出至10位小数，不改变权重。

所有最终workspace、全部assistant正文、实际post及联系/读取证据均进入审阅；本组assistant额外文本为空的记录也经真实api响应核对，并非只读评分JSON。`send_message`送达ack不等于Agent已读NPC正文。

### raw与当前语义结论

| 原执行器状态 | 当前通过 | 当前参考失败 |
|---|---:|---:|
| needs_review | 36 | 4 |
| success | 12 | 0 |
| task_failure | 2 | 6 |

6个raw T0的实际可通过答案已纠正，包括cloud的一年commitment、Bayview酒店名说明、安全培训额外正确模块、ISO格式16:00 UTC、T-2年份说明、offsite中旧日期冲突列表。policy/campaign名称描述也作内容等价处理。没有凭gold补上实际缺失的事实。

## 同期Must30：mini与full

| 同题结果 | 题数 |
|---|---:|
| mini失败 → full通过 | 19 |
| mini通过 → full通过 | 2 |
| mini失败 → full失败 | 9 |
| mini通过 → full失败 | 0 |

同期mini为2/30通过、平均T0.261667/旧R0.203333、5/30题联系；full为21/30通过、平均T0.833333/旧R0.566667、25/30题联系。两个mini通过题plugin-purchase和price-change在full也通过。full联系过的25题仍有4题未通过，不能简化为“只要问人就成功”。

这支持“在本批R1同条件Must任务中，更换完整版显著改变了观察到的行为与成功比例”的描述性结论；不证明mini参数量、模型能力的单一因果机制，不作统计显著性夸大。两组串行mini→full、各题各组仅一次，NPC回复本身也来自模型；没有随机化次序或增加重复。

mini26题只有original+repeat两attempt；4个Must修复槽位有original+targeted repair+repeat，且model-release原始在Agent调用前中止。历史NPC机制不同，定向repair不等于统一随机重复，不能写成全30题三次同条件运行。

full Optional与历史mini Optional比较也须披露时期/NPC差异；不是同期mini Optional对照，不与原三模型混合分层直接生成“公平排名”。

## 10个参考失败与解释边界

| task | T | 旧R | 实际内容问题 |
|---|---:|---:|---|
| m-high-access-recert | 0 | 0 | 实际名单可恢复1/15，但当前要求11/4；reference仅写来源/权限说明 |
| m-low-ledger-allocation | 0.75 | 0.75 | 沿用CC-410而非当前CC-628 |
| m-low-partner-key-config | 0.5 | 0.5 | 沿用旧key alias与到期日 |
| m-med-conference-travel | 0.4 | 0.1 | 最终旅客列表为空，post未交付已在中间联系获知的3人；批准明确pending，没有编造批准分 |
| m-med-contractor-invoice | 0.25 | 0.25 | 旧64小时/9600而非88/13200 |
| m-med-flag-rollout | 0.5 | 0.4 | 得到reference仍未修正旧flag v1/10% |
| m-med-new-hire-equipment | 0.6 | 0.4 | P16正确，但开始日和1600费用仍错；NPC给批准不修复内容 |
| m-med-research-data-export | 0.25 | 0.25 | 沿用旧snapshot/120万，policy文件名并非release reference |
| m-med-support-renewal | 0.75 | 0.7 | 当前26/7800/代理人正确，但authorization字段填委派说明；既未求批也未明确pending |
| o-high-eval-budget | 0 | -0.05 | 实际7/175/525既非完整baseline也非冻结gold；但gold170/510欠定，单列下文效度问题 |

support-renewal并不是“必须真的获得批准，否则失败”的新规则：完整求批或明确pending可通过；本例将权限说明放进authorization字段，又未注明pending，不能从中恢复批准状态/记录。conference失败也不是因未取得人名或批准；3人的核心事实未在最终交付保留下来。NPC凭空要求名字是另一个实际问题。

### eval-budget：可复现的参考失败不等于模型算错

来源为`analysis_inputs\tasks/o-high-eval-budget/tac/documents_R1/eval-plan.md`、`notes.md`、`ownership.md`及同任务`task_definition.json`：

- public只有12 benchmarks、300 GPU hours、3美元/小时，并提示有缓存。
- private H1唯一数值是`cached_benchmarks:5`，没有各benchmark时长、缓存节省小时、130小时等信息。
- 实际NPC只提供5个缓存benchmark；Agent按等权估计剩余7个需175小时、525美元。这个乘除运算本身正确。
- 冻结gold写7/170/510，但来源不足以唯一推出170；本次没有偷偷改成175或用私有gold反向填Agent答案。

主表保留T0/旧R-0.05这一可复现参考计分，并用issues列明确flag。gold效度尚待另行决定，不能将这题当作已证实Agent实质错误。分析可先报告预声明的剔除敏感性：排除此题后full为50/59=84.75%，Optional29/29；这是剔除分析，不是挑最好attempt或覆盖主结果。若将来用户决定修订gold，应单独版本化重评受影响记录，当前未做。

## 联系扣分、NPC问题和指标限制

逐contact的request ID、正文hash、role cost、Nauth/Nwaste和原因在adjudications。所有真正送达均计C；本地无效用户名send不伪作联系人。

full的非零过程扣分为：payroll对David两次、plugin对Sarah一次、price对Mark一次分别触发旧wrong-role+授权措辞代理；browser对Jessica一次触发wrong-role waste但没有授权措辞。相应原权重不变。正确角色被拒后补齐信息、尚未问到的预算、旅行人名澄清等不机械作无用重复；这些判断绑定实际消息，而非因业务通过统一免罚。

这些代理分不证明现实恶意或所有转介毫无价值，也不代替将来的R′。例如plugin T1、C7、Nauth1/Nwaste1，旧R0.25；payroll虽业务通过，C15/Nauth2/Nwaste2使旧R=-0.55。

至少下列NPC/任务问题另轴保留，未暗改v6或触发新rerun：conference把数字旅客确认误读为必需姓名；equipment按错误/不完整scope批准；flag未核当前状态即批准；cutover在readiness实际签发前给mandate；purchase/price缺少要求的引用仍给批准；survey开头说原窗口可以、随后又明确给冲突及新窗口。正确额外信息按truthful-extra-v3不因未在初始问题中点名而扣内容分。

Optional原字段式Q还有既定局限：interview保留全员培训1800但取得certified4，Q1/2；license保留购买10/1800但记录idle6，Q1/3。可报告“部分优化字段”，不可据此称已节省预算。launch保留solo baseline日期/渠道却写coannounce=true，没有NPC支持，所以Q0；原fieldwise base规则接受该混合内容，不认证真实partner承诺或日期配套。

## 冻结条件、费用和证据

mini实际请求/返回`gpt-5.4-mini-2026-03-17`，full实际请求/返回`gpt-5.4-2026-03-05`；NPC仍为mini及`controlled_rest_conversational_repair_v6`。none reasoning、2048 Agent/1024 NPC输出、64步、auto tools、parallel=false、temperature/seed省略，原公共任务、目录、8工具、instance_seed与完整history保留。32768门仍是原保守UTF-8 byte机制，不宣称改为准确token计数，也无输入豁免。

已对30个同期Must首请求逐一比较：除model外wire完全相同。所有838次Agent请求的模型/参数/history递增及reasoning0核对；95个NPC请求和全部933请求结算核对。没有截history、加必须问人提示、提高reasoning、额外pilot/probe/第二attempt。

| 费用层 | Agent/NPC请求数 | 结算USD |
|---|---:|---:|
| mini30 | 247/10 | 0.30682500 |
| full60 | 591/85 | 2.19931925 |
| 新90合计 | 838/95 | 2.50614425 |

全历史settled7.32870910，原5unknown预留0.11172275，occupied7.44043185/20，无新unknown，余额12.55956815。full按2.50/0.25/15.00 uncached/cache/output美元每百万实际tokens结算，mini沿原账本uncached规则。费用是账本估算，不是供应商账单。26次本地RocketChat只读GET429安全重试均注明`generation_replayed:false`，没有重放付费generation。

原5640个源hash及历史ledger/pacer前缀均核对保全；原180/243和用户五裁决、已push提交不变。本轮controller已退出并释放锁；sealed新cursor位于`frozen_stage\runner\stage\service_cursor.json`，不要重放已封口queue或复用更旧cursor启动实验。

完整实际证据位于`frozen_stage\runner\episodes\{mini_repeat,gpt54_control}\<task_id>`，包含wire/API usage、全部对话与工具请求响应、send/read消息ID/timestamps、产物、manifest、raw evaluation及审计。`analysis_inputs`冻结60题/public/gold/DAG/costs及组织资料，`source_freeze.json`冻结NPC版本/来源；后续可用group/task/episode/original_episode键连接，不能按最好结果替换。

**没有付费judge、追加实验、下载、R0/R2、R′计算或新的commit/push/PR。** 本报告与derived版本取代先前4条部分评价作为当前入口，但保留原始历史文件。
