# Phase0 v6：已批准的NPC事实冲突处理与原轨迹续接

直接用户来源：`f69f8951-214c-43f8-ad71-d57bb64d9573` revision13，
“同意你的决策，请你按照这个来继续”。协调者所列的处理方案另作为Agent说明绑定，
不伪称是用户逐字原话；原revision10、范围60题×4臂×1和累计USD50不变。
这不是训练/GPU、额外模型或新预算授权。

## 处理合同与最小变动

NPC后来给错值是环境错误，不再作为整批基础设施停止条件。
B/D私有完成状态只累计实际回复中来源、请求scope、前置/context合格的真值证据；
已取得正确事实不被后来错误值抹掉。未取得的字段仍不完整，不用gold补答案。
矛盾、错scope与前置未满足的提前释放保留诊断，不能成功兜底。
授权仍需实际前置、真实required_context与明确授予；
条件、草稿引用、历史编号不授予，明确合法撤回仍清除旧grant。

公开任务、ordinary executor、NPC、what规则、请求格式、64步、scorer及0.10门不变。
四臂全部保留实际错误和矛盾回复，不删除、不向公开输入注入gold、不改草稿。
最小代码差异是私有reference v6的事实/诊断分离，以及episode可接入已核验hydrated runtime；
普通新episode默认路径归一化AST与原来一致。
技术故障、新unknown、预算不足仍停机；未证实语义保守不完成并留诊断。

## 原18call前缀：不是重抽

来源为v5 plan `f055257f6f16ef807f50bb8b9d6b718456e06c7e6dc966bcedd06b61ee7ef43c`，
episode `reference-v5:phase0:m-med-service-credit:B:r0`。
逐一核对18个request/result与原只读ledger，6组ASK/read/ordinary均完整：
24个公共事件、6次实际普通动作、6次联系/18成本单位。
最后一次ordinary submit已被阻断且已计步；不是等待执行的工具。

恢复只从已持久事件与workspace折叠状态，恢复完整原始NPC对话、native调用/输出配对、
event cursor与各类index6，不调用模型、不执行工具。前缀证明
`864887d78c56a4a33eaa61281f452f71e073238f4f5504d17b7b73ed588d7827`。
实际六回复在新规则下均保留h1；h2从未合法取得。
错误5/400草稿和NPC矛盾原文全部仍在下一个公共请求中。
见[前缀证书](REFERENCE_V6_PREFIX_CERTIFICATE_20261112.json)。

## 固定覆盖和费用

全部原13题26条A/C再次整组核验，不按结果筛选。
214个未完成逻辑slots包括上述1个paid-prefix续接和213个全新episode；
其中A47/B60/C47/D60，所有B/D均非旧52结果复用。
新命名空间仅slot1保留原v5消息身份，其余213用v6；
所有旧run/分数/ledger不写入，旧partial52不恢复。
整组证据见[26A/C绑定](REFERENCE_V6_EXECUTION_COHORT_20261112.json)。

继承1040calls/1034settled/6unknown，累计settled上界USD10.5353333250，
unknown继续预留USD5.148，occupied USD15.6833333250，剩余USD34.3166666750。
未发独立probe，不释放unknown，不增加预算。旧52成本分臂外推214约USD29.71，
去掉已证明D重复循环的敏感性情景约USD7.18；不是保证，
原64步长尾与NPC错误仍可能耗尽余额。每次POST仍预留USD.858，余额不足发送前停止。

## 验收和分析边界

针对性离线测试覆盖实际六次回复的h1保留/h2不成立、错值/错scope不补事实，
及既有条件、否定、撤回、重新授权、95节点原规格回归。
前缀核验和A/C请求重建不是新模型表现；实际执行与结果将另报。

最终主分析保留全部60题，不因NPC错误删任务；Must/Optional分列，
报告B−A或D−A平均R是否达到.10及配对CI，不增加CI门。
NPC错误/矛盾/提前授权附报。B/D是有gold任务进度辅助的路由上限，
并非保证训练能复制；H5跨执行器仍未测。单repeat不证明重复稳定性。
