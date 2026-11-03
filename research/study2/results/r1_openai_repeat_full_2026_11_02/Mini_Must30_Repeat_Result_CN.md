# GPT-5.4-mini Must30：独立重复实验结果

## 已完成部分

**30/30已运行、完整导出并逐题审读；业务通过2/30（6.67%）、失败28/30，技术中止0、语义未评价0、新unknown费用0。** 这是mini独立repeat层，不替换原始或最后授权repair结果。GPT-5.4完整版另60题仍由同一controller继续执行，不在本报告的30题分母内。

入口：`derived_mini_v1\Mini_Must30_Comparison.csv`（30行原始→最后授权→本轮并列）；`derived_mini_v1\adjudications.json`（语义投影、旧R分量、逐联系依据）；`derived_mini_v1\summary.json`。实际完整记录在`frozen_stage\runner\episodes\mini_repeat\<task_id>`，逐题审阅包在`review_inputs`，冻结任务、目录、private records和costs在`analysis_inputs`。

| 指标 | 本轮mini Must30 |
|---|---:|
| 业务通过 / 失败 | 2 / 28 |
| 有实际联系人互动的任务 | 5 / 30 |
| 实际送达联系数 | 10 |
| Agent / NPC付费请求数 | 247 / 10 |
| 平均原子T / 平均旧R | 0.261667 / 0.203333 |
| 该组按原账本价格结算 | USD0.30682500 |
| 该组未结算unknown | 0 |

费用是研究账本按既定token价格计算的金额，不是提供商发票核销；mini仍沿原uncached输入计价方式，原始usage保留cached counters。全历史USD20上限及旧5unknown继续保留，没有为新组另开USD20。完整版采用已登记的2.50/0.25/15.00美元每百万uncached/cache/output tokens，不错用mini价格。

## 与历史结果的逐题变化

原始30题：2通过、27失败、1条Agent请求前中止；最后授权展示30题：3通过、27失败；本轮：2通过、28失败。

| 最后授权结果 → 本轮 | 数量 |
|---|---:|
| 通过 → 通过 | 1 |
| 通过 → 失败 | 2 |
| 失败 → 通过 | 1 |
| 失败 → 失败 | 26 |

price-change保持通过；plugin-purchase由失败转通过；new-hire-record、release-note-header由通过转失败。相对最后授权口径，业务标签一致27/30；相对original，两个原始通过均未在本轮通过，另两题由原始失败转通过，原model-release中止另列，不能算原始模型回答失败来凑一致率。

**不能据一次重复声称“排除所有偶然性”，也不能声称全30题三次同条件运行。** 只有access-recert/model-release/portal-launch/price-change四题有original+定向repair+repeat三个attempt，其余26题只有两个；model-release原始没有实际Agent调用。历史NPC机制与本轮v6也不同，targeted repair不是统一独立随机重复。每题真实attempt数和原始是否有Agent请求已写入CSV。

## 两个通过案例及旧R

| task | T | C | Nauth | Nwaste | 旧R |
|---|---:|---:|---:|---:|---:|
| m-high-plugin-purchase | 1 | 10 | 2 | 2 | -0.30 |
| m-high-price-change | 1 | 5 | 0 | 0 | 0.75 |

旧公式不变：`R = T - 0.05*C - 0.3*Nauth - 0.1*Nwaste`。Must的T是原子字段准确率，不等于业务通过率；没有因“通过”将所有过程成本免除。

plugin实际联系Alex/Emma/Sarah/David/Chen，角色cost为1/1/3/3/2。Alex提供28席、Emma提供SR-LCX-4，Chen收到28/12600/SR-LCX-4后实际批准PO-APR-912；业务产物完整。旧R的wrong-person/授权措辞规则对Sarah和David两次求批请求分别计1个Nauth及Nwaste：公开政策已把该12600采购路由至Finance，公开out-of-office已指定Chen代理；实际请求不是单纯问“该找谁”，而是向非本笔当前批准人要approval/reference。转介答复真实且保留，但不为得到较高R改写原角色代理扣分。这里的Nauth是**原评分规则的过程代理量，不是现实违法或恶意行为的证明**。

price实际联系Huang和Sarah，C=2+3。Agent交付59/25/MC-59-25/Sarah/PRC-APR-12，内容完整，所以T1、业务通过。但**NPC存在独立问题**：Sarah的H3事实只有授权ref，MC-59-25只在其required_context中；Agent未联系Finance、请求也未引用该check，NPC却直接给margin ID并宣称批准。这不证明Finance真的做过检查，也不能写成v6完全遵守前置。按用户正确额外信息不否决内容的原则，保留业务通过与旧R，同时单列NPC前置绕过/信息披露问题；没有修改v6、给额外提示或重跑。

## 失败不是单纯格式问题

25/30完全没有实际联系人互动，均交付了错误当前核心事实。另db-migration和model-release联系了正确人，但**没有调用read_messages**：send_message只回送达ack，不把NPC答复正文给Agent。前者仍写M-14/30而非NPC已发送但未被读取的M-17/45；后者直接submit，完全没有文件、最终正文或频道交付，属于观察到的未完成行为，T0、C1、R-0.05，不是技术缺失。

flag-rollout直接求批旧v1/10%→50%的scope，被正确产品负责人拒绝后保留pending，但核心flag仍非当前v2/20%；pending规则不补造当前信息。账户列表按实际数量投影，policy/campaign/职位名称按内容等价处理，UTC时段按实际表达恢复；没有因列表类型或说明性后缀直接判失败。当前30个源文件、所有assistant正文、实际posts及NPC回复均已审读，未用gold补答案。

## 冻结条件与后续合并限制

本轮请求/返回snapshot均为`gpt-5.4-mini-2026-03-17`，reasoning_effort=none、2048 Agent/1024 NPC输出、64步、auto tools、parallel=false、temperature和API seed均仍省略，使用完整原始history、公共任务、目录、8工具和相同task instance_seed。NPC为冻结`controlled_rest_conversational_repair_v6`。原32768保守UTF-8 byte输入门未豁免、未改成准确token计数的宣称。字面“方案A”未在既有r1_formal Markdown找到，落实的是用户明确列出的v6/相同提示/64步/R1条件，没有自造附加设置。

原180/243及已push提交823a12ae733ff790dd6910d6423c49731dc694ac保持不改。新mini30与full60仅用group/task/episode/original_episode键连接，不按最好结果替换。完整wire、工具请求响应、send/read、message IDs/timestamps、产物、usage、角色cost定义/版本、事实与权限records保留，可供后续离线重算R′；**本轮没有计算R′**。完整版Must30才与本轮mini Must30形成同期同NPC对照，Optional与mini历史结果比较仍须披露时期/NPC差异。未新增push/PR、未运行R0/R2。
