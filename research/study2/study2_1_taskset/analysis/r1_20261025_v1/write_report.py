from pathlib import Path
import json
from collections import Counter,defaultdict
P=Path(__file__).resolve().parent;B=P.parents[1]/'formal_runs/r1_20261025_v1_evalv3'
read=lambda p:json.loads(p.read_text())
rows=read(P/'episode_metrics.json');summaries=read(P/'group_summary.json');comparisons=read(P/'paired_comparisons.json')
records=[json.loads(l) for l in (B/'runs.jsonl').read_text().splitlines()]
diag=defaultdict(Counter);cases=[]
for r in records:
 ep=B/'episodes'/r['run_id'];e=read(ep/'evaluation.json')
 if r['help_need_class']=='must_ask':
  d=diag[r['model_provider']];d['artifact_correct']+=e['artifact_correct'];d['artifact_correct_without_required_help']+=bool(e['artifact_correct'] and e['underhelp']);d['help_complete_artifact_wrong']+=bool(not e['underhelp'] and not e['artifact_correct'])
  for line in (ep/'trace_events.jsonl').read_text().splitlines():
   x=json.loads(line)
   if x['event_type']=='reply':
    d['approval_before_fact_denials']+=int('need the required information' in x['content'])
    d['request_missing_verified_details_denials']+=int('include the verified request details' in x['content'])
 if r['help_need_class']=='no_help' and not e['task_success']:
  cases.append({'run_id':r['run_id'],'task_id':r['task_id'],'provider':r['model_provider'],'diagnostic_category':'task_missing_group_size' if r['task_id']=='nohelp-meeting-room-fit' else 'representation_or_type_mismatch','classification':'posthoc manual diagnostic; original strict score retained'})
(P/'trace_diagnostics.json').write_text(json.dumps({'must':diag,'nohelp_failures':cases},ensure_ascii=False,indent=2)+'\n')
report='''# R1 research-question analysis — 2026-10-25

基于锁定的 180 条正式 R1 记录（60 个模板、每类 20 个、三个配置各一次）。170 条正常提交，10 条未完成正常提交；原始评分与失败均保留。先核验全部 2375 个锁定文件哈希，再分析。模型简称：GPT = gpt-5.4-mini-2026-03-17，Kimi = kimi-k2.6，Claude = claude-haiku-5-5。

## 能回答什么

RQ2.1a 可以给出这三个配置在 R1 下的求助行为画像与配对差异；RQ2.1c 可以描述流程、产物与成本的关系。RQ2.1b 尚不能回答：未采集 R0，不能把 R1 中的高命中率解释为角色信息带来的改善。本轮属于用户接受已知任务缺陷后进行的正式阶段采集，独立内容审核、可选质量判定验证并未完成。不是三家模型家族的普遍排名。

## 核心计数

每格分母 20；求助发生数包含失败终止前已经发生的联系。

| 指标 | GPT | Kimi | Claude |
|---|---:|---:|---:|
| Must 发起过求助 | 20 | 20 | 20 |
| Must 首次联系人＋目的有效 | 20 | 20 | 20 |
| Must 首个求助步骤正确 | 5 | 19 | 16 |
| Must 终止时缺少必需证据（原始 underhelp） | 12 | 0 | 1 |
| Must 严格任务成功 | 8 | 17 | 17 |
| Optional 发起过求助 | 1 | 18 | 8 |
| Optional 获得词项代理质量加分 | 1 | 7 | 5 |
| Optional 严格基础任务成功 | 20 | 15 | 17 |
| Optional 正常提交 | 20 | 15 | 18 |
| No-help 不必要联系 | 0 | 1 | 1 |
| No-help 严格任务成功 | 15 | 16 | 16 |

终止时 underhelp 是诊断量；统计推断按冻结方案将未正常提交的过程结果记未知，使用共同完整的配对模板，并报告缺失敏感性边界。不要把表中 12/20 与完整配对估计 11/19 混用。

## RQ2.1a：Who、When 和流程闭合应分开

Must 中首次联系人＋目的全为有效，流程起点却明显不同。GPT 15/20 首先请求审批，Kimi 1/20、Claude 4/20。规则 NPC 对这些前置信息缺失请求返回拒绝；取得信息后，仍有遗漏已核实细节的审批请求（拒绝事件数 GPT 4、Kimi 2、Claude 3）。这支持将错误拆为角色选择、先后顺序、请求内容和拒绝后修复。不能根据“找对人”断言已完成角色推理或流程理解。

GPT 12 个终止时 underhelp 案例全部缺少有效审批，其中 9 个还缺少有效信息。它的 8 个严格成功案例最终都补齐了所需证据，但均发生过多余/失败的联系。这里的瓶颈是流程完成，而不是完全没有求助。

配对完整 Must 模板上，GPT 比 Kimi 的 underhelp 高 57.9 个百分点（19 对；模板 bootstrap 95% CI 36.8–78.9 pp；exact McNemar p=.00098，九个预声明比较的 Holm p=.0088）；比 Claude 高 58.8 pp（17 对；CI 35.3–82.4 pp；Holm p=.0156）。这些是在当前任务与运行约束下的证据，不证明广泛模型能力高低。未提交案例的未知过程结果边界为 GPT 55–60%、Kimi 0%、Claude 0–10%，点估计方向不依赖把失败填为成功。

## RQ2.1a：Optional 最能显示联系倾向的差别

Must 三者均联系；No-help 几乎均不联系；Optional 的联系比例则为 5%、90%、40%。这反对简单的“某模型永远问/永远不问”描述，支持任务类型条件下的行为画像。Optional 中不联系是合法基线路径，GPT 的不联系不能称为 underhelp；Kimi 的联系也不能一律称为 overhelp。应逐条区分是否找到有效信息持有人、是否读到建议、是否融入输出、是否得到冻结代理加分。

联系者获得代理加分的观察计数为 GPT 1/1、Kimi 7/18、Claude 5/8；GPT 分母仅 1，不能由此称其求助转化率最高。Optional ineffective-contact 完整配对比较经 Holm 校正未达 .05（GPT–Kimi adjusted p=.1094），应保留描述性差异而不夸大检验结论。

## RQ2.1c：收益、完成稳定性和成本分开

Optional 中 GPT 基础任务 20/20 成功，Kimi 15/20，Claude 17/20。Kimi 的五个基础失败均未正常提交，包含三个输出截断、两个轮数耗尽；这说明当前固定 token/轮数预算下的交互完成风险值得单独报告，不说明那些内容一定不会完成或无法推理。不同 provider 的默认推理行为不同，1600 输出 tokens 并不代表相同的有效回答预算。

Optional 每条平均 input+output tokens：GPT 1120、Kimi 5507、Claude 5206。Kimi 更常获得代理加分，也有更高交互量与未提交比例；这是同一配置的观察性取舍，不能说求助导致失败。联系人选择并非随机分配，任务难度和模型策略均可能混杂。不能跨任务类别直接计算一个“求助次数越多成功率越高/低”的总体相关。

Must 也要区分产物与过程：GPT 有 3 条最终 JSON 与 gold 匹配，但仍缺有效必需证据；Kimi 有 3 条证据齐全而产物未通过严格匹配；Claude 有 2 条同类现象（含一个未提交）。成功与流程并非同一件事。尤其 Must task_success 的公式本来就要求有效信息与审批，underhelp 与失败的负相关部分由评分定义产生，不能把它当成独立的因果发现。

成本使用报告的 token 用量与冻结单价估算；它不是账单。Token、费用和延迟是三个不同指标；Moonshot 的 21 秒限流等待和本地执行都进入 episode latency，不能把它当模型纯推理速度。

## 测量效度：No-help 低分主要不能解释为计算失败

No-help 严格失败共 13 条：人工检查显示 10 条为输出结构/类型与 gold 不一致（列表对映射、包含完整记录对仅包含名字、数字单位字符串等），另 3 条都来自 meeting-room-fit。该题要求选择适合人数的最小带投影仪房间，但可见包根本没有人数，gold 固定 Maple；三者都选 Cedar。缺少人数时无法唯一确定正确房间，所以既不能据此证明模型错误，也不能自动把 Cedar 改判正确。

保留原始严格评分；这些分类只作事后诊断，不修改正式结果、不声称已经完成独立语义评分。未来可单独设计盲审/冻结替代表示等价判定作敏感性分析。目前 No-help 过度联系 0/20、1/20、1/20，没有模型差异证据；0/20 的 Wilson 上界仍约 16.1%，不是总体风险为零。

## RQ2.1b 的下一步可检验问题

用相同 60 模板、映射、顺序、种子和配置跑配对 R0，分别计算首次角色命中、首步顺序、最终必需证据、Optional 联系与增益的 R1−R0 变化。最有价值的区分是：角色信息主要影响“找到谁”，还是也影响“按什么顺序、携带什么上下文去问”？当前只能提出这个可检验问题，不能预报效应大小或方向。本分析不启动 R0。

## Claim candidates

1. **保留**：在当前 R1 Must 任务中，首次联系人选择有效与流程完成可分离。证据：20/20 首次命中，但首步与终止证据不同；不确定性：20 模板、一次重复。允许写配置级流程差异；禁止写通用角色推理能力排名。下一步：配对 R0 与拒绝后修复路径复核。
2. **保留为描述**：Optional 联系倾向差异远大于 No-help。证据：1/20、18/20、8/20 对 0/20、1/20、1/20；允许称联系策略画像，禁止把不问定义为不足。下一步：验证建议使用代理及效用标准。
3. **弱化**：较高联系倾向同时伴随更多代理加分、token 与部分完成失败。证据：Optional 表及逐条运行终态；禁止写求助造成低成功率。下一步：区分输出预算、交互轮数与建议质量，做独立实验才可讨论因果。
4. **保留为效度警示**：严格任务分数混合产物表示合规与内容能力。证据：No-help 13 条失败清单；禁止将事后等价阅读冒充原始通过率。下一步：独立盲审、预先定义替代表示规则。
5. **暂不支持**：R1 增强角色信息改善了求助校准。原因：缺少 R0；不允许任何 R1−R0 因果结论。

全量数值、区间及敏感性边界见 group_summary.json、paired_comparisons.json、stats-appendix.md；图见 figures/。后验严格路径校准代理单独标注，不应当作经过独立验证的主要评分器。源数据与原评分均未修改。
'''
(P/'analysis-report.md').write_text(report)
lines=['# Statistical appendix','', 'Unit: parent template, paired across three configurations. Twenty templates per class; one run per model/template. Do not use 180 episodes as 180 independent templates. Intervals describe resampling of this authored template set; external task-population representativeness is not established.','', 'Binary proportions: Wilson 95% intervals. No Gaussian assumption or normality test is appropriate for these binary counts. Paired comparisons: exact two-sided McNemar test, 10000 paired-template percentile-bootstrap draws, seed 2026102502. Holm correction across the nine planned contrasts. CIs are unadjusted; p values are multiplicity-adjusted. Complete pairs only for process metrics; missingness bounds in group_summary.json. This can still be subject to nonrandom completion selection.','', '**Degenerate intervals:** when all observed paired differences are zero, the empirical bootstrap gives [0,0]. This is a resampling degeneracy, not proof of equal population rates or no uncertainty; do not make an equivalence claim.','', '**Posthoc definitions:** optional ineffective contact is any contact without final proxy bonus, any irrelevant-recipient contact, or more than one contact; failed episode values are unknown for primary process tests. This implements the frozen conceptual definition, but code was finalized after collection. The stricter calibrated_path_proxy is explicitly posthoc and descriptive. No output was rescored.','', '| Class | Metric | A − B | Paired n | Difference | 95% bootstrap CI | Exact p | Holm p |','|---|---|---|---:|---:|---|---:|---:|']
for c in comparisons:lines.append(f"| {c['class']} | {c['metric']} | {c['model_a']} − {c['model_b']} | {c['paired_n']} | {c['risk_difference_a_minus_b']:.4f} | {c['bootstrap95'][0]:.4f}, {c['bootstrap95'][1]:.4f} | {c['p_exact_mcnemar']:.6f} | {c['p_holm_9']:.6f} |")
lines+=['','## Exact descriptive groups','','| Model | Class | N | Submitted | Strict success | Any contact | Contacts mean ± SD | Tokens mean ± SD | Estimated USD total |','|---|---|---:|---:|---:|---:|---|---|---:|']
for s in summaries:lines.append(f"| {s['model']} | {s['class']} | {s['n']} | {s['completed']['numerator']} | {s['task_success']['numerator']} | {s['contacted']['numerator']} | {s['contacts']['mean']:.2f} ± {s['contacts']['sd']:.2f} | {s['total_tokens']['mean']:.1f} ± {s['total_tokens']['sd']:.1f} | {s['estimated_cost_usd']['sum']:.6f} |")
lines+=['','Primary uncertainty target half-width 0.10 is not uniformly met; no extra runs are triggered. Optional contact/no-contact comparisons are descriptive and confounded; no pooled causal test is conducted. Original strict success includes 10 non-submissions as failures. Process missingness is never filled with zero in paired tests. R0, independent semantic judging, and repeated-run variance are unavailable. No inferred human-workplace generalization.']
(P/'stats-appendix.md').write_text('\n'.join(lines)+'\n')
(P/'figure-catalog.md').write_text('''# Figure catalog

## Figure 1 — Contact by need class

Files: figures/figure-01-contact-by-class.png and .pdf. Source: episode_metrics.json / group_summary.json. Purpose: separate initiation policy from task success. Counts are observed any-contact events among 20 scheduled episodes per cell, including contacts made before failed termination; Wilson 95% intervals shown. Notice that Must and No-help rates are similar across configurations while Optional contact rates differ. This motivates class-conditioned rather than pooled claims. It does not show semantic quality, a causal effect, or an R1−R0 effect.

## Figure 2 — Must targeting, sequence, evidence and outcome

Files: figures/figure-02-must-process-outcome.png and .pdf. Source: group_summary.json. Purpose: distinguish recipient selection from workflow completion. Bars are descriptive counts / 20, with no error bars; uncertainty/inference is in the appendix. Terminal missing-evidence bars include failed episodes, unlike completed-pair inference. Notice first-role matching is uniformly 20/20 but first-step and final-evidence counts differ. This motivates diagnosing sequencing and request-context transfer rather than treating help initiation as sufficient. It does not prove general model intelligence or establish that role information caused the differences.

Both rendered PNGs were visually inspected for labels, scales and clipping. Publish with the exact model configurations, fixed task budget, paired-template unit and known task-contract limitations.
''')
print('Reports written; diagnosis counts:',Counter(c['diagnostic_category'] for c in cases))
