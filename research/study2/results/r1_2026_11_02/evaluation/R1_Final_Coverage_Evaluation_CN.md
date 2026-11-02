# Study 2.1 R1 全量结果与语义评价

已审阅原180槽位及全部63获准修复attempt，共243个唯一episode。修复涉及61槽位，不改变60任务×3模型的原180分母。当前最后获准attempt展示口径有0条评分/证据缺口；其中0条需用户实质裁定。未把“已经终止”自动写成“任务成功”或“全部可确定评价”。

**审阅覆盖180/180，未审阅0；当前可评价结果180/180，技术/保护中止不可评价0。**业务内容未决0；当前T/R不可用0。已确定业务失败不是“尚未评价”。正常end_turn且缺必需信息的无交付行为按原非提交分支计T0，不再机械记成技术未知；真实完整内容可从最终文字恢复时不因缺JSON而失败。

## 终止原因纠正（v2）

前版把workspace为空机械等同技术不可评价，错误覆盖此前55报告的三条业务失败。现已核验五条全部正常end_turn、采集完整、未到64步上限，均非provider/transport或预算/保护中止。conference-travel实际最终文字信息完整且明确pending，按既定内容及审批规则语义通过；另外四条缺当前关键业务信息，按观察到的未完成行为失败。同时纠正两条同因的历史正常终止；真正runtime/保护中止仍保留不可评价。详见`Five_Gap_Termination_Correction_CN.md`与`termination_correction_v2.json`；前版发布文件完整保存在`published_v1_snapshot/`，raw从未更改。

## 评价口径

人可从实际提交恢复全部gold所需信息时内容通过；正确列表/计数/格式/名称等价不独立导致失败，不以gold补造没有发生的事实。public任务未要求已获批时完整求批或明确pending可通过；真实姓名/编号不自动等于授权已发生。正确额外NPC信息不算错；错误事实/错误拒绝等另轴记录，不自动触发补跑。

原T定义与旧R权重不变：Must按语义满足的原字段比例；Optional按有效base与有证据优化字段采用比例；R=T−0.05C−0.3Nauth−0.1Nwaste。内容投影只存在于派生计分，绝不改写实际产物。pending义务的评分投影不证明gold中的真实签署/编号已经发生；实际节点只绑定真实消息。私有DAG base与public业务判断分栏，不能用私有要求否决已被用户允许的prepare/pending。五条用户裁决及固定分数全部保留，不以新AI意见覆盖。

## 覆盖与分层（非新模型排名）

| 口径 | 模型 | 槽位 | business分布 | T可用 | R可用 |
|---|---|---:|---|---:|---:|
| 原始180 | openai | 60 | {'business_failure': 28, 'not_evaluable': 1, 'business_success': 31} | 59 | 59 |
| 原始180 | anthropic | 60 | {'business_success': 48, 'business_failure': 11, 'not_evaluable': 1} | 59 | 59 |
| 原始180 | kimi | 60 | {'business_success': 36, 'business_failure': 15, 'not_evaluable': 9} | 51 | 51 |
| 最后获准attempt展示 | openai | 60 | {'business_failure': 28, 'business_success': 32} | 60 | 60 |
| 最后获准attempt展示 | anthropic | 60 | {'business_success': 51, 'business_failure': 9} | 60 | 60 |
| 最后获准attempt展示 | kimi | 60 | {'business_success': 50, 'business_failure': 10} | 60 | 60 |

## 修复链与选择偏差

每槽保留原episode及全部获准repair/additional attempt。展示列仅按授权链序取最后一次，不按最高分挑选。119未repair槽位展示original；59槽位一repair；2槽位两repair。这是异常定向修复后的展示，不是新的独立180次实验，不能与原180混算无偏成功率。八个Kimi修复attempt使用用户明确授权的本地输入门豁免（六个首次+两个追加）；原55使用原输入门。条件差异保留，不能声称准确token计数已验收。

## 缺口与历史技术中止

原180缺口12；243全attempt历史缺口14；最后获准展示缺口0。历史技术attempt不凭缺失产物补0分，后续已获准追加结果并列，不抹除失败轨迹。另有1条仅涉及NPC额外告知义务的历史解释缺口，不意味着业务内容或T/R未知，CSV以gap_axis分开。

**当前展示缺口为0；仍完整保留历史技术中止及其不可完整计分记录。**

## 逐例审计入口

- `R1_All_180_Slots.csv`：180行原始/修复链/最后获准展示、原与派生分数及证据路径。
- `All_243_Attempts.csv` / `all_attempt_evaluations.json`：每个attempt的独立业务判断、T/R分量、投影、真实消息绑定。
- `All_Attempt_Gaps.csv` / `Current_Display_Gaps.csv`：所有历史和当前缺口（空表仍有表头）。
- `NPC_Issues_No_Automatic_Rerun.csv`：NPC问题独立记录，不自动重跑。
- `packets/`：实际public任务、private原参考、全部消息、产物/提交/既有裁决；`freeze.json`保存原文件hash。

## 保全与限制

核验180unique/每模型60/61修复槽位/63修复attempt/243唯一episode，5638源文件hash不变。本轮无模型/计数/付费judge/下载/服务请求，无重跑、无raw回写、不实现R′。审阅为非盲session AI及其离线委派，不是独立人工。用户编辑中的五例文档未改写；旧84/55为历史快照，本版独立派生。