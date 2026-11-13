# Phase0 v5：来源纠正与原范围恢复

此前把“零API修正、待我核验”的消息归为revision10之后的用户限制，是本session的归属错误。
协调者明确确认这些是其Agent审查暂停，并已解除。历史turns的`user_message`文本列
不能证明消息来自真人；当前实际转发包仍只声明原直接用户source
`1babf0c9-1a8f-4242-8816-e8872fda2c22` revision10：“我已经续费你继续吧”。
未找到另一条可核对来源的后续直接用户停止限制。

因此，先前v4/v5报告中“修复后必须再来一条新的直接用户授权”的结论不成立；
那些历史报告不改写，本说明明确纠正该判断，不伪造新的用户批准。
本次保留原用户来源，并单独绑定协调者的审查解除/归属纠正：
`call_6rIfUGqMvljG4R3rDF9iRUVK`，
assignment `call_WROHXd0Ztjobl1hqrBccgjvV`。

## 执行边界

仍为原60×4×1和累计USD50。整组保留原26例A/C，
新run/root内仅214fresh（A47/B60/C47/D60），B/D不筛选旧轨迹。
每个fresh episode采用`reference-v5:`新命名空间；不读取旧模型结果续跑、
不重放旧工具，不接旧partial52。不另发preflight/probe。
首目标fresh B/D与保留A/C构成配对验收，之后按原顺序继续。

继承1022calls/1016settled/6unknown；settled上界10.481236425，
unknown5.148仍占帽，起始占15.629236425，余34.370763575。
所有executor/question/NPC调用计同帽，单call .858预留不变。
新unknown、无法安全恢复或预算不足停止，无自动重发/GET/换端点。
同mini/NPC/what、64步、scorer及0.10门；不训练、不新采集、不做终测。

## 受限准入变化

只为上述恢复新增`phase0_recovery.py`：校验原52根的每个文件hash和643笔settled、
锁住全部十个历史根、在首POST前保留整组26个原文件，fresh仅执行214。
原公共episode/build_request/NPC/scorer源码不变；旧full240入口继续拒绝，
新入口必须精确匹配原用户source、Agent解除记录、26＋214映射、新root、
新runtime和相同累计账目/预算，不能仅凭一个cap获得执行资格。

最终执行源码的整组重核另存
`REFERENCE_V5_EXECUTION_COHORT_20261112.json`；不拿解禁前的
`21c36555…`当最终执行源码hash。该旧fingerprint只标识已审阅的固定保留方案。
新plan另绑定完整重核结果、最终commit及原批准/审查解除。
调用前先做无key的`--check`，成功后才在Process注入既有User key。

## 当前状态

本文件记录恢复边界，不冒充已完成214。实际进度、结算与停止原因以新run
`FINAL_RECEIPT.json`和随后研究报告为准；若范围不完整或证据未复核，训练门仍unknown。
