# 原NPC6一次新attempt：73保留＋167待完成，原50帽

直接用户来源`de32a741-1d64-4655-bf85-6f5aeb4213ea` revision2：
“继续运行吧”。这是在上一份实际停止/精确续接选择展示之后的批准。
协调者assignment：
`assignment:741f367f-a37b-48de-a57d-1e7bbe84ade4:call_VQv0ZXPwbH68jQPq4hYIMj8g`。
它批准原service-cutover D NPC6的一次独立记账attempt，不是无限unknown重试。
旧停止报告、结果、账本、全部8unknown和原50美元帽原样保留。

实现`phase0_npc_recovery.py`，只扩展恢复admission，不改Phase0运行语义、
模型/NPC/what、历史内容、ordinary64/contacts64、scorer及0.10门。
历史14个root核对全部2080calls/2072settled/8unknown，
settled23.0652996750＋held6.864＝占29.9292996750，余20.0707003250。
无活跃runner后使用独立`study4-phase0-reference-v8-path73-target167-npc6-20261115` namespace，
不重启旧STARTED root。

## 原有随机前缀，不重抽/重问/重send

完整73份记录全部保留，不按分数、回复或新规则重筛。
原26A/C整组及153个实际请求重新核对；
73份共享公共输入/执行器/NPC/gold进度/scorer相关源码与上一执行版本完全相同。
只有admission及新增恢复模块变化。

原partial19个settled调用保留。question6已付、已发给Li Ming一次：
7outgoing、6read、6ordinary，native history尚未写入question6 receipt。
恢复先按原持久history/workspace直接重建状态，不调用任何旧工具或模型；
从真实读回复恢复逐人NPC对话、publicwhat source cache、messages/seen、
artifact/posted revision、contact cost和indices（question7/NPC6/ordinary6）。
实际pending NPC请求hash必须仍为
`d4ba81a78397e1a9f89a056b0fdf6c1aa794115d23ad42dbcb9b6296d2feeec4`。

`finish_pending`只做NPC6一次新attempt；成功后按原`Phase0Mini.ask`后半段
更新cache、加入原实际reply、写已付question6 receipt，
再由固定执行器生成ordinary6一步，随后进入原episode循环。
任何故障都保存实际partial，停批；不重新生成question6/再次send/重放前6个普通动作。

## 本地验证和可审计绑定

48个针对性fixture回归通过：完整原ASK＋ordinary与“停在NPC前再续接”的
公开state/native history/dialogues/cache/indices逐项相等（含publicwhat开/关），
新NPC失败时不产生第二次send或普通动作；错request、第二attempt、释放unknown、
改source、加预算、取消节流等均拒绝。
原共享Phase0、完成合同和限速本地HTTP/fakeclock回归保持通过。
测试NPC是显式fixture，不是额外真实调用。

- [原26A/C整组重新绑定](REFERENCE_V8_NPC6_EXECUTION_AC26_20261115.json)：
  原审计的26＋214数字是历史cohort证明，不是本次73＋167调度。
- [73全组、原partial与request准备证明](REFERENCE_V8_NPC6_CONTINUATION_PROOF_20261115.json)。
- [上次73例停止、费用、全部非盲复核与配对统计](REFERENCE_V8_PACED_ACTUAL_STOP_ZH.md)。

## 执行命令与剩余边界

先冻结最终执行源码、cohort和授权，再执行`--check`，最后仅在进程内注入已授权User credential。
以下ROOT和PRIOR均为当前session持久files目录内明确的不同路径：

```powershell
python -m research.study4.v2.phase0_npc_recovery --freeze --root $ROOT --prior-root $PRIOR --cohort research\study4\v2\reports\REFERENCE_V8_NPC6_EXECUTION_AC26_20261115.json
python -m research.study4.v2.phase0_npc_recovery --check --root $ROOT
python -m research.study4.v2.phase0_npc_recovery --execute --root $ROOT
```

所有ordinary/question/NPC仍共享一个限速器：恢复冷却60秒、至少20秒前置间隔、
服务端更长等待优先，等待不占HTTP自身deadline。
首个正式请求就是pending NPC6，不发独立probe/GET。
剩余167＝原partial1＋166未开始，A42/B42/C41/D42。
剩20.0707不保证覆盖尾部；额度不足或新unknown仍停止。
实际完成后才可判原60题四臂0.10门，不以当前缺失当0或失败，不启动训练。
本页是执行合同；真实首次恢复以新root的model_result、
`pending_NPC_receipt_and_ordinary_completed`和后续slot为证，不把freeze冒充已执行。
